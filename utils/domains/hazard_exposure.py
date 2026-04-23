"""
INFORM Pillar 1: Hazard & Exposure — Libya CARA

Aggregates four hazard sub-domains into a single Hazard & Exposure pillar score [0, 1]:
  - Infrastructure Hazard  (دams, electric grid, water/sewage)
  - Natural Hazard         (flooding, wildfire, extreme cold, sandstorms)
  - Epidemiological Hazard (infectious disease, vector-borne diseases)
  - Road Safety Hazard     (car accidents)

Each sub-domain is scored [0, 1] and combined with equal weights (0.25 each)
per the workshop consensus (April 2026). Weights are configurable in risk_weights.yaml.

Data sources:
  - WHO GHO:     disease burden, mortality
  - EM-DAT:      historical disaster counts and severity
  - OpenAQ:      air quality / dust (sandstorm proxy)
  - World Bank:  road fatality rates, infrastructure coverage
  - NCDC Libya:  local infectious disease and VBD surveillance (file upload)
  - Local upload: infrastructure-specific data

Missing data policy:
  When a sub-indicator is unavailable, a regional average proxy is used and
  flagged explicitly in the output. See config/jurisdiction.yaml for policy details.
"""

import logging
from typing import Any, Dict, Optional
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)

PILLAR_WEIGHTS = {
    'infrastructure_hazard': 0.25,
    'natural_hazard':        0.25,
    'epidemiological_hazard':0.25,
    'road_safety_hazard':    0.25,
}

INFRA_WEIGHTS = {
    'dam_safety':   0.333,
    'electric_grid':0.333,
    'water_sewage': 0.333,
}

NATURAL_WEIGHTS = {
    'flooding':     0.30,
    'wildfire':     0.20,
    'extreme_cold': 0.25,
    'sandstorm':    0.25,
}

EPID_WEIGHTS = {
    'infectious_disease': 0.60,
    'vector_borne':       0.40,
}


