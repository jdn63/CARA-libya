"""
OCHA Humanitarian Data Exchange (HDX) Connector — Libya CARA

Data source: OCHA HDX — data.humdata.org
Coverage:
  - IOM DTM Libya displacement data (IDPs, returnees, migrants by municipality)
  - OCHA 3W operational presence (NGO/agency footprint by location)
  - UNHCR Libya displacement data

Access method:
  - CKAN REST API — data.humdata.org/api/3/action/
  - No authentication required for public datasets
  - Libya group code on HDX: "lby"

Operation model:
  - CACHE-FIRST: fetch() always reads from local disk cache (low-connectivity safe)
  - refresh() is called by APScheduler (weekly) to download fresh CSV files
  - Downloaded files saved to data/cache/hdx/ for offline resilience
  - Falls back gracefully to "data not available" if cache is empty

Data governance:
  - All HDX data is openly licensed (CC BY-IGO 3.0 or CC BY 4.0 depending on dataset)
  - Municipal-level data may not be available for all 148 municipalities
  - Missing municipalities use national average as documented proxy
  - IOM DTM data is handled as humanitarian indicator per IOM methodology

APScheduler integration:
  - core.py adds a weekly job calling HDXConnector().refresh()
  - Refresh results are logged; failures do not crash the application
"""

import csv
import io
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

HDX_API_BASE = 'https://data.humdata.org/api/3/action'
HDX_LIBYA_GROUP = 'lby'
CACHE_DIR = os.path.join('data', 'cache', 'hdx')

# Dataset search terms for each data category.
# Each entry: (search_query, category_key, preferred_resource_name_fragment)
DATASET_SEARCHES: List[Tuple[str, str, str]] = [
    ('IOM displacement tracking matrix Libya', 'iom_dtm', 'dtm'),
    ('Libya who does what where 3W operational presence', 'ocha_3w', '3w'),
    ('UNHCR Libya displacement population', 'unhcr', 'unhcr'),
]

# Maximum age in days before a cached file is considered stale for logging purposes
CACHE_STALE_DAYS = 10


