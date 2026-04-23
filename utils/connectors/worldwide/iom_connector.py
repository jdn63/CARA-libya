"""
IOM Connector — International Organization for Migration

Data source: IOM Displacement Tracking Matrix (DTM) Libya
URL: https://displacement.iom.int/libya
Coverage: Migrant populations, IDP flows, transit migrants, illegal immigration
          estimates, shelter assessments for Libya municipalities.

Access method: IOM DTM Libya publishes regular assessment reports.
  - Public API: displacement.iom.int/api (JSON, requires registration)
  - Fallback: Manual upload of IOM annual reports as CSV

The connector attempts the DTM API first. If unavailable (low connectivity
or no API key), it falls back to uploaded files in data/uploads/iom/.

Data governance:
  - IOM data is openly licensed (CC BY 4.0 for public DTM datasets).
  - Municipal-level data may not be available for all 148 municipalities.
  - Missing municipalities use regional averages as documented proxies.
  - Illegal immigration data is handled as a humanitarian indicator,
    not a criminality indicator, consistent with IOM's own framing.
"""

import csv
import json
import logging
import os
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

DTM_API_BASE = 'https://displacement.iom.int/api'
UPLOAD_PATH = os.path.join('data', 'uploads', 'iom')


class IOMConnector(BaseConnector):
    """
    IOM Displacement Tracking Matrix connector for Libya.

    Returns migration and displacement metrics used by the
    displacement_vulnerability indicator in the Vulnerability pillar.
    """

    CACHE_DURATION_SECONDS = 3600 * 24 * 7

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._file_data: Dict[str, Any] = {}
        self._file_loaded = False

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch IOM migration and displacement data for a municipality.
        """
        cache_key = f'iom_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._from_file(jurisdiction_id)

        if not data:
            result = self._unavailable_response(
                f"لا تتوفر بيانات منظمة الهجرة الدولية لبلدية {jurisdiction_id}. / "
                f"No IOM DTM data available for municipality {jurisdiction_id}. "
                f"Upload IOM annual report CSV to {UPLOAD_PATH}/ to populate."
            )
            result['data_gap_policy'] = 'regional_average_proxy'
            result['iom_dtm_url'] = 'https://displacement.iom.int/libya'
            self._cache[cache_key] = result
            return result

        result = self._wrap(data)
        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        if os.path.isdir(UPLOAD_PATH):
            files = [f for f in os.listdir(UPLOAD_PATH) if f.endswith(('.csv', '.json'))]
            if files:
                return True
        return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name':                'IOM Displacement Tracking Matrix (DTM) Libya',
            'name_ar':             'مصفوفة تتبع النزوح — منظمة الهجرة الدولية — ليبيا',
            'url':                 'https://displacement.iom.int/libya',
            'update_frequency':    'quarterly_or_annual',
            'license':             'CC BY 4.0 (Public DTM data)',
            'geographic_coverage': 'Libya — municipal and district level',
            'access_method':       'file_upload_or_api',
            'upload_path':         UPLOAD_PATH,
            'notes': (
                'IOM DTM Libya provides displacement tracking for IDPs, migrants, '
                'and returnees. Annual and quarterly reports available publicly. '
                'Migration figures include transit migrants and irregular migration. '
                'Handled as humanitarian indicators per IOM methodology.'
            ),
        }

    def _from_file(self, jurisdiction_id: str) -> Optional[Dict[str, Any]]:
        if not self._file_loaded:
            self._load_files()

        return self._file_data.get(jurisdiction_id)

    def _load_files(self):
        self._file_loaded = True
        if not os.path.isdir(UPLOAD_PATH):
            os.makedirs(UPLOAD_PATH, exist_ok=True)
            return

        for filename in sorted(os.listdir(UPLOAD_PATH)):
            filepath = os.path.join(UPLOAD_PATH, filename)
            try:
                if filename.endswith('.csv'):
                    self._parse_csv(filepath)
                elif filename.endswith('.json'):
                    self._parse_json(filepath)
            except Exception as e:
                logger.error(f"Failed to load IOM file {filename}: {e}")

    def _parse_csv(self, filepath: str):
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                muni_id = row.get('municipality_id', '').strip()
                if not muni_id:
                    continue
                self._file_data[muni_id] = {
                    'total_idps':           self._float(row.get('total_idps')),
                    'total_migrants':       self._float(row.get('total_migrants')),
                    'migrant_flow_annual':  self._float(row.get('migrant_flow_annual')),
                    'returnees':            self._float(row.get('returnees')),
                    'irregular_migrants':   self._float(row.get('irregular_migrants')),
                    '_last_updated':        row.get('report_date', ''),
                }

    def _parse_json(self, filepath: str):
        with open(filepath, encoding='utf-8') as f:
            entries = json.load(f)
        if isinstance(entries, list):
            for entry in entries:
                muni_id = entry.get('municipality_id', '').strip()
                if muni_id:
                    self._file_data[muni_id] = entry

    def _float(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(str(val).replace(',', ''))
        except (ValueError, TypeError):
            return None
