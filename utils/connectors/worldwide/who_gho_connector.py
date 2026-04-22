"""
WHO Global Health Observatory (GHO) data connector.

Fetches health indicators for any country from the WHO GHO OData API.
No API key required. Coverage: all WHO member states.

API documentation: https://www.who.int/data/gho/info/gho-odata-api
Base URL: https://ghoapi.azureedge.net/api/
"""

import logging
import requests
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

GHO_BASE = "https://ghoapi.azureedge.net/api"

INDICATORS = {
    'life_expectancy':          'WHOSIS_000001',
    'infant_mortality':         'MDG_0000000001',
    'under5_mortality':         'MDG_0000000007',
    'maternal_mortality':       'MDG_0000000026',
    'measles_vaccination':      'WHS8_110',
    'dtp3_vaccination':         'WHS4_100',
    'skilled_birth_attendance': 'WHS4_543',
    'physicians_per_10k':       'HRH_14',
    'hospital_beds_per_10k':    'WHS6_102',
    'oop_health_expenditure':   'GHED_OOPC_pc_USD',
    'malaria_incidence':        'MALARIA_EST_INCIDENCE',
    'tb_incidence':             'MDG_0000000020',
    'hiv_prevalence':           'HIV_0000000006',
    'dengue_incidence':         'WHS3_62',
}


class WHOGHOConnector(BaseConnector):
    """
    Fetches WHO GHO health indicators for a given country.
    Returns country-level aggregates; sub-national breakdowns are
    not available through the GHO API and must be sourced locally.
    """

    CACHE_DURATION_SECONDS = 86400 * 30

    def __init__(self, country_code: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.country_code = country_code.upper()

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{GHO_BASE}/WHOSIS_000001", timeout=8,
                             params={'$filter': f"SpatialDim eq '{self.country_code}'",
                                     '$top': '1'})
            return r.status_code == 200
        except requests.RequestException:
            return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'WHO Global Health Observatory (GHO)',
            'url': 'https://www.who.int/data/gho',
            'update_frequency': 'Annual',
            'license': 'CC BY-NC-SA 3.0 IGO',
            'geographic_coverage': 'Global (all WHO member states)',
            'notes': 'Country-level aggregates only. Sub-national data must be sourced locally.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        country = kwargs.get('country_code', self.country_code)
        results = {}

        for metric, indicator_code in INDICATORS.items():
            try:
                value = self._fetch_indicator(indicator_code, country)
                if value is not None:
                    results[metric] = value
            except Exception as e:
                logger.debug(f"GHO {indicator_code} for {country}: {e}")

        if not results:
            return self._unavailable_response(
                f"No WHO GHO data returned for country code {country}"
            )

        results['country_code'] = country
        return self._wrap(results)

    def _fetch_indicator(self, indicator_code: str, country: str) -> Optional[float]:
        url = f"{GHO_BASE}/{indicator_code}"
        params = {
            '$filter': f"SpatialDim eq '{country}' and Dim1 eq 'BTSX'",
            '$orderby': 'TimeDim desc',
            '$top': '1',
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            params.pop('$filter')
            params['$filter'] = f"SpatialDim eq '{country}'"
            r = requests.get(url, params=params, timeout=10)

        if r.status_code == 200:
            data = r.json().get('value', [])
            if data and data[0].get('NumericValue') is not None:
                return float(data[0]['NumericValue'])
        return None

    def get_all_indicators(self, country: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method to fetch all indicators at once."""
        return self.fetch('country', country_code=country or self.country_code)
