"""
INFORM Pillar 3: Lack of Coping Capacity — Libya CARA

Scores the Lack of Coping Capacity pillar [0, 1] from five indicators.
A high score means LOW coping capacity (more risk); each positive indicator
is INVERTED so that the pillar behaves consistently with the INFORM formula.

Indicators:
  1. response_time_gap        — Lack of timely emergency response (ambulance, EM)
  2. data_availability_gap    — Lack of historical disaster data / interoperability
  3. community_support_gap    — Absence of NGOs, volunteers, community organizations
  4. healthcare_access_gap    — Lack of accessible health facilities and services
  5. poverty_vulnerability    — High poverty rate → low capacity to recover

Equal weights (0.20 each) per workshop consensus (April 2026).

Alignment with Sendai Framework:
  Priority 2 (Governance):    → All indicators (institutional capacity)
  Priority 3 (Investment):    → response_time_gap, healthcare_access_gap
  Priority 4 (Preparedness):  → response_time_gap, data_availability_gap

Data sources:
  - WHO GHO:    Healthcare density, health system coverage
  - World Bank: Poverty headcount, GDP per capita, healthcare expenditure
  - IDMC/IOM:   Displacement-adjusted service access
  - COI Libya:  Response time, NGO presence, data availability (file upload)
  - NCDC Libya: Health system capacity (file upload)

Missing data policy: regional average proxy, documented in output.
"""

import logging
from typing import Any, Dict
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)

INDICATOR_WEIGHTS = {
    'response_time_gap':       0.20,
    'data_availability_gap':   0.20,
    'community_support_gap':   0.20,
    'healthcare_access_gap':   0.20,
    'poverty_vulnerability':   0.20,
}


