"""
World Bank Open Data connector.

Fetches development and demographic indicators for any country.
No API key required.

API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
Base URL: https://api.worldbank.org/v2/
"""

import logging
import requests
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

WB_BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    'population':               'SP.POP.TOTL',
    'population_density':       'EN.POP.DNST',
    'gdp_per_capita':           'NY.GDP.PCAP.CD',
    'poverty_headcount':        'SI.POV.DDAY',
    'gini_index':               'SI.POV.GINI',
    'urban_population_pct':     'SP.URB.TOTL.IN.ZS',
    'access_clean_water':       'SH.H2O.BASW.ZS',
    'access_sanitation':        'SH.STA.BASS.ZS',
    'access_electricity':       'EG.ELC.ACCS.ZS',
    'mobile_subscriptions':     'IT.CEL.SETS.P2',
    'internet_users_pct':       'IT.NET.USER.ZS',
    'health_expenditure_pct_gdp': 'SH.XPD.CHEX.GD.ZS',
    'food_insecurity_pct':      'SN.ITK.MSFI.ZS',
    'refugee_population_orig':  'SM.POP.REFG.OR',
    'refugee_population_asyl':  'SM.POP.REFG',
}


class WorldBankConnector(BaseConnector):
    """
    Fetches World Bank development indicators for a given country code (ISO2).

    These indicators are used to compute social vulnerability scores
    and resilience factors in the health metrics and conflict/displacement domains.
    """

    CACHE_DURATION_SECONDS = 86400 * 30

    def __init__(self, country_code: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.country_code = country_code.lower()

    def is_available(self) -> bool:
        try:
            r = requests.get(
                f"{WB_BASE}/country/{self.country_code}/indicator/SP.POP.TOTL",
                params={'format': 'json', 'mrv': 1},
                timeout=8
            )
            return r.status_code == 200
        except requests.RequestException:
            return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'World Bank Open Data',
            'url': 'https://data.worldbank.org',
            'update_frequency': 'Annual',
            'license': 'Creative Commons Attribution 4.0',
            'geographic_coverage': 'Global (all World Bank member countries)',
            'notes': 'No API key required. Uses most recent available year per indicator.',
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
                logger.debug(f"World Bank {indicator_code} for {country}: {e}")

        if not results:
            return self._unavailable_response(
                f"No World Bank data returned for country code {country}"
            )

        results['vulnerability_index'] = self._calculate_vulnerability(results)
        return self._wrap(results)

    def _fetch_indicator(self, indicator_code: str, country: str) -> Optional[float]:
        url = f"{WB_BASE}/country/{country}/indicator/{indicator_code}"
        r = requests.get(url, params={'format': 'json', 'mrv': 3}, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if not isinstance(data, list) or len(data) < 2:
            return None
        for entry in data[1] or []:
            if entry.get('value') is not None:
                return float(entry['value'])
        return None

    def _calculate_vulnerability(self, data: Dict[str, Any]) -> float:
        poverty = data.get('poverty_headcount', 0) or 0
        no_water = 100 - (data.get('access_clean_water', 100) or 100)
        no_sanitation = 100 - (data.get('access_sanitation', 100) or 100)
        no_electricity = 100 - (data.get('access_electricity', 100) or 100)
        food_insec = data.get('food_insecurity_pct', 0) or 0

        score = (
            min(1.0, poverty / 50.0) * 0.25 +
            min(1.0, no_water / 50.0) * 0.20 +
            min(1.0, no_sanitation / 50.0) * 0.20 +
            min(1.0, no_electricity / 50.0) * 0.15 +
            min(1.0, food_insec / 50.0) * 0.20
        )
        return round(score, 4)
