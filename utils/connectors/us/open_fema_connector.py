"""
US connector stub — OpenFEMA APIs.

Placeholder adapter retained for any future fork that targets a US state
(profile == "us_state" in config/jurisdiction.yaml). The Libya deployment
never instantiates this class.

OpenFEMA is keyless: https://www.fema.gov/about/reports-and-data/openfema
Typical endpoints worth wiring up:
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
    Stub connector for OpenFEMA (us_state profile only).

    To implement for a US-state fork:
    1. Replace fetch() with real calls against the OpenFEMA endpoints listed
       in this module's docstring.
    2. Filter requests by the jurisdiction's state code.
    3. Return data in the standard BaseConnector dict format
       (see utils/connectors/base_connector.py).
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
            "Implement against https://www.fema.gov/about/reports-and-data/openfema for a us_state fork."
        )
        return {
            "available": False,
            "connector": self.name,
            "message": "Stub not implemented",
        }
