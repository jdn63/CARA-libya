"""
GADM (Global Administrative Areas) boundary connector.

Downloads and caches GeoJSON boundary files for any country at any
administrative level (0=country, 1=state/province, 2=district/county, etc.).

No API key required.
Data: https://gadm.org
Download URL: https://geodata.ucdavis.edu/gadm/gadm4.1/json/
"""

import json
import logging
import os
import requests
from typing import Any, Dict, List, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

GADM_BASE = "https://geodata.ucdavis.edu/gadm/gadm4.1/json"
GADM_CACHE_DIR = os.path.join("data", "gadm")


class GADMConnector(BaseConnector):
    """
    Downloads GADM GeoJSON boundary files for any country.
    Files are cached locally after first download (they are large).

    Usage:
        connector = GADMConnector(country_code='KEN', level=2)
        geojson = connector.fetch('country')
        features = geojson['features']
    """

    CACHE_DURATION_SECONDS = 86400 * 365

    def __init__(self, country_code: str, level: int = 2,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.country_code = country_code.upper()
        self.level = level
        os.makedirs(GADM_CACHE_DIR, exist_ok=True)

    def is_available(self) -> bool:
        try:
            r = requests.head(self._url(), timeout=8)
            return r.status_code < 400
        except requests.RequestException:
            return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'GADM (Global Administrative Areas)',
            'url': 'https://gadm.org',
            'update_frequency': 'Periodic (major releases ~every 2 years)',
            'license': 'Free for non-commercial use. See https://gadm.org/license.html',
            'geographic_coverage': 'Global',
            'notes': 'Provides administrative boundary polygons for every country at '
                     'multiple administrative levels.',
        }

    def fetch(self, jurisdiction_id: str = 'country', **kwargs) -> Dict[str, Any]:
        cache_path = self._cache_path()

        if os.path.exists(cache_path):
            logger.info(f"Loading GADM from cache: {cache_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
            return self._wrap({'geojson': geojson, '_last_updated': None})

        logger.info(f"Downloading GADM {self.country_code} level {self.level}")
        try:
            r = requests.get(self._url(), timeout=120, stream=True)
            r.raise_for_status()
            geojson = r.json()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f)
            return self._wrap({'geojson': geojson, '_last_updated': None})
        except requests.RequestException as e:
            return self._unavailable_response(f"GADM download failed: {e}")
        except Exception as e:
            return self._unavailable_response(f"GADM parse error: {e}")

    def get_features(self) -> List[Dict[str, Any]]:
        """Return the list of GeoJSON features (one per administrative unit)."""
        result = self.fetch()
        if not result['available']:
            return []
        return result['geojson'].get('features', [])

    def get_jurisdiction_list(self) -> List[Dict[str, str]]:
        """
        Return a simplified list of jurisdictions suitable for populating
        the CARA jurisdiction dropdown.

        Each entry: {'id': GID, 'name': NAME_n, 'level': n}
        """
        features = self.get_features()
        items = []
        name_key = f'NAME_{self.level}'
        gid_key = f'GID_{self.level}'
        for feat in features:
            props = feat.get('properties', {})
            gid = props.get(gid_key, '')
            name = props.get(name_key, '')
            if gid and name:
                items.append({'id': gid, 'name': name, 'level': self.level})
        return sorted(items, key=lambda x: x['name'])

    def _url(self) -> str:
        return f"{GADM_BASE}/gadm41_{self.country_code}_{self.level}.json"

    def _cache_path(self) -> str:
        return os.path.join(GADM_CACHE_DIR, f"gadm41_{self.country_code}_{self.level}.json")
