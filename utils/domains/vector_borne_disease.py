"""
Vector-Borne Disease Risk Domain

Scores risk from vector-borne diseases (Lyme disease, West Nile Virus, Dengue,
Malaria, Zika, Chikungunya, Rift Valley Fever, etc.) using surveillance data
and climate-adjusted range expansion projections.

Profile-aware:
  - US state profile: uses WI DHS EPHT county incidence data (or equivalent
    state epidemiological surveillance CSV exports)
  - International profile: uses WHO GHO disease incidence estimates and
    World Bank climate indicators

Scoring uses the EVR framework (Exposure-Vulnerability-Resilience) with a
climate adjustment factor reflecting projected habitat range expansion.
"""

import logging
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)

DISEASE_CONFIG = {
    "lyme": {
        "vector": "Ixodes tick",
        "climate_sensitive": True,
        "high_incidence_threshold_per_100k": 50.0,
    },
    "west_nile": {
        "vector": "Culex mosquito",
        "climate_sensitive": True,
        "high_incidence_threshold_per_100k": 1.0,
    },
    "dengue": {
        "vector": "Aedes mosquito",
        "climate_sensitive": True,
        "high_incidence_threshold_per_100k": 10.0,
    },
    "malaria": {
        "vector": "Anopheles mosquito",
        "climate_sensitive": True,
        "high_incidence_threshold_per_100k": 50.0,
    },
}


class VectorBorneDiseaseDomain(BaseDomain):

    DOMAIN_ID = "vector_borne_disease"
    DOMAIN_KEY = "vector_borne_disease"
    DOMAIN_LABEL = "Vector-Borne Disease Risk"
    DEFAULT_WEIGHT = 0.07

    def domain_info(self):
        return {
            "id": self.DOMAIN_ID,
            "label": self.DOMAIN_LABEL,
            "description": (
                "Scores risk from vector-borne diseases (Lyme, West Nile, Dengue, Malaria, etc.) "
                "using surveillance data and climate-adjusted range expansion projections."
            ),
            "methodology": "EVR composite: 40% incidence, 25% climate adjustment, 20% vulnerability, 15% resilience (inverted).",
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
        result.setdefault("dominant_factor", "Vector-borne disease incidence")
        return result

    def compute(self, jurisdiction_id: str, data_cache: dict) -> dict:
        try:
            vbd_data = data_cache.get("vector_borne_disease", {})
            if not vbd_data:
                vbd_data = self._fetch(jurisdiction_id)

            incidence_score = self._score_incidence(vbd_data)
            climate_score = self._score_climate_adjustment(vbd_data)
            vulnerability_score = self._score_vulnerability(vbd_data)
            resilience_score = self._score_resilience(vbd_data)

            score = min(1.0, max(0.0,
                0.40 * incidence_score +
                0.25 * climate_score +
                0.20 * vulnerability_score +
                0.15 * (1.0 - resilience_score)
            ))

            return {
                "domain_key": self.DOMAIN_KEY,
                "score": round(score, 4),
                "weight": self._weight(),
                "components": {
                    "current_incidence": round(incidence_score, 4),
                    "climate_range_expansion": round(climate_score, 4),
                    "population_vulnerability": round(vulnerability_score, 4),
                    "surveillance_resilience": round(resilience_score, 4),
                },
                "data_sources": vbd_data.get("sources", []),
                "metadata": {
                    "lyme_incidence_per_100k": vbd_data.get("lyme_rate_per_100k"),
                    "west_nile_incidence_per_100k": vbd_data.get("west_nile_rate_per_100k"),
                    "dengue_incidence_per_100k": vbd_data.get("dengue_rate_per_100k"),
                    "malaria_incidence_per_100k": vbd_data.get("malaria_rate_per_100k"),
                    "active_diseases": vbd_data.get("active_diseases", []),
                },
                "action_plan_items": self._action_items(score, vbd_data),
            }
        except Exception as exc:
            logger.error("VectorBorneDiseaseDomain.compute failed for %s: %s", jurisdiction_id, exc)
            return self._error_result()

    def _fetch(self, jurisdiction_id: str) -> dict:
        return {"sources": []}

    def _score_incidence(self, data: dict) -> float:
        scores = []
        lyme = data.get("lyme_rate_per_100k", 0)
        if lyme is not None:
            scores.append(min(1.0, float(lyme) / 100.0))
        wnv = data.get("west_nile_rate_per_100k", 0)
        if wnv is not None:
            scores.append(min(1.0, float(wnv) / 2.0))
        dengue = data.get("dengue_rate_per_100k", 0)
        if dengue is not None:
            scores.append(min(1.0, float(dengue) / 30.0))
        malaria = data.get("malaria_rate_per_100k", 0)
        if malaria is not None:
            scores.append(min(1.0, float(malaria) / 100.0))
        return max(scores) if scores else 0.0

    def _score_climate_adjustment(self, data: dict) -> float:
        warming_trend = data.get("warming_trend_c_per_decade", 0.2)
        habitat_expansion_pct = data.get("vector_habitat_expansion_pct", 5.0)
        warming_score = min(1.0, warming_trend / 0.5)
        expansion_score = min(1.0, habitat_expansion_pct / 30.0)
        return warming_score * 0.6 + expansion_score * 0.4

    def _score_vulnerability(self, data: dict) -> float:
        outdoor_recreation_pct = data.get("outdoor_recreation_participation_pct", 40.0)
        immunocompromised_pct = data.get("immunocompromised_pct", 3.0)
        forested_area_pct = data.get("forested_area_pct", 30.0)
        return min(1.0,
            min(1.0, outdoor_recreation_pct / 70.0) * 0.35 +
            min(1.0, immunocompromised_pct / 8.0) * 0.35 +
            min(1.0, forested_area_pct / 60.0) * 0.30
        )

    def _score_resilience(self, data: dict) -> float:
        surveillance_active = float(data.get("active_surveillance_programs", 0) > 0)
        vector_control_budget = min(1.0, data.get("vector_control_budget_per_capita", 0) / 10.0)
        provider_awareness = data.get("provider_vbd_training_rate", 0.5)
        return min(1.0, surveillance_active * 0.40 + vector_control_budget * 0.35 + provider_awareness * 0.25)

    def _action_items(self, score: float, data: dict) -> list:
        items = []
        lyme = data.get("lyme_rate_per_100k", 0) or 0
        wnv = data.get("west_nile_rate_per_100k", 0) or 0
        if float(lyme) > 30 or float(wnv) > 0.5:
            items.append({
                "priority": "high" if score >= 0.55 else "medium",
                "capability": "vector_borne_disease",
                "action": "Deploy enhanced tick and mosquito surveillance in high-risk zones; update provider guidance on clinical recognition and reporting.",
                "timeline": "30 days",
                "metric": "Number of active vector surveillance sites and percentage of providers completing annual VBD clinical update",
            })
        items.append({
            "priority": "medium",
            "capability": "vector_borne_disease",
            "action": "Issue annual community education materials on tick checks, personal protective measures, and residential mosquito control.",
            "timeline": "Pre-season (spring and summer)",
            "metric": "Community reach of VBD prevention messaging (unique impressions per 1,000 residents)",
        })
        if score >= 0.60:
            items.append({
                "priority": "high",
                "capability": "vector_borne_disease",
                "action": "Establish or activate a multi-jurisdictional VBD coordination protocol with state epidemiology and vector control agencies.",
                "timeline": "45 days",
                "metric": "Time from case report to vector control field response",
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
