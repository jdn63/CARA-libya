"""
Mass Casualty and Public Safety Events Risk Domain.

This domain replaces the US-specific "active shooter" domain for the international
profile. For US state profiles, it activates an active shooter sub-component
using Gun Violence Archive (GVA) and RAND firearm law data.

For international profiles, it uses EM-DAT technological disaster data and
ACLED mass violence data to assess risk from:
  - Terrorism and targeted attacks
  - Mass violence and civil unrest
  - Industrial and technological accidents with mass casualty potential
  - Crowd crush and stadium/event disasters

Risk components:
  1. Historical Event Frequency (35%) — past mass casualty event rate
  2. Vulnerability Score (30%) — population density, public gathering density
  3. Preparedness Capacity (20%) — emergency response systems, trauma capacity
  4. Environmental Risk Factors (15%) — industrial hazard proximity, infrastructure

US sub-type (active_shooter):
  Adds firearm-specific components using Gun Violence Archive incident data,
  RAND State Firearm Law Database scores, and NCES school safety data.
"""

import logging
import math
from typing import Any, Dict, List, Optional
from utils.domains.base_domain import BaseDomain

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    'event_frequency': 0.35,
    'vulnerability': 0.30,
    'preparedness': 0.20,
    'environmental_risk': 0.15,
}

US_WEIGHTS = {
    'firearm_access': 0.25,
    'gva_incidents': 0.25,
    'protective_capacity': 0.25,
    'population_vulnerability': 0.25,
}


