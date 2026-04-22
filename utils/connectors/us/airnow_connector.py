"""
US connector stub — EPA AirNow.

For a full US state deployment, implement this connector by adapting
utils/air_quality_data.py from the Wisconsin CARA repository.

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
    Stub connector for EPA AirNow (US deployments only).

    To implement:
    1. Copy utils/air_quality_data.py from the Wisconsin repo into this class.
    2. Map the jurisdiction_id to the nearest AirNow monitoring stations.
    3. Return data in the standard connector dict format.
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
            "Implement by adapting utils/air_quality_data.py from the Wisconsin repo."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