class HDXConnector(BaseConnector):
    """
    OCHA Humanitarian Data Exchange connector for Libya.

    Provides displacement, migration, and NGO presence data
    sourced from HDX public datasets. Operates cache-first for
    low-connectivity environments.

    Typical usage:
        connector = HDXConnector()
        data = connector.fetch('LY-011')      # read from cache
        connector.refresh()                   # called by APScheduler
    """

    CACHE_DURATION_SECONDS = 3600 * 24 * 7   # 7 days

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._municipality_data: Dict[str, Dict[str, Any]] = {}
        self._national_data: Dict[str, Any] = {}
        self._cache_loaded = False
        self._last_refresh: Optional[str] = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Return HDX-sourced data for a municipality.
        Always reads from local disk cache — never blocks on network.
        """
        cache_key = f'hdx_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self._cache_loaded:
            self._load_from_disk()

        muni = self._municipality_data.get(jurisdiction_id)

        if not muni:
            nat = self._national_data
            if nat:
                result = self._wrap({
                    **nat,
                    '_proxy': 'national_average',
                    '_proxy_note': (
                        'بيانات HDX غير متاحة على مستوى البلدية — '
                        'يُستخدم المتوسط الوطني كبديل موثق. / '
                        'HDX data not available at municipality level — '
                        'national average used as documented proxy.'
                    ),
                    '_last_updated': self._last_refresh,
                })
            else:
                result = self._unavailable_response(
                    f'لا تتوفر بيانات HDX لبلدية {jurisdiction_id}. / '
                    f'No HDX data cached for municipality {jurisdiction_id}. '
                    f'Run scheduled HDX refresh to populate. Cache dir: {CACHE_DIR}/'
                )
            self._cache[cache_key] = result
            return result

        result = self._wrap({**muni, '_last_updated': self._last_refresh})
        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        """True if any HDX cache files exist on disk."""
        if not os.path.isdir(CACHE_DIR):
            return False
        return any(
            f.endswith(('.csv', '.json'))
            for f in os.listdir(CACHE_DIR)
        )

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'OCHA Humanitarian Data Exchange (HDX) — Libya',
            'name_ar': 'منصة بيانات المساعدات الإنسانية — مكتب الأمم المتحدة لتنسيق الشؤون الإنسانية',
            'url': 'https://data.humdata.org/group/lby',
            'update_frequency': 'weekly_auto',
            'license': 'CC BY-IGO 3.0 / CC BY 4.0 (per dataset)',
            'geographic_coverage': 'Libya — municipal and district level',
            'access_method': 'hdx_ckan_api_cached',
            'cache_dir': CACHE_DIR,
            'notes': (
                'HDX aggregates IOM DTM displacement data, OCHA 3W operational '
                'presence, and UNHCR Libya population data. '
                'No authentication required. Refreshed weekly by APScheduler. '
                'Operates from local cache when network is unavailable.'
            ),
        }

    # ------------------------------------------------------------------
    # Scheduled refresh — called by APScheduler, never during web requests
    # ------------------------------------------------------------------

    def refresh(self) -> Dict[str, Any]:
        """
        Download fresh data from HDX and update local cache.

        Called by APScheduler weekly. Returns a summary dict with counts
        and any per-dataset errors. Never raises — logs failures silently
        so the scheduler job always completes cleanly.

        Returns:
            {
                'datasets_attempted': int,
                'datasets_ok': int,
                'records_saved': int,
                'errors': [str, ...],
                'timestamp': ISO 8601 string,
            }
        """
        summary: Dict[str, Any] = {
            'datasets_attempted': 0,
            'datasets_ok': 0,
            'records_saved': 0,
            'errors': [],
            'timestamp': datetime.utcnow().isoformat(),
        }

        try:
            import urllib.request
            import urllib.parse
            import urllib.error
        except ImportError:
            summary['errors'].append('urllib not available')
            return summary

        for query, category, name_hint in DATASET_SEARCHES:
            summary['datasets_attempted'] += 1
            try:
                dataset_id, resource_url, resource_fmt = self._find_resource(
                    query, category, name_hint
                )
                if not resource_url:
                    summary['errors'].append(
                        f'{category}: no CSV/XLSX resource found on HDX'
                    )
                    continue

                raw_bytes = self._download_url(resource_url)
                if raw_bytes is None:
                    summary['errors'].append(f'{category}: download failed from {resource_url}')
                    continue

                cache_file = os.path.join(CACHE_DIR, f'{category}.csv')
                with open(cache_file, 'wb') as f:
                    f.write(raw_bytes)

                meta_file = os.path.join(CACHE_DIR, f'{category}_meta.json')
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'dataset_id': dataset_id,
                        'resource_url': resource_url,
                        'format': resource_fmt,
                        'downloaded_at': summary['timestamp'],
                        'category': category,
                    }, f, indent=2)

                summary['datasets_ok'] += 1
                logger.info(f'HDX: downloaded {category} ({len(raw_bytes)} bytes) from {resource_url}')

            except Exception as e:
                summary['errors'].append(f'{category}: {e}')
                logger.warning(f'HDX refresh failed for {category}: {e}')

        # Reload in-memory cache from newly saved files
        self._municipality_data = {}
        self._national_data = {}
        self._cache_loaded = False
        self._cache = {}
        self._load_from_disk()

        logger.info(
            f"HDX refresh complete: {summary['datasets_ok']}/{summary['datasets_attempted']} "
            f"datasets ok, {len(summary['errors'])} errors"
        )
        return summary

    # ------------------------------------------------------------------
    # Internal — HDX CKAN API
    # ------------------------------------------------------------------

    def _find_resource(
        self, query: str, category: str, name_hint: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Search HDX for a Libya dataset matching the query.
        Returns (dataset_id, resource_url, resource_format) of the first
        CSV or XLSX resource found, or (None, None, None) if nothing found.
        """
        import urllib.request
        import urllib.parse

        params = urllib.parse.urlencode({
            'q': query,
            'fq': f'groups:{HDX_LIBYA_GROUP}',
            'rows': 5,
            'sort': 'metadata_modified desc',
        })
        url = f'{HDX_API_BASE}/package_search?{params}'

        raw = self._download_url(url)
        if raw is None:
            return None, None, None

        try:
            response = json.loads(raw.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f'HDX search response parse error for {category}: {e}')
            return None, None, None

        if not response.get('success'):
            logger.warning(f'HDX search returned success=false for query: {query}')
            return None, None, None

        results = response.get('result', {}).get('results', [])
        if not results:
            logger.info(f'HDX search returned 0 results for: {query}')
            return None, None, None

        # Pick the first dataset; prefer ones whose title hints match
        dataset = None
        for r in results:
            title = (r.get('title') or '').lower()
            if name_hint.lower() in title or 'libya' in title:
                dataset = r
                break
        if dataset is None:
            dataset = results[0]

        dataset_id = dataset.get('name') or dataset.get('id')

        for resource in dataset.get('resources', []):
            fmt = (resource.get('format') or '').upper()
            if fmt in ('CSV', 'XLSX', 'XLS'):
                return dataset_id, resource.get('url'), fmt

        return dataset_id, None, None

    def _download_url(self, url: str, timeout: int = 30) -> Optional[bytes]:
        """Download a URL, returning raw bytes or None on failure."""
        import urllib.request
        import urllib.error

        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Libya-CARA/1.0 (humanitarian risk assessment; HDX data access)',
                    'Accept': 'application/json, text/csv, */*',
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            logger.warning(f'HDX HTTP {e.code} fetching {url}')
            return None
        except urllib.error.URLError as e:
            logger.warning(f'HDX network error fetching {url}: {e.reason}')
            return None
        except Exception as e:
            logger.warning(f'HDX download failed for {url}: {e}')
            return None

    # ------------------------------------------------------------------
    # Internal — disk cache loading
    # ------------------------------------------------------------------

    def _load_from_disk(self):
        """Load all cached CSV files from CACHE_DIR into memory."""
        self._cache_loaded = True

        if not os.path.isdir(CACHE_DIR):
            return

        latest_mtime = 0.0

        for filename in sorted(os.listdir(CACHE_DIR)):
            filepath = os.path.join(CACHE_DIR, filename)

            if filename == 'iom_dtm.csv':
                try:
                    count = self._parse_iom_dtm_csv(filepath)
                    logger.info(f'HDX: loaded {count} municipality records from iom_dtm.csv')
                    mtime = os.path.getmtime(filepath)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                except Exception as e:
                    logger.error(f'HDX: failed to parse iom_dtm.csv: {e}')

            elif filename == 'ocha_3w.csv':
                try:
                    count = self._parse_3w_csv(filepath)
                    logger.info(f'HDX: loaded {count} presence records from ocha_3w.csv')
                    mtime = os.path.getmtime(filepath)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                except Exception as e:
                    logger.error(f'HDX: failed to parse ocha_3w.csv: {e}')

            elif filename == 'unhcr.csv':
                try:
                    count = self._parse_unhcr_csv(filepath)
                    logger.info(f'HDX: loaded {count} UNHCR records from unhcr.csv')
                    mtime = os.path.getmtime(filepath)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                except Exception as e:
                    logger.error(f'HDX: failed to parse unhcr.csv: {e}')

        if latest_mtime > 0:
            self._last_refresh = datetime.fromtimestamp(latest_mtime).isoformat()

        # Build national averages from all loaded municipality data
        self._build_national_averages()

    def _parse_iom_dtm_csv(self, filepath: str) -> int:
        """
        Parse IOM DTM CSV from HDX.
        IOM DTM Libya CSVs typically have columns:
          Location / Location (English) / Admin2 / Admin1
          IDPs / Total IDPs / Displaced / IDP_Individuals
          Returnees / Total Returnees
          Total Migrants / Migrants
        Column names vary between report versions — we try common variants.
        """
        count = 0
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = [h.lower().strip() for h in (reader.fieldnames or [])]

            for row in reader:
                muni_id = self._extract_municipality_id(row)
                if not muni_id:
                    continue

                entry = self._municipality_data.setdefault(muni_id, {})
                entry['total_idps'] = self._coalesce_float(
                    row, ['total_idps', 'idps', 'displaced', 'idp_individuals', 'idp individuals']
                )
                entry['returnees'] = self._coalesce_float(
                    row, ['returnees', 'total_returnees', 'return', 'returnee_individuals']
                )
                entry['total_migrants'] = self._coalesce_float(
                    row, ['total_migrants', 'migrants', 'migrant_individuals']
                )
                entry['irregular_migrants'] = self._coalesce_float(
                    row, ['irregular_migrants', 'irregular migrants', 'undocumented']
                )
                entry['_iom_dtm_loaded'] = True
                count += 1

        return count

    def _parse_3w_csv(self, filepath: str) -> int:
        """
        Parse OCHA 3W (Who Does What Where) CSV from HDX.
        Counts distinct organizations active per municipality as
        a proxy for NGO presence/community support capacity.
        """
        org_counts: Dict[str, set] = {}
        count = 0

        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                muni_id = self._extract_municipality_id(row)
                if not muni_id:
                    continue
                org = (
                    row.get('Organisation', '')
                    or row.get('organization', '')
                    or row.get('org', '')
                    or row.get('implementing_partner', '')
                ).strip()
                if org:
                    org_counts.setdefault(muni_id, set()).add(org)
                    count += 1

        for muni_id, orgs in org_counts.items():
            entry = self._municipality_data.setdefault(muni_id, {})
            entry['ngo_count'] = len(orgs)
            entry['ngo_presence_score'] = min(10.0, len(orgs) / 2.0)  # scale: 20 orgs = 10
            entry['_3w_loaded'] = True

        return len(org_counts)

    def _parse_unhcr_csv(self, filepath: str) -> int:
        """
        Parse UNHCR Libya displacement CSV from HDX.
        Maps refugee/asylum-seeker figures to municipality entries.
        """
        count = 0
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                muni_id = self._extract_municipality_id(row)
                if not muni_id:
                    continue
                entry = self._municipality_data.setdefault(muni_id, {})
                entry['unhcr_persons_of_concern'] = self._coalesce_float(
                    row, ['total', 'persons_of_concern', 'refugees', 'asylum_seekers']
                )
                entry['_unhcr_loaded'] = True
                count += 1

        return count

    def _build_national_averages(self):
        """Compute national averages across all loaded municipality data."""
        if not self._municipality_data:
            return

        keys = ['total_idps', 'returnees', 'total_migrants', 'ngo_count',
                'ngo_presence_score', 'unhcr_persons_of_concern']
        sums: Dict[str, float] = {k: 0.0 for k in keys}
        counts: Dict[str, int] = {k: 0 for k in keys}

        for muni_data in self._municipality_data.values():
            for k in keys:
                val = muni_data.get(k)
                if val is not None:
                    sums[k] += float(val)
                    counts[k] += 1

        self._national_data = {
            k: (sums[k] / counts[k]) if counts[k] > 0 else None
            for k in keys
        }

    def _extract_municipality_id(self, row: Dict[str, str]) -> Optional[str]:
        """
        Extract a Libya municipality ID (e.g. LY-011) from a CSV row.

        Tries:
        1. Direct 'municipality_id' column
        2. 'admin3_pcode' / 'admin2_pcode' P-code columns (HDX standard)
        3. Name-based lookup via the municipalities JSON
        """
        # 1. Direct ID
        for col in ('municipality_id', 'muni_id', 'pcode', 'p_code'):
            val = row.get(col, '').strip()
            if val.upper().startswith('LY-'):
                return val.upper()

        # 2. HDX P-code columns (admin3 = municipality in Libya)
        for col in ('admin3_pcode', 'admin3pcode', 'admin2_pcode', 'admin2pcode'):
            val = row.get(col, '').strip().upper()
            if val.startswith('LY'):
                return self._normalize_pcode(val)

        # 3. Name-based lookup (fallback)
        for col in ('admin3name_en', 'admin3name', 'location', 'municipality',
                    'Location', 'Location (English)', 'District'):
            name = row.get(col, '').strip()
            if name:
                muni_id = self._name_to_id(name)
                if muni_id:
                    return muni_id

        return None

    def _normalize_pcode(self, pcode: str) -> str:
        """Normalize HDX P-codes to CARA format (e.g. LY001 → LY-001)."""
        pcode = pcode.strip().upper()
        if len(pcode) == 5 and pcode[:2] == 'LY' and pcode[2:].isdigit():
            return f'LY-{pcode[2:]}'
        if '-' not in pcode and pcode.startswith('LY'):
            numeric = ''.join(c for c in pcode[2:] if c.isdigit())
            if numeric:
                return f'LY-{numeric.zfill(3)}'
        return pcode

    def _name_to_id(self, name: str) -> Optional[str]:
        """
        Fuzzy name lookup against loaded municipality list.
        Lazily loads the municipalities JSON on first call.
        """
        if not hasattr(self, '_name_map'):
            self._name_map = self._build_name_map()
        key = name.strip().lower()
        return self._name_map.get(key)

    def _build_name_map(self) -> Dict[str, str]:
        """Build name → ID lookup from the Libya municipalities JSON."""
        name_map: Dict[str, str] = {}
        muni_path = os.path.join('data', 'libya_municipalities.json')
        if not os.path.exists(muni_path):
            return name_map
        try:
            with open(muni_path, encoding='utf-8') as f:
                municipalities = json.load(f)
            for m in municipalities:
                muni_id = m.get('id', '').strip()
                if not muni_id:
                    continue
                for field in ('name_en', 'name_ar', 'alt_names_en'):
                    val = m.get(field)
                    if isinstance(val, str) and val.strip():
                        name_map[val.strip().lower()] = muni_id
                    elif isinstance(val, list):
                        for v in val:
                            if v:
                                name_map[str(v).strip().lower()] = muni_id
        except Exception as e:
            logger.warning(f'HDX: could not build name map from municipalities JSON: {e}')
        return name_map

    def _coalesce_float(
        self, row: Dict[str, str], column_variants: List[str]
    ) -> Optional[float]:
        """Try each column name variant; return the first parseable float value."""
        row_lower = {k.lower().strip(): v for k, v in row.items()}
        for col in column_variants:
            raw = row_lower.get(col.lower())
            if raw is not None and str(raw).strip():
                try:
                    return float(str(raw).replace(',', '').strip())
                except (ValueError, TypeError):
                    pass
        return None

    # ------------------------------------------------------------------
    # Cache staleness reporting (for admin/status pages)
    # ------------------------------------------------------------------

    def cache_status(self) -> Dict[str, Any]:
        """Return a summary of what's in the local cache — for display in the UI."""
        status: Dict[str, Any] = {
            'cache_dir': CACHE_DIR,
            'files': [],
            'municipality_count': len(self._municipality_data),
            'last_refresh': self._last_refresh,
            'stale': False,
        }
        if os.path.isdir(CACHE_DIR):
            for fname in sorted(os.listdir(CACHE_DIR)):
                fpath = os.path.join(CACHE_DIR, fname)
                mtime = os.path.getmtime(fpath)
                age_days = (time.time() - mtime) / 86400
                status['files'].append({
                    'name': fname,
                    'size_kb': round(os.path.getsize(fpath) / 1024, 1),
                    'age_days': round(age_days, 1),
                })
                if age_days > CACHE_STALE_DAYS:
                    status['stale'] = True
        return status
