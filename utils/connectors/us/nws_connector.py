"""
US connector stub — NOAA National Weather Service.

Placeholder adapter retained for any future fork that targets a US state
(profile == "us_state" in config/jurisdiction.yaml). The Libya deployment
never instantiates this class.

NWS API is keyless: https://www.weather.gov/documentation/services-web-api
"""

import logging
from typing import Any, Dict

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class NWSConnector(BaseConnector):
    """
    Stub connector for NOAA NWS heat / weather alert data (us_state profile only).

    To implement for a US-state fork:
    1. Replace fetch() with a real call against the NWS API
       (/points, /gridpoints, /alerts/active endpoints).
    2. Map the jurisdiction_id (county FIPS or place name) to NWS grid points.
    3. Return data in the standard BaseConnector dict format
       (see utils/connectors/base_connector.py).
    """

    name = "nws"
    description = "NOAA NWS API — heat forecasts and weather alerts (US only, keyless)"
    requires_key = False
    refresh_interval_hours = 24

    def is_available(self) -> bool:
        return True

    def fetch(self, jurisdiction_id: str = "", **kwargs) -> Dict[str, Any]:
        logger.warning(
            "NWSConnector.fetch() is a stub. "
            "Implement against https://www.weather.gov/documentation/services-web-api for a us_state fork."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
