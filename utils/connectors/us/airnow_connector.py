"""
US connector stub — EPA AirNow.

Placeholder adapter retained for any future fork that targets a US state
(profile == "us_state" in config/jurisdiction.yaml). The Libya deployment
never instantiates this class.

API docs: https://docs.airnowapi.org/
Requires: AIRNOW_API_KEY environment variable.
"""

import logging
import os
from typing import Any, Dict

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class AirNowConnector(BaseConnector):
    """
    Stub connector for EPA AirNow (us_state profile only).

    To implement for a US-state fork:
    1. Replace fetch() with a real call against the AirNow REST API
       (observations/zipCode or observations/latLong endpoints).
    2. Map the jurisdiction_id to the nearest AirNow monitoring stations.
    3. Return data in the standard BaseConnector dict format
       (see utils/connectors/base_connector.py).
    """

    name = "airnow"
    description = "EPA AirNow API — daily AQI readings at monitoring stations (US only)"
    requires_key = True
    refresh_interval_hours = 24

    def __init__(self):
        self.api_key = os.environ.get("AIRNOW_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def fetch(self, jurisdiction_id: str = "", **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "available": False,
                "connector": self.name,
                "message": "AIRNOW_API_KEY not set",
            }

        logger.warning(
            "AirNowConnector.fetch() is a stub. "
            "Implement against https://docs.airnowapi.org/ for a us_state fork."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
