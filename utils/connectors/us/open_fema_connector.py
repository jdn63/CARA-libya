"""
US connector stub — OpenFEMA APIs.

For a full US state deployment, implement this connector by adapting
utils/fema_data.py from the Wisconsin CARA repository.

OpenFEMA is keyless: https://www.fema.gov/about/reports-and-data/openfema
Endpoints used in Wisconsin:
  - Disaster Declarations Summaries v2
  - NFIP Redacted Claims v2
  - Hazard Mitigation Assistance Projects v4
"""

import logging
from typing import Any, Dict

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class OpenFEMAConnector(BaseConnector):
    """
    Stub connector for OpenFEMA (US deployments only).

    To implement:
    1. Copy utils/fema_data.py from the Wisconsin repo into this class.
    2. Filter requests by the jurisdiction's state code.
    3. Return data in the standard connector dict format.
    """

    name = "open_fema"
    description = "OpenFEMA APIs — disaster declarations, NFIP claims, HMA projects (US only, keyless)"
    requires_key = False
    refresh_interval_hours = 168

    def is_available(self) -> bool:
        return True

    def fetch(self, jurisdiction_id: str = "", **kwargs) -> Dict[str, Any]:
        logger.warning(
            "OpenFEMAConnector.fetch() is a stub. "
            "Implement by adapting utils/fema_data.py from the Wisconsin repo."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
