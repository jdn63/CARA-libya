"""
HeiGIT Accessibility Connector — Libya CARA

Data source: Heidelberg Institute for Geoinformation Technology (HeiGIT)
Dataset: Libya - Accessibility Indicators
HDX URL: https://data.humdata.org/dataset/libya-accessibility-indicators
License: CC BY-SA 4.0

Coverage:
  - Hospital access: % of population reachable within N minutes of nearest hospital
  - Primary healthcare access: % of population reachable within N minutes of nearest clinic
  - Education access: % of school-age population within N km of nearest school
  Geographic level: ADM1 (22 districts / shaabiyat).
  Municipalities receive their parent district's score (documented proxy).

INFORM Pillar mapping:
  - hospital_access_gap    → Coping Capacity (healthcare_access_gap sub-indicator)
  - primary_care_access_gap → Coping Capacity (healthcare_access_gap sub-indicator)
  - education_access_score → Vulnerability (health/education awareness proxy)

Operation model: cache-first.
  refresh() downloads CSVs to data/cache/heigit/
  fetch()   reads from local cache — no network call during web requests.
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

CACHE_DIR = os.path.join('data', 'cache', 'heigit')

# Direct CDN URLs — stable HeiGIT Libya access files on HDX
RESOURCE_URLS = {
    'hospitals':           'https://hot.storage.heigit.org/heigit-hdx-public/access/lby/LBY_hospitals_access_long.csv',
    'primary_healthcare':  'https://hot.storage.heigit.org/heigit-hdx-public/access/lby/LBY_primary_healthcare_access_long.csv',
    'education':           'https://hot.storage.heigit.org/heigit-hdx-public/access/lby/LBY_education_access_long.csv',
}

# Travel time thresholds (seconds) for scoring
# 3600s = 60 minutes — used as the primary access threshold for hospitals
HOSPITAL_TIME_THRESHOLD = '3600'
PRIMARY_CARE_TIME_THRESHOLD = '3600'
# Distance threshold (metres) for education access
EDUCATION_DISTANCE_THRESHOLD = '10000'   # 10 km

# Mapping: our district IDs → HeiGIT ADM1 ISO codes
# Based on Libya's 22 shaabiyat (administrative districts).
DISTRICT_TO_HEIGIT: Dict[str, str] = {
    'tripoli':       'LY-TB',   # Tajura' wa an Nawahi al Arba (Tripoli metro)
    'jafara':        'LY-JI',   # Al Jifarah
    'nuqat':         'LY-NQ',   # An Nuqat al Khams
    'zawiya':        'LY-ZA',   # Az Zawiyah
    'murqub':        'LY-MB',   # Al Marqab
    'misrata':       'LY-MI',   # Misratah
    'sirte':         'LY-SR',   # Surt
    'jabal_gharbi':  'LY-JG',   # Mizdah (Western Mountain)
    'nalut':         'LY-NL',   # Ghadamis / Nalut
    'benghazi':      'LY-BA',   # Benghazi
    'marj':          'LY-MJ',   # Al Marj
    'jabal_akhdar':  'LY-JA',   # Al Jabal al Akhdar
    'derna':         'LY-DR',   # Al Qubbah / Derna
    'batnan':        'LY-BU',   # Al Butnan
    'ajdabiya':      'LY-WA',   # Ajdabiya / Al Wahat
    'wahat':         'LY-WA',   # Al Wahat (same HeiGIT unit as ajdabiya)
    'kufra':         'LY-KF',   # Al Kufrah
    'sabha':         'LY-SB',   # Sabha
    'jufra':         'LY-JUU',  # Al Jufrah
    'wadi_shati':    'LY-WS',   # Ash Shati'
    'murzuq':        'LY-MQ',   # Murzuq
    'wadi_hayaa':    'LY-WD',   # Wadi al Hayaa
    'ghat':          'LY-GT',   # Ghat
}

# Reverse map: HeiGIT ISO → district ID (for loading)
HEIGIT_TO_DISTRICT: Dict[str, str] = {v: k for k, v in DISTRICT_TO_HEIGIT.items()}


class HeiGITAccessibilityConnector(BaseConnector):
    """
    HeiGIT Accessibility Indicators connector for Libya.

    Provides district-level access scores for hospitals, primary healthcare,
    and education. Municipalities inherit their district's score (documented proxy).

    Scores are expressed as the share (0–100) of total population reachable
    within a defined travel time / distance threshold. Higher = better access.

    For Coping Capacity scoring: the gap (100 − access_score) is used so that
    low access → high risk contribution, consistent with INFORM inversion logic.
    """

    CACHE_DURATION_SECONDS = 3600 * 24 * 7   # 7 days

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._district_scores: Dict[str, Dict[str, Any]] = {}
        self._national_scores: Dict[str, Any] = {}
        self._cache_loaded = False
        self._last_refresh: Optional[str] = None
        self._muni_district_map: Optional[Dict[str, str]] = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Return accessibility scores for a municipality.
        Looks up the municipality's district, then returns district scores.
        Falls back to national average when district mapping is absent.
        """
        cache_key = f'heigit_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self._cache_loaded:
            self._load_from_disk()

        district_id = self._get_district(jurisdiction_id)
        heigit_iso = DISTRICT_TO_HEIGIT.get(district_id) if district_id else None
        scores = self._district_scores.get(heigit_iso) if heigit_iso else None

        if scores:
            result = self._wrap({
                **scores,
                '_district_id': district_id,
                '_heigit_iso': heigit_iso,
                '_geographic_proxy': 'district_level',
                '_proxy_note': (
                    'مؤشرات إمكانية الوصول متاحة على مستوى المديرية — '
                    'يُطبَّق على جميع بلديات المديرية كبديل موثق. / '
                    'Accessibility data available at district level — '
                    'applied to all municipalities in the district as documented proxy.'
                ),
                '_last_updated': self._last_refresh,
            })
        elif self._national_scores:
            result = self._wrap({
                **self._national_scores,
                '_geographic_proxy': 'national_average',
                '_proxy_note': (
                    'بيانات إمكانية الوصول غير متاحة على مستوى المديرية — '
                    'يُستخدم المتوسط الوطني كبديل موثق. / '
                    'District accessibility data not available — '
                    'national average used as documented proxy.'
                ),
                '_last_updated': self._last_refresh,
            })
        else:
            result = self._unavailable_response(
                f'لا تتوفر بيانات إمكانية الوصول لبلدية {jurisdiction_id}. / '
                f'No HeiGIT accessibility data for {jurisdiction_id}. '
                f'Run scheduled refresh to populate cache.'
            )

        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        if not os.path.isdir(CACHE_DIR):
            return False
        return any(f.endswith('.csv') for f in os.listdir(CACHE_DIR))

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'HeiGIT Accessibility Indicators — Libya',
            'name_ar': 'مؤشرات إمكانية الوصول — معهد هايدلبرغ لتقنيات المعلومات الجغرافية',
            'url': 'https://data.humdata.org/dataset/libya-accessibility-indicators',
            'update_frequency': 'annual_auto',
            'license': 'CC BY-SA 4.0',
            'geographic_coverage': 'Libya — district level (22 shaabiyat), applied to municipalities',
            'access_method': 'direct_cdn_cached',
            'cache_dir': CACHE_DIR,
            'notes': (
                'Provides share of population within defined travel time / distance '
                'of nearest hospital, primary healthcare facility, and school. '
                'Computed from OpenStreetMap facility locations + WorldPop population. '
                'Data is at ADM1 (district) level; municipalities inherit district score.'
            ),
        }

    # ------------------------------------------------------------------
    # Scheduled refresh
    # ------------------------------------------------------------------

    def refresh(self) -> Dict[str, Any]:
        """
        Download fresh HeiGIT accessibility CSVs to local cache.
        Called by APScheduler weekly alongside the HDX refresh job.
        """
        summary: Dict[str, Any] = {
            'files_attempted': 0,
            'files_ok': 0,
            'errors': [],
            'timestamp': datetime.utcnow().isoformat(),
        }

        for category, url in RESOURCE_URLS.items():
            summary['files_attempted'] += 1
            raw = self._download(url)
            if raw is None:
                summary['errors'].append(f'{category}: download failed')
                continue
            cache_file = os.path.join(CACHE_DIR, f'{category}.csv')
            with open(cache_file, 'wb') as f:
                f.write(raw)
            summary['files_ok'] += 1
            logger.info(f'HeiGIT: downloaded {category}.csv ({len(raw)} bytes)')

        # Reload in-memory cache
        self._district_scores = {}
        self._national_scores = {}
        self._cache_loaded = False
        self._cache = {}
        self._load_from_disk()

        logger.info(
            f"HeiGIT refresh: {summary['files_ok']}/{summary['files_attempted']} files ok"
        )
        return summary

    # ------------------------------------------------------------------
    # Disk cache loading
    # ------------------------------------------------------------------

    def _load_from_disk(self):
        self._cache_loaded = True
        latest_mtime = 0.0

        hospitals_file = os.path.join(CACHE_DIR, 'hospitals.csv')
        primary_file = os.path.join(CACHE_DIR, 'primary_healthcare.csv')
        education_file = os.path.join(CACHE_DIR, 'education.csv')

        if os.path.exists(hospitals_file):
            self._parse_time_access_csv(hospitals_file, 'hospital', HOSPITAL_TIME_THRESHOLD)
            latest_mtime = max(latest_mtime, os.path.getmtime(hospitals_file))

        if os.path.exists(primary_file):
            self._parse_time_access_csv(primary_file, 'primary_care', PRIMARY_CARE_TIME_THRESHOLD)
            latest_mtime = max(latest_mtime, os.path.getmtime(primary_file))

        if os.path.exists(education_file):
            self._parse_distance_access_csv(education_file, 'education', EDUCATION_DISTANCE_THRESHOLD)
            latest_mtime = max(latest_mtime, os.path.getmtime(education_file))

        if latest_mtime > 0:
            self._last_refresh = datetime.fromtimestamp(latest_mtime).isoformat()

        self._build_national_averages()

    def _parse_time_access_csv(self, filepath: str, key_prefix: str, threshold: str):
        """
        Parse a HeiGIT time-based access CSV.
        Extracts the % of total population within `threshold` seconds of nearest facility.
        """
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('admin_level') != 'ADM1':
                    continue
                if row.get('range_type') != 'TIME':
                    continue
                if row.get('range') != threshold:
                    continue
                if row.get('population_type') != 'total':
                    continue
                iso = row.get('iso', '').strip()
                if not iso:
                    continue
                share_str = row.get('population_share', '')
                try:
                    share = float(share_str)
                except (ValueError, TypeError):
                    continue
                entry = self._district_scores.setdefault(iso, {})
                entry[f'{key_prefix}_access_pct'] = round(share, 2)
                entry[f'{key_prefix}_access_gap_pct'] = round(100.0 - share, 2)
                entry[f'{key_prefix}_threshold_seconds'] = int(threshold)
                entry['_district_name'] = row.get('name', '')

    def _parse_distance_access_csv(self, filepath: str, key_prefix: str, threshold: str):
        """
        Parse a HeiGIT distance-based access CSV.
        Extracts the % of school-age population within `threshold` metres of nearest school.
        """
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('admin_level') != 'ADM1':
                    continue
                if row.get('range_type') != 'DISTANCE':
                    continue
                if row.get('range') != threshold:
                    continue
                if row.get('population_type') != 'school_age':
                    continue
                iso = row.get('iso', '').strip()
                if not iso:
                    continue
                share_str = row.get('population_share', '')
                try:
                    share = float(share_str)
                except (ValueError, TypeError):
                    continue
                entry = self._district_scores.setdefault(iso, {})
                entry[f'{key_prefix}_access_pct'] = round(share, 2)
                entry[f'{key_prefix}_access_gap_pct'] = round(100.0 - share, 2)
                entry[f'{key_prefix}_threshold_metres'] = int(threshold)

    def _build_national_averages(self):
        if not self._district_scores:
            return
        keys = [
            'hospital_access_pct', 'hospital_access_gap_pct',
            'primary_care_access_pct', 'primary_care_access_gap_pct',
            'education_access_pct', 'education_access_gap_pct',
        ]
        sums: Dict[str, float] = {k: 0.0 for k in keys}
        counts: Dict[str, int] = {k: 0 for k in keys}
        for scores in self._district_scores.values():
            for k in keys:
                v = scores.get(k)
                if v is not None:
                    sums[k] += v
                    counts[k] += 1
        self._national_scores = {
            k: round(sums[k] / counts[k], 2) if counts[k] > 0 else None
            for k in keys
        }

    def _get_district(self, jurisdiction_id: str) -> Optional[str]:
        """Return the district ID for a municipality from the municipalities JSON."""
        if self._muni_district_map is None:
            self._muni_district_map = self._build_muni_district_map()
        return self._muni_district_map.get(jurisdiction_id)

    def _build_muni_district_map(self) -> Dict[str, str]:
        muni_path = os.path.join('data', 'libya_municipalities.json')
        result: Dict[str, str] = {}
        try:
            with open(muni_path, encoding='utf-8') as f:
                raw = json.load(f)
            for m in raw.get('municipalities', []):
                muni_id = m.get('id', '').strip()
                district = m.get('district', '').strip()
                if muni_id and district:
                    result[muni_id] = district
        except Exception as e:
            logger.warning(f'HeiGIT: could not build municipality-district map: {e}')
        return result

    def _download(self, url: str, timeout: int = 30) -> Optional[bytes]:
        import urllib.request
        import urllib.error
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Libya-CARA/1.0 (HeiGIT accessibility data)'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            logger.warning(f'HeiGIT download failed ({url}): {e}')
            return None

    def district_summary(self) -> List[Dict[str, Any]]:
        """Return a list of all district scores — useful for admin/status pages."""
        if not self._cache_loaded:
            self._load_from_disk()
        rows = []
        for heigit_iso, scores in sorted(self._district_scores.items()):
            district_id = HEIGIT_TO_DISTRICT.get(heigit_iso, heigit_iso)
            rows.append({
                'district_id': district_id,
                'heigit_iso': heigit_iso,
                'district_name': scores.get('_district_name', ''),
                **{k: v for k, v in scores.items() if not k.startswith('_')},
            })
        return rows
