"""
IDMC (Internal Displacement Monitoring Centre) connector.

Fetches internal displacement data for any country, including conflict-induced
and disaster-induced displacement figures.

No API key required for public data access.
API: https://www.internal-displacement.org/database/displacement-data
Data portal: https://www.internal-displacement.org/global-internal-displacement-database
"""

import logging
import requests
from datetime import datetime
from typing import Any, Dict, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

IDMC_API_BASE = "https://helix-tools-api.idmcdb.org/external-api"
IDMC_DATA_BASE = "https://api.internal-displacement.org/global-report/2024"


class IDMCConnector(BaseConnector):
    """
    Fetches IDMC displacement data for a given country.

    Returns:
        - conflict_new_displacements: new displacements due to conflict (latest year)
        - disaster_new_displacements: new displacements due to disasters (latest year)
        - total_idps: total stock of internally displaced persons
        - displacement_score: normalized [0,1] score for use in risk engine
        - year: year of most recent data
        - trend_5yr: list of annual displacement figures (conflict)
    """

    CACHE_DURATION_SECONDS = 86400 * 7

    def __init__(self, iso3: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.iso3 = iso3.upper()

    def is_available(self) -> bool:
        try:
            r = requests.get(
                f"{IDMC_API_BASE}/countries/",
                params={'iso3': self.iso3},
                timeout=10
            )
            return r.status_code == 200
        except requests.RequestException:
            return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'IDMC (Internal Displacement Monitoring Centre)',
            'url': 'https://www.internal-displacement.org',
            'update_frequency': 'Annual (mid-year update)',
            'license': 'Free for non-commercial use with attribution',
            'geographic_coverage': 'Global',
            'notes': 'No API key required for public displacement figures. '
                     'Sub-national breakdown not available for all countries.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        iso3 = kwargs.get('iso3', self.iso3)

        conflict_data = self._fetch_conflict_displacement(iso3)
        disaster_data = self._fetch_disaster_displacement(iso3)
        stock_data = self._fetch_idp_stock(iso3)

        if not any([conflict_data, disaster_data, stock_data]):
            return self._unavailable_response(
                f"No IDMC displacement data available for {iso3}"
            )

        conflict_new = conflict_data.get('new_displacements', 0) or 0
        disaster_new = disaster_data.get('new_displacements', 0) or 0
        total_idps = stock_data.get('total_stock', 0) or 0

        displacement_score = self._calculate_score(
            conflict_new, disaster_new, total_idps,
            kwargs.get('population', 1_000_000)
        )

        return self._wrap({
            'conflict_new_displacements': conflict_new,
            'disaster_new_displacements': disaster_new,
            'total_new_displacements': conflict_new + disaster_new,
            'total_idps': total_idps,
            'displacement_score': displacement_score,
            'year': conflict_data.get('year') or datetime.utcnow().year - 1,
            'trend_5yr': conflict_data.get('trend_5yr', []),
            '_last_updated': datetime.utcnow().isoformat(),
        })

    def _fetch_conflict_displacement(self, iso3: str) -> Dict[str, Any]:
        try:
            r = requests.get(
                f"{IDMC_API_BASE}/conflict-statistics/",
                params={'iso3': iso3, 'limit': 10, 'ordering': '-year'},
                timeout=15
            )
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    latest = results[0]
                    trend = [
                        {'year': row.get('year'), 'new': row.get('new_displacements', 0)}
                        for row in results[:5]
                    ]
                    return {
                        'new_displacements': latest.get('new_displacements', 0),
                        'year': latest.get('year'),
                        'trend_5yr': trend,
                    }
        except Exception as e:
            logger.debug(f"IDMC conflict fetch for {iso3}: {e}")
        return {}

    def _fetch_disaster_displacement(self, iso3: str) -> Dict[str, Any]:
        try:
            r = requests.get(
                f"{IDMC_API_BASE}/disaster-statistics/",
                params={'iso3': iso3, 'limit': 5, 'ordering': '-year'},
                timeout=15
            )
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    return {
                        'new_displacements': results[0].get('new_displacements', 0),
                        'year': results[0].get('year'),
                    }
        except Exception as e:
            logger.debug(f"IDMC disaster fetch for {iso3}: {e}")
        return {}

    def _fetch_idp_stock(self, iso3: str) -> Dict[str, Any]:
        try:
            r = requests.get(
                f"{IDMC_API_BASE}/countries/",
                params={'iso3': iso3},
                timeout=15
            )
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    country = results[0]
                    return {
                        'total_stock': (
                            (country.get('total_stock_conflict') or 0) +
                            (country.get('total_stock_disaster') or 0)
                        )
                    }
        except Exception as e:
            logger.debug(f"IDMC stock fetch for {iso3}: {e}")
        return {}

    def _calculate_score(
        self,
        conflict_new: int,
        disaster_new: int,
        total_idps: int,
        population: int
    ) -> float:
        if population <= 0:
            population = 1_000_000

        conflict_rate = min(1.0, conflict_new / (population * 0.05))
        disaster_rate = min(1.0, disaster_new / (population * 0.10))
        stock_rate = min(1.0, total_idps / (population * 0.15))

        score = (conflict_rate * 0.50 + stock_rate * 0.35 + disaster_rate * 0.15)
        return round(min(1.0, score), 4)
