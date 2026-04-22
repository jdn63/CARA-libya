"""
Connector registry for CARA template.

Maps configuration profile names and jurisdiction settings to the appropriate
connector instances. The risk engine asks the registry for connectors by
domain name; the registry returns the right implementation based on profile.

To add a new connector:
1. Implement BaseConnector in utils/connectors/
2. Register it here by adding an entry to CONNECTOR_MAP
3. Reference it in the appropriate config/profiles/*.yaml under connectors:
"""

import logging
import os
from typing import Any, Dict, Optional, Type
import yaml

from utils.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


def load_jurisdiction_config() -> Dict[str, Any]:
    config_path = os.path.join('config', 'jurisdiction.yaml')
    if not os.path.exists(config_path):
        logger.warning("jurisdiction.yaml not found. Using defaults.")
        return {}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


class ConnectorRegistry:
    """
    Instantiates and caches connector objects based on the active profile.

    Connectors are instantiated lazily on first access and cached for the
    lifetime of the registry (one per application startup).
    """

    def __init__(self, profile: str, jurisdiction_config: Optional[Dict[str, Any]] = None):
        self.profile = profile
        self.config = jurisdiction_config or load_jurisdiction_config()
        self._connectors: Dict[str, BaseConnector] = {}

    def get(self, connector_name: str) -> Optional[BaseConnector]:
        """
        Return the connector instance for the given name, or None if unavailable.
        Connector names match the keys in config/profiles/*.yaml under connectors:.
        """
        if connector_name in self._connectors:
            return self._connectors[connector_name]

        connector = self._build_connector(connector_name)
        if connector:
            self._connectors[connector_name] = connector
        return connector

    def get_all_available(self) -> Dict[str, BaseConnector]:
        """Return all connectors that are currently available."""
        available = {}
        for name in self._get_connector_names():
            c = self.get(name)
            if c and c.is_available():
                available[name] = c
        return available

    def _get_connector_names(self) -> list:
        profile_path = os.path.join('config', 'profiles', f'{self.profile}.yaml')
        if not os.path.exists(profile_path):
            return []
        with open(profile_path, 'r') as f:
            profile_data = yaml.safe_load(f) or {}
        return list(profile_data.get('connectors', {}).values())

    def _build_connector(self, name: str) -> Optional[BaseConnector]:
        jconfig = self.config.get('jurisdiction', {})
        country_code = jconfig.get('country_code', 'XX')
        iso3 = jconfig.get('iso3166_1', country_code)
        population = jconfig.get('population', 1_000_000)

        try:
            if name == 'who_gho':
                from utils.connectors.worldwide.who_gho_connector import WHOGHOConnector
                return WHOGHOConnector(country_code=country_code)

            elif name == 'gadm':
                from utils.connectors.worldwide.gadm_connector import GADMConnector
                level = jconfig.get('geographic', {}).get('gadm_level', 2)
                return GADMConnector(country_code=country_code, level=level)

            elif name == 'em_dat':
                from utils.connectors.worldwide.em_dat_connector import EMDATConnector
                return EMDATConnector(country=jconfig.get('name', ''), iso2=country_code)

            elif name == 'worldbank':
                from utils.connectors.worldwide.worldbank_connector import WorldBankConnector
                return WorldBankConnector(country_code=country_code)

            elif name == 'acled':
                from utils.connectors.worldwide.acled_connector import ACLEDConnector
                acled_cfg = jconfig.get('acled_config', {})
                country_name = acled_cfg.get('country', jconfig.get('name', country_code))
                return ACLEDConnector(country=country_name)

            elif name == 'idmc':
                from utils.connectors.worldwide.idmc_connector import IDMCConnector
                idmc_cfg = jconfig.get('idmc_config', {})
                return IDMCConnector(iso3=idmc_cfg.get('iso3', iso3))

            elif name == 'openaq':
                from utils.connectors.worldwide.openaq_connector import OpenAQConnector
                return OpenAQConnector(country_code=country_code)

            elif name == 'noaa_gsod':
                from utils.connectors.worldwide.noaa_gsod_connector import NOAAGSODConnector
                return NOAAGSODConnector(country_code=country_code)

            elif name == 'airnow':
                try:
                    from utils.connectors.us.airnow_connector import AirNowConnector
                    return AirNowConnector()
                except ImportError:
                    logger.warning("US AirNow connector not available — add to utils/connectors/us/")

            elif name == 'nws':
                try:
                    from utils.connectors.us.nws_connector import NWSConnector
                    return NWSConnector()
                except ImportError:
                    logger.warning("US NWS connector not available")

            elif name == 'open_fema':
                try:
                    from utils.connectors.us.open_fema_connector import OpenFEMAConnector
                    return OpenFEMAConnector()
                except ImportError:
                    logger.warning("US OpenFEMA connector not available")

            elif name == 'cdc_nssp':
                try:
                    from utils.connectors.us.cdc_nssp_connector import CDCNSSPConnector
                    return CDCNSSPConnector()
                except ImportError:
                    logger.warning("US CDC NSSP connector not available")

            else:
                logger.debug(f"No connector implementation found for: {name}")

        except Exception as e:
            logger.error(f"Failed to instantiate connector '{name}': {e}")

        return None
