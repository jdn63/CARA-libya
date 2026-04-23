"""
IDMC Libya Connector — via OCHA HDX (replaces direct IDMC API)

Data source: Internal Displacement Monitoring Centre (IDMC)
HDX datasets:
  - idmc-idp-data-lby       (annual new displacements + IDP stock)
  - idmc-event-data-for-lby (event-level displacement updates)
License: CC BY-IGO 3.0

Why HDX instead of the direct IDMC API:
  The IDMC public API (api.internal-displacement.org) currently returns 403
  Forbidden without a registered API key. IDMC publishes identical data
  on OCHA HDX as open CSV files updated through April 2026. This connector
  uses those CSV files as the authoritative access path.

Coverage:
  - Annual new conflict displacements (Libya, 2011–present)
  - Annual new disaster displacements (Libya, 2013–present, with event detail)
  - Total IDP stock (most recent year available)

Geographic level: National (Libya, iso3=LBY).
  Municipality fetch: national figures returned as documented proxy.

INFORM Pillar mapping:
  - new_displacements_conflict → Vulnerability (displacement_vulnerability)
  - total_displacement_stock  → Vulnerability (displacement_vulnerability)
  - recent_disaster_events    → Hazard & Exposure (infrastructure / flood events)

Operation model: cache-first.
  refresh() downloads CSVs to data/cache/idmc/
  fetch()   reads from local cache — never blocks on network.
"""

import csv
import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join('data', 'cache', 'idmc')

# Direct HDX resource download URLs (stable permalink format)
RESOURCE_URLS = {
    'annual_idp': (
        'https://data.humdata.org/dataset/aac363e3-aa9f-4f5e-a05b-790c39040b14'
        '/resource/1c1ffdad-f470-4c72-b5c4-21eaa459ade2'
        '/download/internal-displacements-new-displacements-idps_lby.csv'
    ),
    'disaster_events': (
        'https://data.humdata.org/dataset/aac363e3-aa9f-4f5e-a05b-790c39040b14'
        '/resource/527e209f-ce9e-4143-8a4b-f6d9954c333d'
        '/download/internal-displacements-new-displacements-associated-with-disasters_lby.csv'
    ),
    'event_updates': (
        'https://data.humdata.org/dataset/f6ee13fa-bed1-4f4c-b3ca-d42d6f42642b'
        '/resource/f4bf7be1-00e3-476a-83c0-8f9dfc9c064b'
        '/download/event_data_lby.csv'
    ),
}

# Minimum year for "recent" displacement events (for hazard indicator)
RECENT_EVENTS_FROM_YEAR = 2020


