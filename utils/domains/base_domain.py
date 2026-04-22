"""
Abstract base class for CARA risk domains.

Every domain must implement calculate() and domain_info(). The risk engine
calls calculate() for each enabled domain and combines the returned scores
using the PHRAT quadratic mean formula.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseDomain(ABC):
    """
    Abstract base for all CARA risk domains.

    A domain encapsulates a coherent category of risk (e.g., natural hazards,
    conflict, health metrics). Each domain:
    - Accepts raw connector output as input
    - Applies domain-specific scoring logic
    - Returns a normalized score on [0, 1] plus a detailed breakdown

    Domains should be stateless and re-entrant: they should not store
    jurisdiction-specific state between calls.
    """

    DOMAIN_ID: str = ""
    DOMAIN_LABEL: str = ""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.sub_weights = weights or {}

    @abstractmethod
    def calculate(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
        profile: str = 'international',
    ) -> Dict[str, Any]:
        """
        Calculate the domain risk score.

        Args:
            connector_data: Dict of connector_name -> connector result dict.
                            Use connector_data.get('acled', {}) etc.
            jurisdiction_config: The jurisdiction's configuration dict.
            profile: 'us_state' or 'international' — controls which sub-components
                     and data sources are used.

        Returns:
            Dict with at minimum:
                - 'score': float [0, 1] — the domain risk score
                - 'confidence': float [0, 1] — data completeness confidence
                - 'components': dict — sub-scores and raw values
                - 'dominant_factor': str — human-readable description of top risk
                - 'data_sources': list[str] — data sources actually used
                - 'available': bool — whether real data was used

            On failure, return a safe default using _unavailable_result().
        """

    @abstractmethod
    def domain_info(self) -> Dict[str, str]:
        """
        Returns display metadata for the methodology and attribution pages.

        Must return:
            - 'id': str — machine-readable identifier (e.g. 'conflict_displacement')
            - 'label': str — human-readable name (e.g. 'Conflict and Displacement Risk')
            - 'description': str — paragraph-length description of what this domain measures
            - 'methodology': str — brief description of the scoring approach
            - 'applicable_profiles': list[str] — which profiles use this domain
        """

    def _unavailable_result(self, reason: str = "Data unavailable") -> Dict[str, Any]:
        """Standard safe-default result when data cannot be computed."""
        return {
            'score': 0.0,
            'confidence': 0.0,
            'components': {},
            'dominant_factor': reason,
            'data_sources': [],
            'available': False,
        }

    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Linear normalization to [0, 1]."""
        if max_val <= min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
