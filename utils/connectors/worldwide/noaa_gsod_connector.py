"""
NOAA Global Surface Summary of Day (GSOD) connector.

Fetches daily meteorological data (temperature, precipitation, wind) from
NOAA's global weather station network. Covers 9,000+ stations worldwide.

No API key required for bulk data access via NOAA's THREDDS/ERDDAP servers
or the NCEI API. Optional NOAA CDO token improves rate limits.

NCEI Climate Data Online: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
GSOD FTP: https://www.ncei.noaa.gov/data/global-summary-of-the-day/
"""

import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

CDO_BASE = "https://www.ncei.noaa.gov/cdo-web/api/v2"
GSOD_BASE = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access"

HEAT_INDEX_THRESHOLDS = {
    'celsius': {'dangerous': 40, 'extreme_caution': 33, 'caution': 27},
}


class NOAAGSODConnector(BaseConnector):
    """
    Fetches NOAA GSOD climate data for a given country.

    Returns temperature statistics, heat event counts, and precipitation data
    for use in the extreme heat and natural hazards risk domains.

    Requires station IDs for the jurisdiction. The connector will attempt to
    find nearby stations using the NCEI station search if station_ids is not provided.
    """

    CACHE_DURATION_SECONDS = 86400 * 7

    def __init__(
        self,
        country_code: str,
        station_ids: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(config)
        self.country_code = country_code.upper()
        self.station_ids = station_ids or []
        self.cdo_token = os.environ.get('NOAA_CDO_TOKEN', '')

    def is_available(self) -> bool:
        try:
            r = requests.get(
                f"{CDO_BASE}/stations",
                headers={'token': self.cdo_token} if self.cdo_token else {},
                params={'locationid': f'FIPS:{self.country_code}', 'limit': 1},
                timeout=10
            )
            return r.status_code in (200, 400)
        except requests.RequestException:
            return False

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'NOAA Global Surface Summary of Day (GSOD) / NCEI CDO',
            'url': 'https://www.ncei.noaa.gov/products/land-based-station/global-summary-day',
            'update_frequency': 'Daily',
            'license': 'Public Domain (U.S. Government Work)',
            'geographic_coverage': 'Global (9,000+ stations)',
            'notes': 'No API key required. NOAA_CDO_TOKEN improves rate limits. '
                     'Coverage varies by country and year.',
        }

    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        lookback_days = kwargs.get('lookback_days', 365)
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=lookback_days)

        station_ids = self.station_ids or self._find_stations()
        if not station_ids:
            return self._unavailable_response(
                f"No GSOD stations found for {self.country_code}"
            )

        all_readings: List[Dict] = []
        for station_id in station_ids[:5]:
            readings = self._fetch_station_data(station_id, date_from, date_to)
            all_readings.extend(readings)

        if not all_readings:
            return self._unavailable_response(
                f"No GSOD observations available for {self.country_code}"
            )

        return self._wrap({
            **self._compute_statistics(all_readings),
            '_last_updated': date_to.isoformat(),
        })

    def _find_stations(self) -> List[str]:
        if not self.cdo_token:
            return []
        try:
            r = requests.get(
                f"{CDO_BASE}/stations",
                headers={'token': self.cdo_token},
                params={
                    'locationid': f'FIPS:{self.country_code}',
                    'datasetid': 'GSOD',
                    'limit': 10,
                },
                timeout=15
            )
            if r.status_code == 200:
                results = r.json().get('results', [])
                return [s['id'] for s in results]
        except Exception as e:
            logger.debug(f"GSOD station search for {self.country_code}: {e}")
        return []

    def _fetch_station_data(
        self,
        station_id: str,
        date_from: datetime,
        date_to: datetime
    ) -> List[Dict]:
        if not self.cdo_token:
            return []
        try:
            r = requests.get(
                f"{CDO_BASE}/data",
                headers={'token': self.cdo_token},
                params={
                    'datasetid': 'GSOD',
                    'stationid': station_id,
                    'startdate': date_from.strftime('%Y-%m-%d'),
                    'enddate': date_to.strftime('%Y-%m-%d'),
                    'datatypeid': 'TEMP,MAX,MIN,PRCP',
                    'limit': 1000,
                    'units': 'metric',
                },
                timeout=20
            )
            if r.status_code == 200:
                return r.json().get('results', [])
        except Exception as e:
            logger.debug(f"GSOD data fetch for {station_id}: {e}")
        return []

    def _compute_statistics(self, readings: List[Dict]) -> Dict[str, Any]:
        temps_max = [r['value'] for r in readings if r.get('datatype') == 'MAX' and r.get('value')]
        temps_min = [r['value'] for r in readings if r.get('datatype') == 'MIN' and r.get('value')]
        temps_avg = [r['value'] for r in readings if r.get('datatype') == 'TEMP' and r.get('value')]

        thresholds = HEAT_INDEX_THRESHOLDS['celsius']
        heat_days = sum(1 for t in temps_max if t >= thresholds['extreme_caution'])
        dangerous_heat_days = sum(1 for t in temps_max if t >= thresholds['dangerous'])

        avg_max = round(sum(temps_max) / len(temps_max), 1) if temps_max else None
        avg_min = round(sum(temps_min) / len(temps_min), 1) if temps_min else None
        avg_temp = round(sum(temps_avg) / len(temps_avg), 1) if temps_avg else None

        heat_score = min(1.0, heat_days / 90.0)

        return {
            'avg_max_temp_c': avg_max,
            'avg_min_temp_c': avg_min,
            'avg_temp_c': avg_temp,
            'heat_days_above_33c': heat_days,
            'dangerous_heat_days_above_40c': dangerous_heat_days,
            'heat_risk_score': round(heat_score, 4),
            'stations_used': len(set(
                r.get('station', '') for r in readings if r.get('station')
            )),
        }
