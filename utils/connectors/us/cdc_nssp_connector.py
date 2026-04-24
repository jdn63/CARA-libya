"""
US connector stub — CDC NSSP Emergency Department Visits.

Placeholder adapter retained for any future fork that targets a US state
(profile == "us_state" in config/jurisdiction.yaml). The Libya deployment
never instantiates this class.

Endpoint (keyless): https://data.cdc.gov/resource/vutn-jzwm.json
Updated weekly. Provides percent of ED visits for Influenza, COVID-19, RSV.
"""

import logging
from typing import Any, Dict

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class CDCNSSPConnector(BaseConnector):
    """
    Stub connector for CDC NSSP respiratory ED visit surveillance (us_state profile only).

    To implement for a US-state fork:
    1. Replace fetch() with a real call against the Socrata endpoint
       https://data.cdc.gov/resource/vutn-jzwm.json.
    2. Filter by the appropriate state / jurisdiction.
    3. Return data in the standard BaseConnector dict format
       (see utils/connectors/base_connector.py).
    """

    name = "cdc_nssp"
    description = "CDC NSSP — percent ED visits for Influenza, COVID-19, RSV by state (US only, keyless)"
    requires_key = False
    refresh_interval_hours = 168

    def is_available(self) -> bool:
        return True

    def fetch(self, jurisdiction_id: str = "", **kwargs) -> Dict[str, Any]:
        logger.warning(
            "CDCNSSPConnector.fetch() is a stub. "
            "Implement against https://data.cdc.gov/resource/vutn-jzwm.json for a us_state fork."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