class MassCasualtyDomain(BaseDomain):
    """
    Mass Casualty and Public Safety Events Risk Domain.

    Supports both international and US state profiles. The US profile activates
    active shooter-specific sub-components while retaining the general mass
    casualty framework structure.
    """

    DOMAIN_ID = 'mass_casualty'
    DOMAIN_LABEL = 'Mass Casualty and Public Safety Events'

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        super().__init__(weights or DEFAULT_WEIGHTS)

    def domain_info(self) -> Dict[str, Any]:
        return {
            'id': self.DOMAIN_ID,
            'label': self.DOMAIN_LABEL,
            'description': (
                'Measures public health risk from mass casualty events and public safety '
                'incidents, including terrorism, mass violence, civil unrest, and '
                'large-scale technological accidents. For US state deployments, an '
                'active shooter sub-component is included using firearm-specific data. '
                'This domain uses historical event frequency, population vulnerability, '
                'emergency preparedness capacity, and environmental risk factors.'
            ),
            'methodology': (
                'For international profiles: combines EM-DAT technological disaster history, '
                'ACLED mass violence event data, and World Bank vulnerability indicators. '
                'For US profiles: adds Gun Violence Archive incident data, RAND Firearm Law '
                'Database scores, and NCES school safety data. All scores use the PHRAT '
                'quadratic mean for component aggregation.'
            ),
            'applicable_profiles': ['us_state', 'international'],
            'data_sources': [
                {
                    'name': 'EM-DAT (for non-US deployments)',
                    'url': 'https://www.emdat.be',
                    'notes': 'Technological disaster history.',
                },
                {
                    'name': 'ACLED (for non-US deployments)',
                    'url': 'https://acleddata.com',
                    'notes': 'Mass violence event data.',
                },
                {
                    'name': 'Gun Violence Archive (US profile only)',
                    'url': 'https://www.gunviolencearchive.org',
                    'notes': 'US active shooter and mass shooting incidents.',
                },
                {
                    'name': 'RAND State Firearm Law Database (US profile only)',
                    'url': 'https://www.rand.org/pubs/tools/TL354-1.html',
                    'notes': 'State firearm law restrictiveness score.',
                },
            ],
        }

    def calculate(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
        profile: str = 'international',
    ) -> Dict[str, Any]:
        domain_cfg = jurisdiction_config.get('domain_config', {}).get('mass_casualty', {})
        us_subtype = domain_cfg.get('us_subtype', False) and profile == 'us_state'

        if us_subtype:
            return self._calculate_us(connector_data, jurisdiction_config)
        return self._calculate_international(connector_data, jurisdiction_config)

    def _calculate_international(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        em_dat = connector_data.get('em_dat', {})
        acled = connector_data.get('acled', {})
        worldbank = connector_data.get('worldbank', {})

        event_score = self._score_events_international(em_dat, acled)
        vulnerability_score = self._score_vulnerability_international(worldbank)
        preparedness_score = self._score_preparedness(worldbank)
        environmental_score = self._score_environmental(em_dat)

        phrat_score = math.sqrt(
            self.sub_weights.get('event_frequency', 0.35) * event_score ** 2 +
            self.sub_weights.get('vulnerability', 0.30) * vulnerability_score ** 2 +
            self.sub_weights.get('preparedness', 0.20) * preparedness_score ** 2 +
            self.sub_weights.get('environmental_risk', 0.15) * environmental_score ** 2
        )

        sources = [s for s, d in [
            ('EM-DAT', em_dat), ('ACLED', acled), ('World Bank', worldbank)
        ] if d.get('available')]

        return {
            'score': round(min(1.0, phrat_score), 4),
            'confidence': round(len(sources) / 3.0, 2),
            'components': {
                'event_frequency': round(event_score, 4),
                'vulnerability': round(vulnerability_score, 4),
                'preparedness': round(preparedness_score, 4),
                'environmental_risk': round(environmental_score, 4),
                'em_dat_events_10yr': em_dat.get('total_events_10yr', 0),
                'em_dat_dominant_hazard': em_dat.get('dominant_hazard'),
                'acled_mass_violence_events': acled.get(
                    'events_by_type', {}
                ).get('Violence against civilians', 0),
            },
            'dominant_factor': self._dominant_factor_international(
                event_score, vulnerability_score, preparedness_score
            ),
            'data_sources': sources,
            'available': bool(sources),
        }

    def _calculate_us(
        self,
        connector_data: Dict[str, Any],
        jurisdiction_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        gva = connector_data.get('gun_violence_archive', {})
        rand = connector_data.get('rand_firearm', {})
        census = connector_data.get('census', {})
        svi = connector_data.get('svi', {})

        firearm_access = rand.get('restrictiveness_inverse', 0.5) if rand.get('available') else 0.5
        gva_rate = min(1.0, (gva.get('mass_shootings_per_100k', 0) or 0) / 5.0) if gva.get('available') else 0.3
        protective_capacity = connector_data.get('health_metrics', {}).get('protective_capacity', 0.5) or 0.5
        vulnerability = svi.get('svi_percentile', 50) / 100.0 if svi.get('available') else 0.5

        phrat_score = math.sqrt(
            US_WEIGHTS['firearm_access'] * firearm_access ** 2 +
            US_WEIGHTS['gva_incidents'] * gva_rate ** 2 +
            US_WEIGHTS['protective_capacity'] * protective_capacity ** 2 +
            US_WEIGHTS['population_vulnerability'] * vulnerability ** 2
        )

        return {
            'score': round(min(1.0, phrat_score), 4),
            'confidence': 0.7,
            'components': {
                'firearm_access_score': round(firearm_access, 4),
                'gva_incident_rate': round(gva_rate, 4),
                'protective_capacity': round(protective_capacity, 4),
                'population_vulnerability': round(vulnerability, 4),
            },
            'dominant_factor': 'Active shooter risk (US profile)',
            'data_sources': ['Gun Violence Archive', 'RAND Firearm Law Database'],
            'available': True,
            'us_active_shooter_subtype': True,
        }

    def _score_events_international(
        self, em_dat: Dict, acled: Dict
    ) -> float:
        em_score = 0.0
        if em_dat.get('available'):
            tech_events = sum(
                v for k, v in (em_dat.get('events_by_type') or {}).items()
                if any(t in k.lower() for t in ['accident', 'industrial', 'transport'])
            )
            em_score = min(1.0, tech_events / 20.0)

        acled_score = 0.0
        if acled.get('available'):
            mass_violence = (acled.get('events_by_type') or {}).get(
                'Violence against civilians', 0
            )
            acled_score = min(1.0, mass_violence / 100.0)

        if em_dat.get('available') and acled.get('available'):
            return em_score * 0.4 + acled_score * 0.6
        return em_score or acled_score

    def _score_vulnerability_international(self, worldbank: Dict) -> float:
        if not worldbank.get('available'):
            return 0.4
        return worldbank.get('vulnerability_index', 0.4) or 0.4

    def _score_preparedness(self, worldbank: Dict) -> float:
        if not worldbank.get('available'):
            return 0.5
        gdp_pc = worldbank.get('gdp_per_capita', 5000) or 5000
        access_electricity = worldbank.get('access_electricity', 80) or 80
        prep = (1.0 - min(1.0, gdp_pc / 50000.0)) * 0.6 + (1.0 - access_electricity / 100.0) * 0.4
        return round(prep, 4)

    def _score_environmental(self, em_dat: Dict) -> float:
        if not em_dat.get('available'):
            return 0.3
        total = em_dat.get('total_events_10yr', 0) or 0
        return min(1.0, total / 30.0)

    def _dominant_factor_international(
        self, event_score: float, vulnerability_score: float, preparedness_score: float
    ) -> str:
        factors = {
            'Historical mass casualty event frequency': event_score,
            'Population vulnerability': vulnerability_score,
            'Emergency response capacity gaps': preparedness_score,
        }
        return max(factors, key=factors.get)
