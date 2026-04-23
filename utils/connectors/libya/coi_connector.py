"""
Centre for Coordination of Information (COI) Connector — Libya CARA

Data source: Centre for Coordination of Information (Libya)
Coverage: Emergency response capacity, NGO presence, inter-agency data,
          security incident rates, ambulance response times.

Access method: Manual file upload (CSV/Excel)
Upload path: data/uploads/coi/

This is a local Libyan government data source. No public API exists.
Data must be uploaded by authorized personnel from the Centre.

Data governance:
  - All COI data is attributed with source, upload date, and version.
  - Missing municipalities display "البيانات غير متاحة / Data not available".
  - Regional averages are used as documented proxies where data is absent.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

UPLOAD_PATH = os.path.join('data', 'uploads', 'coi')


class COILibyaConnector(BaseConnector):
    """
    Reads Centre for Coordination of Information (COI) Libya data from uploaded files.

    Returns indicators used by the Vulnerability and Coping Capacity pillars.
    """

    CACHE_DURATION_SECONDS = 3600 * 24

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._loaded_data: Dict[str, Any] = {}
        self._load_timestamp: Optional[str] = None

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch COI coordination data for a municipality.
        """
        cache_key = f'coi_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._ensure_loaded()
        muni_data = self._loaded_data.get(jurisdiction_id, {})

        if not muni_data:
            result = self._unavailable_response(
                f"لا تتوفر بيانات مركز تنسيق المعلومات لبلدية {jurisdiction_id}. / "
                f"No COI data available for municipality {jurisdiction_id}. "
                f"Upload data to {UPLOAD_PATH}/ to populate this indicator."
            )
            result['data_gap_policy'] = 'regional_average_proxy'
            self._cache[cache_key] = result
            return result

        result = self._wrap({
            'agency_staffing_gap':             muni_data.get('agency_staffing_gap'),
            'avg_ambulance_response_minutes':  muni_data.get('avg_ambulance_response_minutes'),
            'ngo_presence_score':              muni_data.get('ngo_presence_score'),
            'security_incident_rate':          muni_data.get('security_incident_rate'),
            'data_interoperability_score':     muni_data.get('data_interoperability_score'),
            'electric_grid_reliability':       muni_data.get('electric_grid_reliability'),
            '_last_updated':                   self._load_timestamp,
        })
        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        if not os.path.isdir(UPLOAD_PATH):
            return False
        files = [f for f in os.listdir(UPLOAD_PATH) if f.endswith(('.csv', '.xlsx'))]
        return len(files) > 0

    def source_info(self) -> Dict[str, str]:
        return {
            'name':                 'Centre for Coordination of Information (COI) — Libya',
            'name_ar':              'مركز تنسيق المعلومات — ليبيا',
            'url':                  '',
            'update_frequency':     'periodic_upload',
            'license':              'Official Government Data — Restricted Use',
            'geographic_coverage':  'Libya — municipal level',
            'access_method':        'manual_file_upload',
            'upload_path':          UPLOAD_PATH,
            'notes': (
                'COI Libya provides emergency response coordination data. '
                'No public API available. Data must be uploaded manually.'
            ),
        }

    def _ensure_loaded(self):
        if self._loaded_data:
            return
        if not os.path.isdir(UPLOAD_PATH):
            os.makedirs(UPLOAD_PATH, exist_ok=True)
            return
        for filename in sorted(os.listdir(UPLOAD_PATH)):
            if not filename.endswith('.csv'):
                continue
            filepath = os.path.join(UPLOAD_PATH, filename)
            try:
                self._parse_csv(filepath)
                self._load_timestamp = datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                ).isoformat()
            except Exception as e:
                logger.error(f"Failed to load COI file {filename}: {e}")

    def _parse_csv(self, filepath: str):
        numeric_fields = [
            'agency_staffing_gap', 'avg_ambulance_response_minutes',
            'ngo_presence_score', 'security_incident_rate',
            'data_interoperability_score', 'electric_grid_reliability',
        ]
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                muni_id = row.get('municipality_id', '').strip()
                if not muni_id:
                    continue
                entry = {}
                for field in numeric_fields:
                    raw = row.get(field)
                    if raw is not None and str(raw).strip():
                        try:
                            entry[field] = float(raw)
                        except ValueError:
                            pass
                self._loaded_data[muni_id] = entry
