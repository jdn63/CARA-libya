"""
US connector stub — NOAA National Weather Service.

For a full US state deployment, implement this connector by adapting
utils/heat_risk.py from the Wisconsin CARA repository.

NWS API is keyless: https://www.weather.gov/documentation/services-web-api
"""

import logging
from typing import Any, Dict

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class NWSConnector(BaseConnector):
    """
    Stub connector for NOAA NWS heat forecast data (US deployments only).

    To implement:
    1. Copy utils/heat_risk.py from the Wisconsin repo into this class.
    2. Map the jurisdiction_id (state county FIPS or name) to NWS grid points.
    3. Return data in the standard connector dict format.
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
            "Implement by adapting utils/heat_risk.py from the Wisconsin repo."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
