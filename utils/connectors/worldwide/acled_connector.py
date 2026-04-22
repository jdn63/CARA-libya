"""
ACLED (Armed Conflict Location and Event Data Project) connector.

Fetches conflict event data for any country or region. ACLED provides
near-real-time data on political violence and protest events globally.

Registration required (free): https://acleddata.com/register/
API documentation: https://acleddata.com/acleddatanew/wp-content/uploads/dlm_uploads/2019/01/ACLED_API_User-Guide_2019.12.10.pdf

Environment variable required: ACLED_API_KEY and ACLED_EMAIL
"""

import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

ACLED_BASE = "https://api.acleddata.com/acled/read"

EVENT_TYPES = {
    'battles':                      'Battles',
    'explosions_remote_violence':   'Explosions/Remote violence',
    'violence_against_civilians':   'Violence against civilians',
    'protests':                     'Protests',
    'riots':                        'Riots',
    'strategic_developments':       'Strategic developments',
}

FATALITY_TYPES = ['battles', 'explosions_remote_violence', 'violence_against_civilians']


class ACLEDConnector(BaseConnector):
    """
    Fetches ACLED conflict event data for a given country and administrative region.

    Returns:
        - total_events_12mo: total events in past 12 months
        - violent_events_12mo: battles + explosions + violence against civilians
        - fatalities_12mo: total fatalities in past 12 months
        - events_by_type: dict of event_type -> count
        - trend_direction: 'increasing', 'stable', 'decreasing'
        - conflict_intensity_score: normalized [0,1] score for use in risk engine
        - hotspot_districts: list of admin2 names with highest event concentration
    """

    CACHE_DURATION_SECONDS = 86400 * 7

    def __init__(self, country: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.country = country
        self.api_key = os.environ.get('ACLED_API_KEY')
        self.email = os.environ.get('ACLED_EMAIL')

    def is_available(self) -> bool:
        return bool(self.api_key and self.email)

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'ACLED (Armed Conflict Location and Event Data Project)',
            'url': 'https://acleddata.com',
            'update_frequency': 'Weekly',
            'license': 'Free for non-commercial use with registration',
            'geographic_coverage': 'Global',
            'notes': 'Requires free registration and API key. '
                     'Set ACLED_API_KEY and ACLED_EMAIL environment variables.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return self._unavailable_response(
                "ACLED API key not configured. Set ACLED_API_KEY and ACLED_EMAIL."
            )

        admin1 = kwargs.get('admin1')
        admin2 = kwargs.get('admin2')
        lookback_years = kwargs.get('lookback_years', 1)

        date_from = (datetime.utcnow() - timedelta(days=365 * lookback_years)).strftime('%Y-%m-%d')
        date_to = datetime.utcnow().strftime('%Y-%m-%d')

        params = {
            'key': self.api_key,
            'email': self.email,
            'country': self.country,
            'event_date': f'{date_from}|{date_to}',
            'event_date_where': 'BETWEEN',
            'limit': 5000,
            'fields': 'event_date|event_type|sub_event_type|admin1|admin2|location|fatalities|latitude|longitude',
        }
        if admin1:
            params['admin1'] = admin1
        if admin2:
            params['admin2'] = admin2

        try:
            r = requests.get(ACLED_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            if 'data' not in data:
                return self._unavailable_response("ACLED returned unexpected response structure")

            events = data['data']
            return self._wrap(self._process_events(events))

        except requests.RequestException as e:
            return self._unavailable_response(f"ACLED API request failed: {e}")
        except Exception as e:
            return self._unavailable_response(f"ACLED processing error: {e}")

    def _process_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(events)
        violent_types = {'Battles', 'Explosions/Remote violence', 'Violence against civilians'}
        violent = sum(1 for e in events if e.get('event_type') in violent_types)
        fatalities = sum(int(e.get('fatalities', 0) or 0) for e in events)

        by_type: Dict[str, int] = {}
        for e in events:
            et = e.get('event_type', 'Unknown')
            by_type[et] = by_type.get(et, 0) + 1

        by_admin2: Dict[str, int] = {}
        for e in events:
            a2 = e.get('admin2', 'Unknown')
            by_admin2[a2] = by_admin2.get(a2, 0) + 1

        hotspots = sorted(by_admin2.items(), key=lambda x: x[1], reverse=True)[:5]

        midpoint = len(events) // 2
        first_half = sum(1 for i, e in enumerate(events) if i < midpoint and
                         e.get('event_type') in violent_types)
        second_half = violent - first_half
        if second_half > first_half * 1.15:
            trend = 'increasing'
        elif second_half < first_half * 0.85:
            trend = 'decreasing'
        else:
            trend = 'stable'

        raw_score = min(1.0, (violent * 0.6 + fatalities * 0.4 / max(total, 1)) / 100.0)
        conflict_score = round(raw_score, 4)

        return {
            'total_events_12mo': total,
            'violent_events_12mo': violent,
            'fatalities_12mo': fatalities,
            'events_by_type': by_type,
            'trend_direction': trend,
            'conflict_intensity_score': conflict_score,
            'hotspot_districts': [name for name, _ in hotspots],
            '_last_updated': datetime.utcnow().isoformat(),
        }
