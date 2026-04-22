"""
Natural Hazards Risk Domain

Calculates exposure-vulnerability-resilience scores for natural hazard risk.
Works with any data source that provides disaster event counts and impact metrics:
  - US deployments: FEMA NRI, NOAA Storm Events, OpenFEMA declarations
  - International deployments: EM-DAT, ReliefWeb

Pluggable scoring: connector data is normalized before scoring so the formula
runs identically regardless of the upstream data source.
"""

import logging
from typing import Any

from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)


class NaturalHazardsDomain(BaseDomain):
    """
    EVR-framework natural hazard risk domain.

    Exposure: event frequency + magnitude relative to jurisdiction peers
    Vulnerability: population density, housing age, infrastructure quality
    Resilience: insurance/NFIP coverage, mitigation grants, declaration history
    Health Impact: excess mortality, displacement, health-facility disruption
    """

    DOMAIN_ID = "natural_hazards"
    DOMAIN_KEY = "natural_hazards"
    DOMAIN_LABEL = "Natural Hazards Risk"
    DEFAULT_WEIGHT = 0.28

    HAZARD_TYPES = [
        "flood", "tornado", "severe_storm", "wildfire", "earthquake",
        "hurricane", "ice_storm", "drought", "landslide", "tsunami",
    ]

    DEFAULT_HAZARD_WEIGHTS = {
        "flood": 0.25,
        "tornado": 0.20,
        "severe_storm": 0.20,
        "wildfire": 0.15,
        "earthquake": 0.10,
        "other": 0.10,
    }

    def __init__(self, weights=None):
        super().__init__(weights)
        self.hazard_weights = self.DEFAULT_HAZARD_WEIGHTS.copy()

    def domain_info(self):
        return {
            "id": self.DOMAIN_ID,
            "label": self.DOMAIN_LABEL,
            "description": (
                "Scores risk from natural hazards using an Exposure-Vulnerability-Resilience "
                "framework. Compatible with US (FEMA/NOAA) and international (EM-DAT/ReliefWeb) "
                "data sources."
            ),
            "methodology": "EVR composite: 40% exposure, 30% vulnerability, 20% resilience (inverted), 10% health impact.",
            "applicable_profiles": ["us_state", "international"],
        }

    def calculate(self, connector_data, jurisdiction_config, profile="international"):
        jid = jurisdiction_config.get("jurisdiction", {}).get("short_name", "XX")
        merged = {}
        for v in connector_data.values():
            if isinstance(v, dict) and v.get("available", True):
                merged.update({k: val for k, val in v.items() if k != "available"})
        data_cache = {self.DOMAIN_KEY: merged}
        result = self.compute(jurisdiction_id=jid, data_cache=data_cache)
        result.setdefault("available", result.get("score") is not None)
        result.setdefault("confidence", 0.5 if result.get("available") else 0.0)
        result.setdefault("dominant_factor", "Natural hazard exposure")
        return result

    def compute(self, jurisdiction_id: str, data_cache: dict) -> dict:
        """Return scored result dict with domain_key, score, components, metadata."""
        try:
            hazard_data = data_cache.get("natural_hazards", {})
            if not hazard_data:
                hazard_data = self._fetch(jurisdiction_id)

            exposure = self._score_exposure(hazard_data)
            vulnerability = self._score_vulnerability(hazard_data)
            resilience = self._score_resilience(hazard_data)
            health_impact = self._score_health_impact(hazard_data)

            raw = (
                0.40 * exposure +
                0.30 * vulnerability +
                0.20 * (1.0 - resilience) +
                0.10 * health_impact
            )
            score = min(1.0, max(0.0, raw))

            return {
                "domain_key": self.DOMAIN_KEY,
                "score": round(score, 4),
                "weight": self._weight(),
                "components": {
                    "exposure": round(exposure, 4),
                    "vulnerability": round(vulnerability, 4),
                    "resilience": round(resilience, 4),
                    "health_impact": round(health_impact, 4),
                },
                "data_sources": hazard_data.get("sources", []),
                "metadata": {
                    "event_count": hazard_data.get("event_count", 0),
                    "years_analyzed": hazard_data.get("years_analyzed", 0),
                    "declaration_count": hazard_data.get("declaration_count", 0),
                },
                "action_plan_items": self._action_items(score),
            }
        except Exception as exc:
            logger.error("NaturalHazardsDomain.compute failed for %s: %s", jurisdiction_id, exc)
            return self._error_result()

    def _fetch(self, jurisdiction_id: str) -> dict:
        return {"sources": []}

    def _score_exposure(self, data: dict) -> float:
        event_count = data.get("event_count", 0)
        population = max(data.get("population", 1), 1)
        events_per_100k = (event_count / population) * 100_000
        if events_per_100k >= 50:
            return 1.0
        if events_per_100k >= 20:
            return 0.75
        if events_per_100k >= 10:
            return 0.50
        if events_per_100k >= 5:
            return 0.25
        return 0.10

    def _score_vulnerability(self, data: dict) -> float:
        svi = data.get("svi_percentile", 0.5)
        housing_age_pct = data.get("housing_pre1980_pct", 0.3)
        pop_density_score = min(1.0, data.get("pop_density_km2", 50) / 500)
        return min(1.0, (svi * 0.5 + housing_age_pct * 0.3 + pop_density_score * 0.2))

    def _score_resilience(self, data: dict) -> float:
        mitigation_score = min(1.0, data.get("mitigation_grant_dollars_per_capita", 0) / 200)
        insurance_coverage = data.get("insurance_coverage_rate", 0.5)
        return min(1.0, (insurance_coverage * 0.6 + mitigation_score * 0.4))

    def _score_health_impact(self, data: dict) -> float:
        deaths_per_100k = data.get("storm_deaths_per_100k_annual", 0)
        if deaths_per_100k >= 2.0:
            return 1.0
        if deaths_per_100k >= 1.0:
            return 0.75
        if deaths_per_100k >= 0.5:
            return 0.50
        if deaths_per_100k >= 0.1:
            return 0.25
        return 0.05

    def _action_items(self, score: float) -> list:
        items = [
            {
                "priority": "high" if score >= 0.65 else "medium",
                "capability": "natural_hazards",
                "action": "Develop or update the jurisdiction's Multi-Hazard Mitigation Plan (MHMP).",
                "timeline": "30-90 days",
                "metric": "MHMP approval date and coverage of top three hazard types",
            },
            {
                "priority": "medium",
                "capability": "natural_hazards",
                "action": "Conduct a shelter inventory and map gaps relative to projected displacement zones.",
                "timeline": "60 days",
                "metric": "Shelter capacity per 1,000 population in highest-exposure census tracts",
            },
            {
                "priority": "medium" if score >= 0.5 else "low",
                "capability": "natural_hazards",
                "action": "Establish or verify automatic FEMA/emergency declaration notification routing to public health EOC.",
                "timeline": "14 days",
                "metric": "Time from declaration to public health activation",
            },
        ]
        if score >= 0.75:
            items.insert(0, {
                "priority": "critical",
                "capability": "natural_hazards",
                "action": "Activate enhanced hazard monitoring and pre-position supplies in highest-risk zones immediately.",
                "timeline": "Immediate (72 hours)",
                "metric": "Pre-positioned cache coverage of top-quartile exposure census tracts",
            })
        return items

    def _error_result(self) -> dict:
        return {
            "domain_key": self.DOMAIN_KEY,
            "score": None,
            "weight": self._weight(),
            "error": "Data unavailable",
            "components": {},
            "data_sources": [],
            "action_plan_items": [],
        }

    def _weight(self) -> float:
        return self.DEFAULT_WEIGHT
