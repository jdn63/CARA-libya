"""
OpenAQ connector.

Fetches real-time and historical air quality data from the OpenAQ platform.
OpenAQ aggregates air quality data from government monitoring stations worldwide.

No API key required for basic access (rate limited). Free API key available
at https://openaq.org for higher limits.

API documentation: https://docs.openaq.org
"""

import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

OPENAQ_BASE = "https://api.openaq.org/v3"

AQI_BREAKPOINTS = {
    'pm25': [
        (0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ],
    'pm10': [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500),
    ],
}


class OpenAQConnector(BaseConnector):
    """
    Fetches air quality data for a given country using the OpenAQ API.

    Returns:
        - pm25_avg: average PM2.5 concentration (ug/m3)
        - pm10_avg: average PM10 concentration (ug/m3)
        - o3_avg: average ozone (ppb)
        - no2_avg: average NO2 (ug/m3)
        - aqi_category: 'Good', 'Moderate', 'Unhealthy for Sensitive Groups', etc.
        - stations_count: number of monitoring stations found
        - data_coverage_pct: percentage of past 30 days with observations
        - air_quality_score: normalized [0,1] risk score (higher = worse air quality)
    """

    CACHE_DURATION_SECONDS = 3600 * 6

    def __init__(self, country_code: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.country_code = country_code.upper()
        self.api_key = os.environ.get('OPENAQ_API_KEY', '')

    def is_available(self) -> bool:
        try:
            headers = {'X-API-Key': self.api_key} if self.api_key else {}
            r = requests.get(
                f"{OPENAQ_BASE}/locations",
                params={'countries_id': self.country_code, 'limit': 1},
                headers=headers,
                timeout=10
            )
            return r.status_code == 200
        except requests.RequestException:
            return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'OpenAQ (Open Air Quality)',
            'url': 'https://openaq.org',
            'update_frequency': 'Real-time (hourly averages)',
            'license': 'CC BY 4.0',
            'geographic_coverage': 'Global (90+ countries, 30,000+ monitoring stations)',
            'notes': 'No API key required for basic access. Register at openaq.org '
                     'for higher rate limits. Coverage varies by country.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        city = kwargs.get('city')
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=30)

        headers = {'X-API-Key': self.api_key} if self.api_key else {}
        params = {
            'countries_id': self.country_code,
            'date_from': date_from.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'date_to': date_to.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'limit': 100,
        }
        if city:
            params['city'] = city

        try:
            r = requests.get(f"{OPENAQ_BASE}/locations", params=params,
                             headers=headers, timeout=20)
            r.raise_for_status()
            locations = r.json().get('results', [])

            if not locations:
                return self._unavailable_response(
                    f"No OpenAQ monitoring stations found for {self.country_code}"
                )

            pollutants = self._aggregate_pollutants(locations)
            return self._wrap({**pollutants, '_last_updated': date_to.isoformat()})

        except requests.RequestException as e:
            return self._unavailable_response(f"OpenAQ request failed: {e}")
        except Exception as e:
            return self._unavailable_response(f"OpenAQ processing error: {e}")

    def _aggregate_pollutants(self, locations: List[Dict]) -> Dict[str, Any]:
        readings: Dict[str, List[float]] = {'pm25': [], 'pm10': [], 'o3': [], 'no2': []}

        for loc in locations:
            for sensor in loc.get('sensors', []):
                param = sensor.get('parameter', {}).get('name', '').lower()
                value = sensor.get('latest', {}).get('value')
                if value is not None and param in readings:
                    readings[param].append(float(value))

        averages: Dict[str, Optional[float]] = {}
        for pollutant, values in readings.items():
            averages[f"{pollutant}_avg"] = (
                round(sum(values) / len(values), 2) if values else None
            )

        pm25 = averages.get('pm25_avg') or 0
        aqi_category = self._aqi_category(pm25, 'pm25')
        air_quality_score = min(1.0, pm25 / 150.0)

        return {
            **averages,
            'aqi_category': aqi_category,
            'stations_count': len(locations),
            'air_quality_score': round(air_quality_score, 4),
        }

    def _aqi_category(self, value: float, pollutant: str) -> str:
        categories = [
            'Good', 'Moderate', 'Unhealthy for Sensitive Groups',
            'Unhealthy', 'Very Unhealthy', 'Hazardous', 'Hazardous+'
        ]
        for i, (lo, hi, _, _) in enumerate(AQI_BREAKPOINTS.get(pollutant, [])):
            if lo <= value <= hi:
                return categories[i] if i < len(categories) else 'Hazardous+'
        return 'Unknown'
