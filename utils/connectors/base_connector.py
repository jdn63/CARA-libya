"""
Base connector interface for CARA data sources.

Every data connector — US-specific or global — must implement this interface.
The risk engine uses duck typing against these methods, so any class that
implements fetch(), is_available(), and source_info() is a valid connector.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for all CARA data connectors.

    Subclasses implement fetch() to return a standardized dict of metrics
    for a given jurisdiction. The connector is responsible for caching,
    error handling, and graceful degradation when data is unavailable.
    """

    CACHE_DURATION_SECONDS: int = 86400

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._cache: Dict[str, Any] = {}

    @abstractmethod
    def fetch(self, jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch data for a given jurisdiction.

        Args:
            jurisdiction_id: String identifier for the jurisdiction (e.g., county
                FIPS code, GADM GID, ISO3166 code, or a custom identifier).
            **kwargs: Additional connector-specific parameters.

        Returns:
            Dict containing the fetched metrics. Must include:
                - 'available': bool — whether real data was returned
                - 'source': str — human-readable data source name
                - 'last_updated': str or None — ISO 8601 date string
            All other keys are domain-specific.

        On failure, return a dict with available=False and a 'message' key
        explaining the failure. Never raise exceptions to the caller.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Returns True if this connector can currently serve data.
        Used by the scheduler to decide whether to run the fetch job.
        """

    @abstractmethod
    def source_info(self) -> Dict[str, str]:
        """
        Returns metadata about the data source for display in the methodology
        and data source attribution pages.

        Must return:
            - 'name': str — full data source name
            - 'url': str — canonical URL for the data source
            - 'update_frequency': str — e.g. 'weekly', 'annual', 'real-time'
            - 'license': str — data license (e.g. 'Public Domain', 'CC BY 4.0')
            - 'geographic_coverage': str — e.g. 'Global', 'United States'
            - 'notes': str — any important caveats
        """

    def _unavailable_response(self, message: str) -> Dict[str, Any]:
        """Standard response when data cannot be fetched."""
        return {
            'available': False,
            'message': message,
            'source': self.source_info().get('name', 'Unknown'),
            'last_updated': None,
        }

    def _wrap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap a successful fetch result with standard metadata."""
        info = self.source_info()
        return {
            'available': True,
            'source': info.get('name', 'Unknown'),
            'last_updated': data.pop('_last_updated', None),
            **data,
        }