class CopingCapacityDomain(BaseDomain):
    """
    INFORM Lack of Coping Capacity pillar for Libya.

    High score = low coping capacity = more risk.
    All positive indicators (e.g., healthcare access) are inverted.
    """

    def calculate(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
        profile: str = 'libya',
    ) -> Dict[str, Any]:
        """Compute the Lack of Coping Capacity pillar score."""
        scores = {}
        proxy_flags = {}

        scores['response_time_gap'], proxy_flags['response_time_gap'] = \
            self._response_time_gap(connector_data)

        scores['data_availability_gap'], proxy_flags['data_availability_gap'] = \
            self._data_availability_gap(connector_data)

        scores['community_support_gap'], proxy_flags['community_support_gap'] = \
            self._community_support_gap(connector_data)

        scores['healthcare_access_gap'], proxy_flags['healthcare_access_gap'] = \
            self._healthcare_access_gap(connector_data)

        scores['poverty_vulnerability'], proxy_flags['poverty_vulnerability'] = \
            self._poverty_vulnerability(connector_data)

        pillar_score, data_coverage = self._weighted_average(scores, INDICATOR_WEIGHTS)

        return {
            'score': pillar_score,
            'pillar': 'coping_capacity',
            'label_ar': 'ضعف القدرة على المواجهة',
            'label_en': 'Lack of Coping Capacity',
            'indicators': {
                k: {
                    'score': scores[k],
                    'weight': INDICATOR_WEIGHTS[k],
                    'proxy_used': proxy_flags.get(k, False),
                }
                for k in scores
            },
            'data_coverage': data_coverage,
            'available': data_coverage > 0,
        }

    def _response_time_gap(self, data: Dict[str, Any]):
        """
        Score the gap in emergency response capability.
        High score = slow/absent emergency response.
        """
        coi = data.get('coi_libya', {})
        worldbank = data.get('worldbank', {})

        avg_response_min = coi.get('avg_ambulance_response_minutes', None)
        if avg_response_min is not None:
            score = min(1.0, float(avg_response_min) / 60.0)
            return round(score, 4), False

        health_infra = worldbank.get('hospital_beds_per_1000', None)
        if health_infra is not None:
            gap = 1.0 - min(1.0, float(health_infra) / 5.0)
            return round(gap, 4), False

        return 0.60, True

    def _data_availability_gap(self, data: Dict[str, Any]):
        """
        Score the lack of disaster/health data availability and interoperability.
        This is the meta-indicator: the tool itself measures data gaps.
        High score = large data gap.
        """
        total_indicators = 20
        missing_count = sum(
            1 for v in data.values()
            if isinstance(v, dict) and not v.get('available', True)
        )
        available_count = sum(
            1 for v in data.values()
            if isinstance(v, dict) and v.get('available', False)
        )

        coi = data.get('coi_libya', {})
        data_interop = coi.get('data_interoperability_score', None)
        if data_interop is not None:
            gap = 1.0 - max(0.0, min(1.0, float(data_interop)))
            return round(gap, 4), False

        if available_count + missing_count > 0:
            gap = missing_count / (available_count + missing_count)
            return round(gap, 4), False

        return 0.70, True

    def _community_support_gap(self, data: Dict[str, Any]):
        """
        Score the absence of community support systems (NGOs, volunteers).
        High score = weak community support networks.
        """
        coi = data.get('coi_libya', {})
        worldbank = data.get('worldbank', {})

        ngo_presence = coi.get('ngo_presence_score', None)
        if ngo_presence is not None:
            gap = 1.0 - max(0.0, min(1.0, float(ngo_presence)))
            return round(gap, 4), False

        civil_society = worldbank.get('civil_society_index', None)
        if civil_society is not None:
            gap = 1.0 - max(0.0, min(1.0, float(civil_society)))
            return round(gap, 4), False

        return 0.55, True

    def _healthcare_access_gap(self, data: Dict[str, Any]):
        """
        Score the lack of accessible healthcare.
        High score = poor healthcare access (distance, scarcity, quality).
        """
        who = data.get('who_gho', {})
        worldbank = data.get('worldbank', {})

        uchi = who.get('universal_health_coverage_index', None)
        if uchi is not None:
            gap = 1.0 - max(0.0, min(1.0, float(uchi) / 100.0))
            return round(gap, 4), False

        health_exp_pct = worldbank.get('health_expenditure_pct_gdp', None)
        beds = who.get('hospital_beds_per_1000', None)

        scores_raw = []
        if health_exp_pct is not None:
            gap = 1.0 - min(1.0, float(health_exp_pct) / 10.0)
            scores_raw.append(gap)
        if beds is not None:
            gap = 1.0 - min(1.0, float(beds) / 5.0)
            scores_raw.append(gap)

        if scores_raw:
            score = sum(scores_raw) / len(scores_raw)
            return round(score, 4), False

        return 0.50, True

    def _poverty_vulnerability(self, data: Dict[str, Any]):
        """
        Score poverty rate as a coping capacity gap.
        High poverty = low capacity to absorb and recover from shocks.
        """
        worldbank = data.get('worldbank', {})

        poverty_headcount = worldbank.get('poverty_headcount_ratio', None)
        if poverty_headcount is not None:
            score = min(1.0, float(poverty_headcount) / 100.0)
            return round(score, 4), False

        gni_per_capita = worldbank.get('gni_per_capita', None)
        if gni_per_capita is not None:
            gap = 1.0 - min(1.0, float(gni_per_capita) / 15000.0)
            return round(gap, 4), False

        return 0.45, True

    def _weighted_average(self, scores: Dict[str, float], weights: Dict[str, float]):
        """Compute weighted average. Returns (score, data_coverage)."""
        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            val = scores.get(key)
            if val is not None:
                total += weight * float(val)
                weight_sum += weight
        if weight_sum == 0:
            return 0.0, 0.0
        coverage = weight_sum / sum(weights.values()) if weights else 0.0
        return round(min(1.0, total / weight_sum * sum(weights.values())), 4), round(coverage, 4)
