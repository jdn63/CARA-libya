"""
US connector stub — CDC NSSP Emergency Department Visits.

For a full US state deployment, implement this connector by adapting
utils/nssp_respiratory.py from the Wisconsin CARA repository.

Endpoint (keyless): https://data.cdc.gov/resource/vutn-jzwm.json
Updated every Friday. Provides percent of ED visits for Influenza, COVID-19, RSV.
"""

import logging
from typing import Any, Dict

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class CDCNSSPConnector(BaseConnector):
    """
    Stub connector for CDC NSSP respiratory ED visit surveillance (US only).

    To implement:
    1. Copy utils/nssp_respiratory.py from the Wisconsin repo into this class.
    2. Filter by the appropriate state/jurisdiction.
    3. Return data in the standard connector dict format.
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
            "Implement by adapting utils/nssp_respiratory.py from the Wisconsin repo."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