class HazardExposureDomain(BaseDomain):
    """
    INFORM Hazard & Exposure pillar for Libya.
    """

    def calculate(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
        profile: str = 'libya',
    ) -> Dict[str, Any]:
        """
        Compute the Hazard & Exposure pillar score.

        Returns a dict with 'score', 'sub_domains', 'proxy_flags', and 'available'.
        """
        sub_scores = {}
        proxy_flags = {}

        sub_scores['infrastructure_hazard'], proxy_flags['infrastructure_hazard'] = \
            self._infrastructure_hazard(connector_data)

        sub_scores['natural_hazard'], proxy_flags['natural_hazard'] = \
            self._natural_hazard(connector_data)

        sub_scores['epidemiological_hazard'], proxy_flags['epidemiological_hazard'] = \
            self._epidemiological_hazard(connector_data)

        sub_scores['road_safety_hazard'], proxy_flags['road_safety_hazard'] = \
            self._road_safety_hazard(connector_data)

        pillar_score, data_coverage = self._weighted_average(sub_scores, PILLAR_WEIGHTS)

        return {
            'score': pillar_score,
            'pillar': 'hazard_exposure',
            'label_ar': 'المخاطر والتعرض',
            'label_en': 'Hazard & Exposure',
            'sub_domains': {
                k: {
                    'score': sub_scores[k],
                    'weight': PILLAR_WEIGHTS[k],
                    'proxy_used': proxy_flags.get(k, False),
                }
                for k in sub_scores
            },
            'data_coverage': data_coverage,
            'available': data_coverage > 0,
        }

    def _infrastructure_hazard(self, data: Dict[str, Any]):
        """Score infrastructure hazard from dam, electric, and water/sewage indicators."""
        scores = {}
        proxy = {}

        em_dat = data.get('em_dat', {})
        worldbank = data.get('worldbank', {})
        local = data.get('coi_libya', {})

        scores['dam_safety'] = self._extract(em_dat, 'dam_failure_score',
                                              worldbank, 'dam_safety_index',
                                              default=None)
        if scores['dam_safety'] is None:
            scores['dam_safety'] = 0.4
            proxy['dam_safety'] = True

        scores['electric_grid'] = self._extract(worldbank, 'electricity_access_gap',
                                                  local, 'electric_grid_reliability',
                                                  default=None)
        if scores['electric_grid'] is None:
            scores['electric_grid'] = 0.5
            proxy['electric_grid'] = True

        scores['water_sewage'] = self._extract(worldbank, 'water_access_gap',
                                                data.get('who_gho', {}), 'water_sanitation_score',
                                                default=None)
        if scores['water_sewage'] is None:
            scores['water_sewage'] = 0.45
            proxy['water_sewage'] = True

        infra_score, _ = self._weighted_average(scores, INFRA_WEIGHTS)
        has_proxy = any(proxy.values())
        return infra_score, has_proxy

    def _natural_hazard(self, data: Dict[str, Any]):
        """Score natural hazards from EM-DAT, OpenAQ, and World Bank data."""
        scores = {}
        proxy = {}

        em_dat = data.get('em_dat', {})
        openaq = data.get('openaq', {})
        worldbank = data.get('worldbank', {})

        flood_count = em_dat.get('flood_events_10yr', None)
        if flood_count is not None:
            scores['flooding'] = min(1.0, float(flood_count) / 10.0)
        else:
            scores['flooding'] = 0.4
            proxy['flooding'] = True

        wildfire_count = em_dat.get('wildfire_events_10yr', None)
        if wildfire_count is not None:
            scores['wildfire'] = min(1.0, float(wildfire_count) / 5.0)
        else:
            scores['wildfire'] = 0.2
            proxy['wildfire'] = True

        cold_events = em_dat.get('extreme_cold_events_10yr', None)
        if cold_events is not None:
            scores['extreme_cold'] = min(1.0, float(cold_events) / 5.0)
        else:
            scores['extreme_cold'] = 0.3
            proxy['extreme_cold'] = True

        pm25 = openaq.get('pm25_annual_mean', None)
        if pm25 is not None:
            scores['sandstorm'] = min(1.0, float(pm25) / 100.0)
        else:
            scores['sandstorm'] = 0.6
            proxy['sandstorm'] = True

        nat_score, _ = self._weighted_average(scores, NATURAL_WEIGHTS)
        has_proxy = any(proxy.values())
        return nat_score, has_proxy

    def _epidemiological_hazard(self, data: Dict[str, Any]):
        """Score epidemiological hazard from WHO GHO and NCDC Libya data."""
        scores = {}
        proxy = {}

        who = data.get('who_gho', {})
        ncdc = data.get('ncdc_libya', {})

        mortality = who.get('under5_mortality_rate', None)
        disease_burden = ncdc.get('infectious_disease_rate', None)

        if disease_burden is not None:
            scores['infectious_disease'] = min(1.0, float(disease_burden) / 500.0)
        elif mortality is not None:
            scores['infectious_disease'] = min(1.0, float(mortality) / 50.0)
        else:
            scores['infectious_disease'] = 0.35
            proxy['infectious_disease'] = True

        vbd_rate = ncdc.get('vector_borne_rate', None) or who.get('malaria_incidence', None)
        if vbd_rate is not None:
            scores['vector_borne'] = min(1.0, float(vbd_rate) / 100.0)
        else:
            scores['vector_borne'] = 0.3
            proxy['vector_borne'] = True

        epid_score, _ = self._weighted_average(scores, EPID_WEIGHTS)
        has_proxy = any(proxy.values())
        return epid_score, has_proxy

    def _road_safety_hazard(self, data: Dict[str, Any]):
        """Score road safety hazard from WHO GHO and World Bank data."""
        who = data.get('who_gho', {})
        worldbank = data.get('worldbank', {})

        rtf = who.get('road_traffic_mortality_rate', None) or worldbank.get('road_fatality_rate', None)
        if rtf is not None:
            score = min(1.0, float(rtf) / 30.0)
            return score, False
        return 0.5, True

    def _extract(self, primary_data, primary_key, fallback_data, fallback_key, default=None):
        """Extract a numeric value from primary source, falling back to secondary."""
        val = primary_data.get(primary_key)
        if val is not None:
            try:
                return max(0.0, min(1.0, float(val)))
            except (ValueError, TypeError):
                pass
        val = fallback_data.get(fallback_key)
        if val is not None:
            try:
                return max(0.0, min(1.0, float(val)))
            except (ValueError, TypeError):
                pass
        return default

    def _weighted_average(self, scores: Dict[str, float], weights: Dict[str, float]):
        """Compute weighted average of scores. Returns (score, data_coverage)."""
        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            val = scores.get(key)
            if val is not None:
                total += weight * float(val)
                weight_sum += weight
        if weight_sum == 0:
            return 0.0, 0.0
        if weight_sum < sum(weights.values()) and weight_sum > 0:
            total = total / weight_sum * sum(weights.values())
        coverage = weight_sum / sum(weights.values()) if weights else 0.0
        return round(min(1.0, total), 4), round(coverage, 4)
