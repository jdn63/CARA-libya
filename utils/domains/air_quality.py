"""
Air Quality Risk Domain

Scores ambient air quality risk using AQI or PM2.5/O3 concentration data.
Works with any connector that returns daily AQI or pollutant concentration readings:
  - US deployments: EPA AirNow (real-time + historical)
  - International deployments: OpenAQ (global, near-real-time)
  - Both: NOAA, WHO ambient air quality datasets

Scoring is based on the US EPA AQI breakpoints for PM2.5 and ozone, which are
also the basis for WHO air quality guidelines and therefore appropriate for
both US and international use.
"""

import logging
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)

AQI_BREAKPOINTS = [
    (0, 50, "Good"),
    (51, 100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]


class AirQualityDomain(BaseDomain):

    DOMAIN_ID = "air_quality"
    DOMAIN_KEY = "air_quality"
    DOMAIN_LABEL = "Air Quality Risk"
    DEFAULT_WEIGHT = 0.12

    def domain_info(self):
        return {
            "id": self.DOMAIN_ID,
            "label": self.DOMAIN_LABEL,
            "description": (
                "Scores ambient air quality risk using AQI or PM2.5/ozone concentration data. "
                "Compatible with US (EPA AirNow) and international (OpenAQ) data sources."
            ),
            "methodology": "Weighted composite: 50% AQI level, 30% unhealthy days, 20% sensitive population exposure.",
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
        result.setdefault("dominant_factor", "Air quality exposure")
        return result

    def compute(self, jurisdiction_id: str, data_cache: dict) -> dict:
        try:
            aq_data = data_cache.get("air_quality", {})
            if not aq_data:
                aq_data = self._fetch(jurisdiction_id)

            aqi_score = self._score_aqi(aq_data)
            unhealthy_days_score = self._score_unhealthy_days(aq_data)
            sensitive_pop_score = self._score_sensitive_population(aq_data)

            score = min(1.0, max(0.0,
                0.50 * aqi_score +
                0.30 * unhealthy_days_score +
                0.20 * sensitive_pop_score
            ))

            return {
                "domain_key": self.DOMAIN_KEY,
                "score": round(score, 4),
                "weight": self._weight(),
                "components": {
                    "aqi_level": round(aqi_score, 4),
                    "unhealthy_days": round(unhealthy_days_score, 4),
                    "sensitive_population_exposure": round(sensitive_pop_score, 4),
                },
                "data_sources": aq_data.get("sources", []),
                "metadata": {
                    "current_aqi": aq_data.get("current_aqi"),
                    "pm25_annual_mean": aq_data.get("pm25_annual_mean_ug_m3"),
                    "ozone_4th_max_ppb": aq_data.get("ozone_4th_max_8hr_ppb"),
                    "unhealthy_days_annual": aq_data.get("unhealthy_days_annual", 0),
                    "monitoring_stations": aq_data.get("station_count", 0),
                },
                "action_plan_items": self._action_items(score, aq_data),
            }
        except Exception as exc:
            logger.error("AirQualityDomain.compute failed for %s: %s", jurisdiction_id, exc)
            return self._error_result()

    def _fetch(self, jurisdiction_id: str) -> dict:
        return {"sources": []}

    def _score_aqi(self, data: dict) -> float:
        aqi = data.get("current_aqi") or data.get("aqi_annual_median", 0)
        if aqi is None:
            return 0.0
        aqi = float(aqi)
        if aqi <= 50:
            return 0.05
        if aqi <= 100:
            return 0.20
        if aqi <= 150:
            return 0.45
        if aqi <= 200:
            return 0.70
        if aqi <= 300:
            return 0.90
        return 1.00

    def _score_unhealthy_days(self, data: dict) -> float:
        days = data.get("unhealthy_days_annual", 0)
        if days == 0:
            return 0.0
        if days <= 5:
            return 0.15
        if days <= 15:
            return 0.35
        if days <= 30:
            return 0.60
        if days <= 60:
            return 0.80
        return 1.00

    def _score_sensitive_population(self, data: dict) -> float:
        copd_pct = data.get("copd_prevalence_pct", 6.0)
        asthma_pct = data.get("asthma_prevalence_pct", 9.0)
        elderly_pct = data.get("population_over65_pct", 15.0)
        raw = (copd_pct / 12.0 * 0.40 + asthma_pct / 18.0 * 0.40 + elderly_pct / 25.0 * 0.20)
        return min(1.0, raw)

    def _action_items(self, score: float, data: dict) -> list:
        items = []
        aqi = data.get("current_aqi", 0) or 0
        if aqi > 150:
            items.append({
                "priority": "critical",
                "capability": "air_quality",
                "action": "Issue public health advisory for current AQI conditions; activate cooling/clean air center network.",
                "timeline": "Immediate",
                "metric": "Population reached by advisory within 2 hours of AQI threshold breach",
            })
        if score >= 0.5:
            items.append({
                "priority": "high",
                "capability": "air_quality",
                "action": "Enroll high-risk patients (COPD, asthma, cardiac) in AirNow/AQI automated alert system.",
                "timeline": "30 days",
                "metric": "Percentage of high-risk patients enrolled in air quality alert registry",
            })
        items.append({
            "priority": "medium" if score >= 0.4 else "low",
            "capability": "air_quality",
            "action": "Expand air quality monitoring station coverage in underserved areas and maintain current station calibration.",
            "timeline": "90 days",
            "metric": "Monitoring station coverage area per 100,000 population",
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
