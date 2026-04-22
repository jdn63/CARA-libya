"""
Extreme Heat Risk Domain

Scores extreme heat risk using meteorological data and population vulnerability.
Works with any connector providing temperature, heat index, or climate summary data:
  - US deployments: NOAA/NWS heat alerts, NOAA climate normals
  - International deployments: NOAA GSOD (Global Surface Summary of Day), ERA5

The domain combines:
  - Climatological exposure (days above threshold, heat wave frequency)
  - Population vulnerability (elderly, outdoor workers, unhoused)
  - Infrastructure resilience (cooling centers, green space, tree canopy)
  - Health impact proxy (heat-related ED visits, mortality rate)
"""

import logging
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)


class ExtremeHeatDomain(BaseDomain):

    DOMAIN_ID = "extreme_heat"
    DOMAIN_KEY = "extreme_heat"
    DOMAIN_LABEL = "Extreme Heat Risk"
    DEFAULT_WEIGHT = 0.11

    HEAT_DAY_THRESHOLD_F = 90.0
    EXTREME_HEAT_DAY_THRESHOLD_F = 100.0

    def domain_info(self):
        return {
            "id": self.DOMAIN_ID,
            "label": self.DOMAIN_LABEL,
            "description": (
                "Scores extreme heat risk using meteorological data and population vulnerability. "
                "Compatible with US (NOAA/NWS) and international (NOAA GSOD, ERA5) data sources."
            ),
            "methodology": "Weighted composite: 35% climatological exposure, 30% vulnerability, 20% resilience (inverted), 15% health impact.",
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
        result.setdefault("dominant_factor", "Heat exposure")
        return result

    def compute(self, jurisdiction_id: str, data_cache: dict) -> dict:
        try:
            heat_data = data_cache.get("extreme_heat", {})
            if not heat_data:
                heat_data = self._fetch(jurisdiction_id)

            exposure = self._score_exposure(heat_data)
            vulnerability = self._score_vulnerability(heat_data)
            resilience = self._score_resilience(heat_data)
            health_impact = self._score_health_impact(heat_data)

            score = min(1.0, max(0.0,
                0.35 * exposure +
                0.30 * vulnerability +
                0.20 * (1.0 - resilience) +
                0.15 * health_impact
            ))

            return {
                "domain_key": self.DOMAIN_KEY,
                "score": round(score, 4),
                "weight": self._weight(),
                "components": {
                    "climatological_exposure": round(exposure, 4),
                    "population_vulnerability": round(vulnerability, 4),
                    "infrastructure_resilience": round(resilience, 4),
                    "health_impact": round(health_impact, 4),
                },
                "data_sources": heat_data.get("sources", []),
                "metadata": {
                    "days_above_90f_annual": heat_data.get("days_above_90f_annual"),
                    "days_above_100f_annual": heat_data.get("days_above_100f_annual"),
                    "heat_wave_events_5yr": heat_data.get("heat_wave_events_5yr"),
                    "cooling_centers_per_100k": heat_data.get("cooling_centers_per_100k"),
                    "climate_scenario": heat_data.get("climate_scenario", "current"),
                },
                "action_plan_items": self._action_items(score, heat_data),
            }
        except Exception as exc:
            logger.error("ExtremeHeatDomain.compute failed for %s: %s", jurisdiction_id, exc)
            return self._error_result()

    def _fetch(self, jurisdiction_id: str) -> dict:
        return {"sources": []}

    def _score_exposure(self, data: dict) -> float:
        days_90 = data.get("days_above_90f_annual", 10)
        days_100 = data.get("days_above_100f_annual", 0)
        heat_waves = data.get("heat_wave_events_5yr", 0)
        raw = (
            min(1.0, days_90 / 60.0) * 0.40 +
            min(1.0, days_100 / 15.0) * 0.35 +
            min(1.0, heat_waves / 10.0) * 0.25
        )
        return min(1.0, raw)

    def _score_vulnerability(self, data: dict) -> float:
        elderly_pct = data.get("population_over65_pct", 15.0)
        outdoor_workers_pct = data.get("outdoor_workers_pct", 8.0)
        poverty_rate = data.get("poverty_rate", 0.12)
        ac_access_rate = data.get("ac_access_rate", 0.85)
        raw = (
            min(1.0, elderly_pct / 25.0) * 0.35 +
            min(1.0, outdoor_workers_pct / 20.0) * 0.25 +
            poverty_rate * 0.25 +
            (1.0 - ac_access_rate) * 0.15
        )
        return min(1.0, raw)

    def _score_resilience(self, data: dict) -> float:
        cooling_centers = data.get("cooling_centers_per_100k", 1.0)
        green_space_pct = data.get("green_space_pct", 20.0)
        tree_canopy_pct = data.get("tree_canopy_pct", 25.0)
        cc_score = min(1.0, cooling_centers / 5.0)
        green_score = min(1.0, green_space_pct / 40.0)
        canopy_score = min(1.0, tree_canopy_pct / 40.0)
        return min(1.0, cc_score * 0.50 + green_score * 0.25 + canopy_score * 0.25)

    def _score_health_impact(self, data: dict) -> float:
        heat_ed_per_100k = data.get("heat_related_ed_per_100k", 0)
        heat_mortality_per_100k = data.get("heat_mortality_per_100k_annual", 0)
        ed_score = min(1.0, heat_ed_per_100k / 50.0)
        mort_score = min(1.0, heat_mortality_per_100k / 2.0)
        return max(ed_score * 0.6 + mort_score * 0.4, 0.0)

    def _action_items(self, score: float, data: dict) -> list:
        items = []
        cooling_centers = data.get("cooling_centers_per_100k", 1.0)
        if cooling_centers < 2.0 and score >= 0.4:
            items.append({
                "priority": "high" if score >= 0.65 else "medium",
                "capability": "extreme_heat",
                "action": "Audit and expand cooling center network; ensure 24-hour availability during heat emergencies.",
                "timeline": "30 days",
                "metric": "Cooling center capacity per 1,000 residents in highest-heat-vulnerability census tracts",
            })
        items.append({
            "priority": "medium",
            "capability": "extreme_heat",
            "action": "Establish a heat-vulnerable resident registry (elderly, outdoor workers, unhoused) for proactive wellness checks.",
            "timeline": "45 days",
            "metric": "Percentage of identified high-risk residents enrolled in wellness-check program",
        })
        if score >= 0.6:
            items.append({
                "priority": "high",
                "capability": "extreme_heat",
                "action": "Activate extreme heat emergency response plan trigger thresholds and coordinate cross-agency response protocol.",
                "timeline": "Immediate review",
                "metric": "Time from NWS excessive heat warning to public health activation",
            })
        items.append({
            "priority": "low",
            "capability": "extreme_heat",
            "action": "Partner with urban planning agencies to expand tree canopy and permeable surface coverage in heat-island zones.",
            "timeline": "1-3 years",
            "metric": "Increase tree canopy coverage by 5% in the three highest heat-index census tracts",
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