class IDMCHDXConnector(BaseConnector):
    """
    IDMC Libya displacement data connector via OCHA HDX.

    Returns annual displacement figures and recent disaster-triggered
    displacement events for Libya. Municipality-level data is not
    available from IDMC; national figures are returned with a documented
    proxy note for all municipality-level requests.
    """

    CACHE_DURATION_SECONDS = 3600 * 24 * 7   # 7 days

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._national: Dict[str, Any] = {}
        self._disaster_events: List[Dict[str, Any]] = []
        self._cache_loaded = False
        self._last_refresh: Optional[str] = None
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Return IDMC displacement data.
        All data is national-level; municipality requests return national
        figures with a documented proxy note.
        """
        cache_key = f'idmc_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self._cache_loaded:
            self._load_from_disk()

        if not self._national:
            result = self._unavailable_response(
                'لا تتوفر بيانات النزوح من IDMC. / '
                'No IDMC displacement data in cache. '
                f'Run scheduled refresh to populate. Cache: {CACHE_DIR}/'
            )
        else:
            is_national = (jurisdiction_id in ('LY', 'LBY'))
            payload: Dict[str, Any] = {**self._national}

            # Include recent disaster events for hazard domain
            if self._disaster_events:
                payload['recent_disaster_events'] = self._disaster_events

            if not is_national:
                payload['_geographic_proxy'] = 'national_average'
                payload['_proxy_note'] = (
                    'بيانات النزوح الداخلي من IDMC متاحة على المستوى الوطني فقط — '
                    'يُستخدم المتوسط الوطني كبديل موثق لجميع البلديات. / '
                    'IDMC data available at national level only — '
                    'national figure applied to all municipalities as documented proxy.'
                )

            payload['_last_updated'] = self._last_refresh
            result = self._wrap(payload)

        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        if not os.path.isdir(CACHE_DIR):
            return False
        return any(f.endswith('.csv') for f in os.listdir(CACHE_DIR))

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'IDMC — Internal Displacement Monitoring Centre (via OCHA HDX)',
            'name_ar': 'مركز رصد النزوح الداخلي — عبر منصة HDX للبيانات الإنسانية',
            'url': 'https://data.humdata.org/dataset/idmc-idp-data-lby',
            'update_frequency': 'annual_auto',
            'license': 'CC BY-IGO 3.0',
            'geographic_coverage': 'Libya — national level',
            'access_method': 'hdx_csv_cached',
            'cache_dir': CACHE_DIR,
            'notes': (
                'IDMC provides annual new displacement and total IDP stock for Libya '
                'from 2011 to present. Disaster-specific events (floods, storms) are '
                'available with location and displaced-person counts. Direct IDMC API '
                'requires registration; this connector uses openly published HDX files.'
            ),
        }

    # ------------------------------------------------------------------
    # Scheduled refresh
    # ------------------------------------------------------------------

    def refresh(self) -> Dict[str, Any]:
        """
        Download fresh IDMC CSV files from OCHA HDX.
        Called by APScheduler (weekly HDX job).
        """
        summary: Dict[str, Any] = {
            'files_attempted': 0,
            'files_ok': 0,
            'errors': [],
            'timestamp': datetime.utcnow().isoformat(),
        }

        for key, url in RESOURCE_URLS.items():
            summary['files_attempted'] += 1
            raw = self._download(url)
            if raw is None:
                summary['errors'].append(f'{key}: download failed')
                continue
            cache_file = os.path.join(CACHE_DIR, f'{key}.csv')
            with open(cache_file, 'wb') as f:
                f.write(raw)
            summary['files_ok'] += 1
            logger.info(f'IDMC: downloaded {key}.csv ({len(raw)} bytes)')

        # Reload in-memory
        self._national = {}
        self._disaster_events = []
        self._cache_loaded = False
        self._cache = {}
        self._load_from_disk()

        logger.info(f"IDMC refresh: {summary['files_ok']}/{summary['files_attempted']} ok")
        return summary

    # ------------------------------------------------------------------
    # Disk cache loading
    # ------------------------------------------------------------------

    def _load_from_disk(self):
        self._cache_loaded = True
        latest_mtime = 0.0

        annual_file = os.path.join(CACHE_DIR, 'annual_idp.csv')
        disaster_file = os.path.join(CACHE_DIR, 'disaster_events.csv')

        if os.path.exists(annual_file):
            self._parse_annual_idp(annual_file)
            latest_mtime = max(latest_mtime, os.path.getmtime(annual_file))

        if os.path.exists(disaster_file):
            self._parse_disaster_events(disaster_file)
            latest_mtime = max(latest_mtime, os.path.getmtime(disaster_file))

        if latest_mtime > 0:
            self._last_refresh = datetime.fromtimestamp(latest_mtime).isoformat()

    def _parse_annual_idp(self, filepath: str):
        """
        Parse annual IDP CSV. Takes the most recent year's values.
        Columns: iso3, country_name, year, new_displacement, new_displacement_rounded,
                 total_displacement, total_displacement_rounded
        """
        best_year = -1
        best_row: Dict[str, str] = {}
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('iso3', '').upper() != 'LBY':
                    continue
                try:
                    yr = int(row.get('year', 0))
                except (ValueError, TypeError):
                    continue
                if yr > best_year:
                    best_year = yr
                    best_row = row

        if best_row:
            self._national = {
                'data_year': best_year,
                'new_displacements_conflict': self._to_float(best_row.get('new_displacement')),
                'new_displacements_conflict_rounded': self._to_float(best_row.get('new_displacement_rounded')),
                'total_displacement_stock': self._to_float(best_row.get('total_displacement')),
                'total_displacement_rounded': self._to_float(best_row.get('total_displacement_rounded')),
            }
            logger.info(f'IDMC: loaded annual IDP data for {best_year}')

    def _parse_disaster_events(self, filepath: str):
        """
        Parse disaster-specific displacement events CSV.
        Columns: iso3, country_name, year, start_date, end_date, event_name,
                 hazard_category, hazard_category_name, hazard_sub_category,
                 hazard_type_name, new_displacements, new_displacements_rounded, ...
        """
        events: List[Dict[str, Any]] = []
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('iso3', '').upper() != 'LBY':
                    continue
                try:
                    yr = int(row.get('year', 0))
                except (ValueError, TypeError):
                    yr = 0
                if yr < RECENT_EVENTS_FROM_YEAR:
                    continue
                displaced = self._to_float(row.get('new_displacement') or row.get('new_displacement_rounded'))
                event: Dict[str, Any] = {
                    'year': yr,
                    'event_name': (row.get('event_name') or '').strip(),
                    'hazard_type': (row.get('hazard_type_name') or row.get('hazard_category_name') or '').strip(),
                    'start_date': (row.get('start_date') or '').strip(),
                    'new_displacements': displaced,
                }
                events.append(event)

        # Sort by most recent first
        self._disaster_events = sorted(events, key=lambda e: e.get('year', 0), reverse=True)
        logger.info(f'IDMC: loaded {len(self._disaster_events)} disaster events from {RECENT_EVENTS_FROM_YEAR}+')

    def _to_float(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(str(val).replace(',', '').strip())
        except (ValueError, TypeError):
            return None

    def _download(self, url: str, timeout: int = 30) -> Optional[bytes]:
        import urllib.request
        import urllib.error
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Libya-CARA/1.0 (IDMC displacement data via HDX)'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            logger.warning(f'IDMC download failed ({url}): {e}')
            return None
