"""
Abstract base class for public health assessment frameworks.

Assessment frameworks determine how CARA maps risk scores to preparedness
capabilities and generates action plan items. Two frameworks are included:
  - CDC PHEP (Public Health Emergency Preparedness) — for US deployments
  - WHO IHR (International Health Regulations) — for international deployments

Custom frameworks can be added by extending BaseFramework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseFramework(ABC):
    """
    Abstract base for CARA assessment frameworks.

    A framework maps CARA domain scores to a structured set of preparedness
    capabilities or capacities, generating prioritized action plans.
    """

    FRAMEWORK_ID: str = ""
    FRAMEWORK_NAME: str = ""
    FRAMEWORK_URL: str = ""

    @abstractmethod
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """
        Returns the full list of capabilities or capacities defined by this framework.

        Each entry must include:
            - 'id': str — machine-readable identifier
            - 'label': str — human-readable name
            - 'description': str — what this capability covers
            - 'domain_links': list[str] — CARA domain IDs most relevant to this capability
        """

    @abstractmethod
    def map_to_action_plan(
        self,
        domain_scores: Dict[str, float],
        jurisdiction_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Maps domain risk scores to prioritized action plan items.

        Args:
            domain_scores: Dict of domain_id -> score [0,1]
            jurisdiction_config: Jurisdiction configuration dict

        Returns:
            List of action items, each with:
                - 'capability': str — capability ID this item addresses
                - 'priority': str — 'critical', 'high', 'medium', 'low'
                - 'action': str — specific recommended action
                - 'domains': list[str] — relevant domain IDs
                - 'timeframe': str — 'immediate', '30_days', '90_days', 'ongoing'
        """

    @abstractmethod
    def get_capability_score(
        self,
        capability_id: str,
        domain_scores: Dict[str, float],
    ) -> float:
        """
        Returns a [0,1] capability maturity estimate based on domain scores.
        Used to generate the spider/radar chart on the dashboard.
        """

    def framework_info(self) -> Dict[str, str]:
        return {
            'id': self.FRAMEWORK_ID,
            'name': self.FRAMEWORK_NAME,
            'url': self.FRAMEWORK_URL,
        }
