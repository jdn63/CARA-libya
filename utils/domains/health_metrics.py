"""
Health Metrics Risk Domain

Scores population health baseline risk using available health surveillance data.
Connector-agnostic: accepts data from CDC PLACES, County Health Rankings,
Wisconsin DHS, WHO GHO, World Bank Health Indicators, or any source
that provides the expected metric keys.

Metric groups:
  - Chronic disease burden (COPD, diabetes, cardiovascular)
  - Vaccination coverage (influenza, routine immunizations)
  - Healthcare access (primary care density, insurance coverage)
  - Social determinants (poverty rate, food insecurity)
"""

import logging
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)


class HealthMetricsDomain(BaseDomain):

    DOMAIN_ID = "health_metrics"
    DOMAIN_KEY = "health_metrics"
    DOMAIN_LABEL = "Health Metrics Risk"
    DEFAULT_WEIGHT = 0.17

    def domain_info(self):
        return {
            "id": self.DOMAIN_ID,
            "label": self.DOMAIN_LABEL,
            "description": (
                "Scores population health baseline risk using available health surveillance data. "
                "Compatible with CDC PLACES, County Health Rankings, WHO GHO, World Bank, and local ministry data."
            ),
            "methodology": "Weighted composite: 35% chronic burden, 25% vaccination gap, 25% healthcare access gap, 15% social determinants.",
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
        result.setdefault("dominant_factor", "Population health baseline")
        return result

    def compute(self, jurisdiction_id: str, data_cache: dict) -> dict:
        try:
            hm_data = data_cache.get("health_metrics", {})
            if not hm_data:
                hm_data = self._fetch(jurisdiction_id)

            chronic_score = self._score_chronic_burden(hm_data)
            vaccination_score = self._score_vaccination(hm_data)
            access_score = self._score_healthcare_access(hm_data)
            sdoh_score = self._score_sdoh(hm_data)

            risk_score = (
                0.35 * chronic_score +
                0.25 * (1.0 - vaccination_score) +
                0.25 * (1.0 - access_score) +
                0.15 * sdoh_score
            )
            score = min(1.0, max(0.0, risk_score))

            return {
                "domain_key": self.DOMAIN_KEY,
                "score": round(score, 4),
                "weight": self._weight(),
                "components": {
                    "chronic_disease_burden": round(chronic_score, 4),
                    "vaccination_coverage": round(vaccination_score, 4),
                    "healthcare_access": round(access_score, 4),
                    "social_determinants": round(sdoh_score, 4),
                },
                "data_sources": hm_data.get("sources", []),
                "metadata": {
                    "copd_prevalence": hm_data.get("copd_prevalence_pct"),
                    "flu_vaccination_rate": hm_data.get("flu_vaccination_rate"),
                    "primary_care_per_100k": hm_data.get("primary_care_per_100k"),
                },
                "action_plan_items": self._action_items(score, hm_data),
            }
        except Exception as exc:
            logger.error("HealthMetricsDomain.compute failed for %s: %s", jurisdiction_id, exc)
            return self._error_result()

    def _fetch(self, jurisdiction_id: str) -> dict:
        return {"sources": []}

    def _score_chronic_burden(self, data: dict) -> float:
        copd = data.get("copd_prevalence_pct", 6.0)
        diabetes = data.get("diabetes_prevalence_pct", 10.0)
        cardiovascular = data.get("cardiovascular_prevalence_pct", 30.0)
        copd_score = min(1.0, copd / 12.0)
        diabetes_score = min(1.0, diabetes / 18.0)
        cardio_score = min(1.0, cardiovascular / 50.0)
        return copd_score * 0.40 + diabetes_score * 0.35 + cardio_score * 0.25

    def _score_vaccination(self, data: dict) -> float:
        flu = data.get("flu_vaccination_rate", 0.45)
        mmr = data.get("mmr_vaccination_rate", 0.90)
        routine = data.get("routine_immunization_coverage", 0.85)
        return min(1.0, (flu * 0.40 + mmr * 0.35 + routine * 0.25))

    def _score_healthcare_access(self, data: dict) -> float:
        pcp_per_100k = data.get("primary_care_per_100k", 70.0)
        insurance_rate = data.get("insurance_coverage_rate", 0.92)
        pcp_score = min(1.0, pcp_per_100k / 150.0)
        return min(1.0, (pcp_score * 0.5 + insurance_rate * 0.5))

    def _score_sdoh(self, data: dict) -> float:
        poverty_rate = data.get("poverty_rate", 0.12)
        food_insecurity = data.get("food_insecurity_rate", 0.12)
        return min(1.0, (poverty_rate * 0.5 + food_insecurity * 0.5))

    def _action_items(self, score: float, data: dict) -> list:
        items = []
        flu_rate = data.get("flu_vaccination_rate", 0.5)
        if flu_rate < 0.50:
            items.append({
                "priority": "high",
                "capability": "health_metrics",
                "action": "Launch targeted flu vaccination outreach in underserved census tracts; coordinate with pharmacies and FQHC partners.",
                "timeline": "30 days",
                "metric": "Flu vaccination rate increase of 5 percentage points within 60 days",
            })
        copd = data.get("copd_prevalence_pct", 6.0)
        if copd > 8.0:
            items.append({
                "priority": "medium",
                "capability": "health_metrics",
                "action": "Integrate COPD case registry with emergency alert system to ensure proactive outreach during air quality events.",
                "timeline": "45 days",
                "metric": "Percent of high-risk COPD patients registered in the emergency notification list",
            })
        pcp = data.get("primary_care_per_100k", 70)
        if pcp < 60:
            items.append({
                "priority": "high",
                "capability": "health_metrics",
                "action": "Identify and activate telehealth partnerships to supplement primary care access in shortage areas.",
                "timeline": "60 days",
                "metric": "Telehealth visit capacity per 1,000 residents in HPSA-designated zones",
            })
        if not items:
            items.append({
                "priority": "low",
                "capability": "health_metrics",
                "action": "Maintain annual review of chronic disease burden and vaccination coverage against state benchmarks.",
                "timeline": "Annual",
                "metric": "Year-over-year improvement in COPD prevalence and flu vaccination rate",
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
