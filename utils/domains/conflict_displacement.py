"""
Conflict and Displacement Risk Domain.

Assesses public health risk from political violence, armed conflict,
and population displacement using ACLED event data and IDMC displacement figures.

This domain is enabled by the international profile and disabled by the US state
profile. It is relevant for any jurisdiction experiencing or adjacent to:
  - Armed conflict or political violence
  - Mass population displacement (internal or cross-border)
  - Civil unrest with public health implications

Risk components:
  1. Conflict Intensity (40%) — violent event frequency and fatality burden from ACLED
  2. Displacement Burden (35%) — IDP stock and new displacement flows from IDMC
  3. Health System Disruption (15%) — inferred from conflict intensity + displacement
  4. Trend Trajectory (10%) — whether conflict is escalating or de-escalating

EVR Framework:
  - Exposure: conflict events and displacement within the jurisdiction
  - Vulnerability: social vulnerability from World Bank (poverty, access to services)
  - Resilience: healthcare access, governance indicators

Scoring range: 0.0 (no conflict/displacement) to 1.0 (active high-intensity conflict
with massive displacement)
"""

import logging
import math
from typing import Any, Dict, List, Optional
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    'conflict_intensity': 0.40,
    'displacement_burden': 0.35,
    'health_system_disruption': 0.15,
    'trend_trajectory': 0.10,
}

TREND_SCORES = {
    'increasing': 1.0,
    'stable': 0.5,
    'decreasing': 0.1,
    'unknown': 0.5,
}


