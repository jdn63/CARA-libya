"""
EM-DAT (Emergency Events Database) connector.

EM-DAT is the international disaster database maintained by the Centre for
Research on Epidemiology of Disasters (CRED) at UC Louvain, Belgium.

Access requires free registration at: https://www.emdat.be/
API: https://www.emdat.be/api/

Environment variable required: EMDAT_API_KEY (obtained after registration)
"""

import logging
import os
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

EMDAT_API = "https://www.emdat.be/api/emdat"

DISASTER_GROUPS = {
    'natural': ['Geophysical', 'Meteorological', 'Hydrological', 'Climatological', 'Biological'],
    'technological': ['Industrial Accident', 'Transport Accident', 'Miscellaneous Accident'],
}


class EMDATConnector(BaseConnector):
    """
    Fetches historical disaster data from EM-DAT for a given country.

    Returns:
        - total_events_10yr: total recorded disaster events in past 10 years
        - events_by_type: dict of disaster type -> count
        - total_deaths_10yr: cumulative deaths across all events
        - total_affected_10yr: cumulative affected persons
        - economic_damage_usd: total economic damage (USD thousands)
        - dominant_hazard: most frequent disaster type
        - disaster_risk_score: normalized [0,1] score for use in risk engine
    """

    CACHE_DURATION_SECONDS = 86400 * 30

    def __init__(self, country: str, iso2: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.country = country
        self.iso2 = iso2.upper()
        self.api_key = os.environ.get('EMDAT_API_KEY')

    def is_available(self) -> bool:
        return bool(self.api_key)

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'EM-DAT (Emergency Events Database, CRED/UCLouvain)',
            'url': 'https://www.emdat.be',
            'update_frequency': 'Monthly',
            'license': 'Free for non-commercial use with registration',
            'geographic_coverage': 'Global',
            'notes': 'Requires free registration and API key. Set EMDAT_API_KEY. '
                     'Coverage begins 1900; most comprehensive from 1988 onward.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return self._unavailable_response(
                "EM-DAT API key not configured. Set EMDAT_API_KEY after registering at emdat.be"
            )

        current_year = datetime.utcnow().year
        start_year = current_year - 10

        try:
            params = {
                'key': self.api_key,
                'country': self.iso2,
                'startyear': start_year,
                'endyear': current_year,
                'classification': 'natural',
            }
            r = requests.get(EMDAT_API, params=params, timeout=30)
            r.raise_for_status()
            events = r.json()

            return self._wrap(self._process_events(events))

        except requests.RequestException as e:
            return self._unavailable_response(f"EM-DAT request failed: {e}")
        except Exception as e:
            return self._unavailable_response(f"EM-DAT processing error: {e}")

    def _process_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not events:
            return {
                'total_events_10yr': 0,
                'events_by_type': {},
                'total_deaths_10yr': 0,
                'total_affected_10yr': 0,
                'economic_damage_usd': 0,
                'dominant_hazard': 'None',
                'disaster_risk_score': 0.0,
                '_last_updated': datetime.utcnow().isoformat(),
            }

        by_type: Dict[str, int] = {}
        total_deaths = 0
        total_affected = 0
        total_damage = 0.0

        for event in events:
            dtype = event.get('disaster_type') or event.get('type') or 'Unknown'
            by_type[dtype] = by_type.get(dtype, 0) + 1
            total_deaths += int(event.get('total_deaths', 0) or 0)
            total_affected += int(event.get('total_affected', 0) or 0)
            total_damage += float(event.get('total_damage', 0) or 0)

        dominant = max(by_type, key=by_type.get) if by_type else 'None'
        total = len(events)

        frequency_score = min(1.0, total / 50.0)
        mortality_score = min(1.0, total_deaths / 10000.0)
        affected_score = min(1.0, total_affected / 1_000_000.0)
        risk_score = (frequency_score * 0.40 + mortality_score * 0.35 + affected_score * 0.25)

        return {
            'total_events_10yr': total,
            'events_by_type': by_type,
            'total_deaths_10yr': total_deaths,
            'total_affected_10yr': total_affected,
            'economic_damage_usd': total_damage * 1000,
            'dominant_hazard': dominant,
            'disaster_risk_score': round(risk_score, 4),
            '_last_updated': datetime.utcnow().isoformat(),
        }
