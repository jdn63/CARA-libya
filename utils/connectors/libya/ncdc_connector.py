"""
NCDC Libya Connector — National Centre for Disease Control

Data source: Libya National Centre for Disease Control (NCDC)
Coverage: Infectious disease surveillance, vector-borne disease reports,
          outbreak notifications for Libyan municipalities.

Access method: Manual file upload (CSV/Excel)
Upload path: data/uploads/ncdc/

Data format expected:
  CSV with columns:
    - municipality_id (e.g. LY-001)
    - year, week (or year, month)
    - disease_name
    - case_count
    - death_count
    - region

This connector reads from pre-uploaded files. It does not make live API calls
because NCDC Libya does not currently provide a public API endpoint.
The deployer must arrange for periodic data uploads from NCDC.

Data governance:
  - All data from NCDC is attributed with source, upload date, and version.
  - "Data not available" is displayed honestly for municipalities with no data.
  - Regional averages are used as proxies where documented (see jurisdiction.yaml).
"""

import csv
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

UPLOAD_PATH = os.path.join('data', 'uploads', 'ncdc')


class NCDCLibyaConnector(BaseConnector):
    """
    Reads NCDC Libya disease surveillance data from uploaded files.

    Returns per-municipality disease burden indicators used by the
    Epidemiological Hazard sub-domain and the Vulnerability pillar.
    """

    CACHE_DURATION_SECONDS = 3600 * 24

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._loaded_data: Dict[str, Any] = {}
        self._load_timestamp: Optional[str] = None

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch NCDC disease data for a municipality.

        Returns:
            Dict with 'available', 'source', 'last_updated', and disease metrics.
            If no data found for the municipality, returns available=False with
            explicit messaging per the Libya CARA "data not available" policy.
        """
        cache_key = f'ncdc_{jurisdiction_id}'
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._ensure_loaded()

        muni_data = self._loaded_data.get(jurisdiction_id, {})

        if not muni_data:
            result = self._unavailable_response(
                f"لا تتوفر بيانات المراقبة الوبائية من المركز الوطني لمكافحة الأمراض "
                f"لبلدية {jurisdiction_id}. / "
                f"No NCDC disease surveillance data available for municipality {jurisdiction_id}. "
                f"Upload data to {UPLOAD_PATH}/ to populate this indicator."
            )
            result['data_gap_policy'] = 'regional_average_proxy'
            self._cache[cache_key] = result
            return result

        result = self._wrap({
            'infectious_disease_rate': muni_data.get('infectious_disease_rate'),
            'vector_borne_rate':       muni_data.get('vector_borne_rate'),
            'outbreak_count_12mo':     muni_data.get('outbreak_count_12mo'),
            'top_diseases':            muni_data.get('top_diseases', []),
            'data_year':               muni_data.get('data_year'),
            '_last_updated':           self._load_timestamp,
        })
        self._cache[cache_key] = result
        return result

    def is_available(self) -> bool:
        """Returns True if the NCDC upload directory exists and contains files."""
        if not os.path.isdir(UPLOAD_PATH):
            return False
        files = [f for f in os.listdir(UPLOAD_PATH) if f.endswith(('.csv', '.xlsx'))]
        return len(files) > 0

    def source_info(self) -> Dict[str, str]:
        return {
            'name':                 'Libya National Centre for Disease Control (NCDC)',
            'name_ar':              'المركز الوطني الليبي لمكافحة الأمراض',
            'url':                  'https://ncdc.org.ly',
            'update_frequency':     'periodic_upload',
            'license':              'Official Government Data — Restricted Use',
            'geographic_coverage':  'Libya — municipal level',
            'access_method':        'manual_file_upload',
            'upload_path':          UPLOAD_PATH,
            'notes':                (
                'NCDC Libya provides infectious disease and vector-borne disease '
                'surveillance data. No public API is currently available. '
                'Data must be uploaded manually by authorized personnel.'
            ),
        }

    def _ensure_loaded(self):
        """Load data from all CSV files in the upload directory."""
        if self._loaded_data:
            return

        if not os.path.isdir(UPLOAD_PATH):
            os.makedirs(UPLOAD_PATH, exist_ok=True)
            logger.info(f"Created NCDC upload directory: {UPLOAD_PATH}")
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
                logger.info(f"Loaded NCDC data from {filename}")
            except Exception as e:
                logger.error(f"Failed to load NCDC file {filename}: {e}")

    def _parse_csv(self, filepath: str):
        """Parse a NCDC CSV file and aggregate by municipality."""
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                muni_id = row.get('municipality_id', '').strip()
                if not muni_id:
                    continue

                if muni_id not in self._loaded_data:
                    self._loaded_data[muni_id] = {
                        'infectious_disease_rate': 0.0,
                        'vector_borne_rate': 0.0,
                        'outbreak_count_12mo': 0,
                        'top_diseases': [],
                        'data_year': row.get('year', ''),
                    }

                disease = row.get('disease_name', '').lower()
                cases = float(row.get('case_count', 0) or 0)

                vector_borne_keywords = ['malaria', 'dengue', 'west nile', 'leishmaniasis', 'sandfly']
                if any(k in disease for k in vector_borne_keywords):
                    self._loaded_data[muni_id]['vector_borne_rate'] += cases
                else:
                    self._loaded_data[muni_id]['infectious_disease_rate'] += cases

                if cases > 0 and disease not in self._loaded_data[muni_id]['top_diseases']:
                    self._loaded_data[muni_id]['top_diseases'].append(disease)