class ConflictDisplacementDomain(BaseDomain):
    """
    Conflict and Displacement Risk Domain.

    Integrates ACLED political violence data with IDMC displacement figures
    to produce a composite public health risk score.
    """

    DOMAIN_ID = 'conflict_displacement'
    DOMAIN_LABEL = 'Conflict and Displacement Risk'

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        super().__init__(weights or DEFAULT_WEIGHTS)

    def domain_info(self) -> Dict[str, Any]:
        return {
            'id': self.DOMAIN_ID,
            'label': self.DOMAIN_LABEL,
            'description': (
                'Measures public health risk from political violence, armed conflict, '
                'and population displacement. Active conflict disrupts healthcare delivery, '
                'causes injury and death, contaminates water and food supplies, and generates '
                'displacement that strains receiving community health systems. This domain '
                'uses the Exposure-Vulnerability-Resilience (EVR) framework.'
            ),
            'methodology': (
                'Conflict intensity is computed from ACLED violent event frequency and '
                'associated fatality burden. Displacement burden is computed from IDMC '
                'internally displaced person stock and new displacement flows normalized '
                'to jurisdiction population. Health system disruption is inferred from '
                'combined conflict and displacement pressure. Trend trajectory adjusts '
                'the score based on whether conflict is escalating, stable, or de-escalating. '
                'All components are combined using a weighted quadratic mean consistent '
                'with the PHRAT formula.'
            ),
            'applicable_profiles': ['international'],
            'data_sources': [
                {
                    'name': 'ACLED (Armed Conflict Location and Event Data Project)',
                    'url': 'https://acleddata.com',
                    'update_frequency': 'Weekly',
                    'notes': 'Requires free registration and ACLED_API_KEY env variable.',
                },
                {
                    'name': 'IDMC (Internal Displacement Monitoring Centre)',
                    'url': 'https://www.internal-displacement.org',
                    'update_frequency': 'Annual with mid-year updates',
                    'notes': 'No API key required for public data.',
                },
                {
                    'name': 'World Bank Open Data (vulnerability adjustment)',
                    'url': 'https://data.worldbank.org',
                    'update_frequency': 'Annual',
                    'notes': 'No API key required.',
                },
            ],
        }

    def calculate(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
        profile: str = 'international',
    ) -> Dict[str, Any]:
        if profile == 'us_state':
            return self._unavailable_result(
                "Conflict/displacement domain not applicable for US state profile"
            )

        acled = connector_data.get('acled', {})
        idmc = connector_data.get('idmc', {})
        worldbank = connector_data.get('worldbank', {})
        population = jurisdiction_config.get('population', 1_000_000) or 1_000_000

        conflict_score, conflict_components = self._score_conflict_intensity(acled)
        displacement_score, displacement_components = self._score_displacement(idmc, population)
        disruption_score = self._score_health_disruption(conflict_score, displacement_score)
        trend_score = self._score_trend(acled)

        vulnerability_adj = worldbank.get('vulnerability_index', 0.5) if worldbank.get('available') else 0.5

        raw_score = (
            conflict_score * self.sub_weights.get('conflict_intensity', 0.40) +
            displacement_score * self.sub_weights.get('displacement_burden', 0.35) +
            disruption_score * self.sub_weights.get('health_system_disruption', 0.15) +
            trend_score * self.sub_weights.get('trend_trajectory', 0.10)
        )

        phrat_score = math.sqrt(
            self.sub_weights.get('conflict_intensity', 0.40) * conflict_score ** 2 +
            self.sub_weights.get('displacement_burden', 0.35) * displacement_score ** 2 +
            self.sub_weights.get('health_system_disruption', 0.15) * disruption_score ** 2 +
            self.sub_weights.get('trend_trajectory', 0.10) * trend_score ** 2
        )

        adjusted_score = min(1.0, phrat_score * (1.0 + 0.2 * vulnerability_adj))

        sources_used = []
        if acled.get('available'):
            sources_used.append('ACLED')
        if idmc.get('available'):
            sources_used.append('IDMC')
        if worldbank.get('available'):
            sources_used.append('World Bank')

        confidence = self._compute_confidence(acled, idmc, worldbank)
        dominant = self._dominant_factor(conflict_score, displacement_score, disruption_score, trend_score)

        return {
            'score': round(adjusted_score, 4),
            'confidence': confidence,
            'components': {
                'conflict_intensity': round(conflict_score, 4),
                'displacement_burden': round(displacement_score, 4),
                'health_system_disruption': round(disruption_score, 4),
                'trend_trajectory': round(trend_score, 4),
                'vulnerability_adjustment': round(vulnerability_adj, 4),
                **conflict_components,
                **displacement_components,
            },
            'dominant_factor': dominant,
            'data_sources': sources_used,
            'available': bool(sources_used),
        }

    def _score_conflict_intensity(self, acled: Dict[str, Any]) -> tuple:
        if not acled.get('available'):
            return 0.0, {'acled_available': False}

        violent_events = acled.get('violent_events_12mo', 0) or 0
        fatalities = acled.get('fatalities_12mo', 0) or 0
        raw_score = acled.get('conflict_intensity_score', 0.0) or 0.0

        event_score = min(1.0, violent_events / 500.0)
        fatality_score = min(1.0, fatalities / 5000.0)
        combined = max(raw_score, event_score * 0.5 + fatality_score * 0.5)

        return combined, {
            'acled_violent_events_12mo': violent_events,
            'acled_fatalities_12mo': fatalities,
            'acled_hotspot_districts': acled.get('hotspot_districts', []),
        }

    def _score_displacement(self, idmc: Dict[str, Any], population: int) -> tuple:
        if not idmc.get('available'):
            return 0.0, {'idmc_available': False}

        displacement_score = idmc.get('displacement_score', 0.0) or 0.0
        conflict_new = idmc.get('conflict_new_displacements', 0) or 0
        disaster_new = idmc.get('disaster_new_displacements', 0) or 0
        total_idps = idmc.get('total_idps', 0) or 0

        return displacement_score, {
            'idmc_conflict_new_displacements': conflict_new,
            'idmc_disaster_new_displacements': disaster_new,
            'idmc_total_idps': total_idps,
            'idmc_displacement_year': idmc.get('year'),
        }

    def _score_health_disruption(
        self, conflict_score: float, displacement_score: float
    ) -> float:
        combined_pressure = (conflict_score * 0.60 + displacement_score * 0.40)
        if combined_pressure > 0.7:
            disruption = min(1.0, combined_pressure * 1.3)
        elif combined_pressure > 0.4:
            disruption = combined_pressure * 1.1
        else:
            disruption = combined_pressure * 0.8
        return round(disruption, 4)

    def _score_trend(self, acled: Dict[str, Any]) -> float:
        if not acled.get('available'):
            return TREND_SCORES['unknown']
        trend = acled.get('trend_direction', 'unknown')
        return TREND_SCORES.get(trend, TREND_SCORES['unknown'])

    def _compute_confidence(
        self,
        acled: Dict[str, Any],
        idmc: Dict[str, Any],
        worldbank: Dict[str, Any],
    ) -> float:
        sources = [acled, idmc, worldbank]
        available_count = sum(1 for s in sources if s.get('available'))
        return round(available_count / len(sources), 2)

    def _dominant_factor(
        self,
        conflict: float,
        displacement: float,
        disruption: float,
        trend: float,
    ) -> str:
        factors = {
            'Political violence and armed conflict': conflict,
            'Population displacement burden': displacement,
            'Health system disruption': disruption,
            'Escalating conflict trend': trend if trend > 0.7 else 0.0,
        }
        dominant = max(factors, key=factors.get)
        top_score = factors[dominant]
        if top_score < 0.1:
            return 'No significant conflict or displacement detected'
        return dominant

    def get_action_plan_items(self, score: float, components: Dict[str, Any]) -> List[str]:
        """Return prioritized action plan items based on domain score."""
        items = []
        if score >= 0.55:
            items.extend([
                'Activate emergency health coordination with protection cluster',
                'Deploy mobile health teams to high-displacement areas',
                'Establish trauma care and psychological first aid services',
                'Coordinate with UNHCR and IOM on health of displaced populations',
            ])
        if score >= 0.35:
            items.extend([
                'Develop contingency plans for potential mass displacement scenarios',
                'Pre-position medical supplies in conflict-adjacent districts',
                'Strengthen disease surveillance in IDP settlements and host communities',
                'Engage community health workers for conflict-affected populations',
            ])
        if score >= 0.15:
            items.extend([
                'Monitor ACLED and IDMC updates for emerging trends',
                'Review health facility security protocols',
                'Conduct population movement needs assessments',
            ])
        return items
