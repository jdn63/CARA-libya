"""
WHO International Health Regulations (IHR) assessment framework.

Maps CARA domain scores to the 13 core IHR capacities and supports
the Joint External Evaluation (JEE) framework as a supplementary lens.

IHR core capacities: https://www.who.int/health-topics/international-health-regulations
JEE framework: https://www.who.int/emergencies/operations/international-health-regulations-monitoring-evaluation-framework/joint-external-evaluations

This framework is used by the international profile.
"""

import logging
from typing import Any, Dict, List, Optional
from utils.frameworks.base_framework import BaseFramework

logger = logging.getLogger(__name__)

IHR_CAPACITIES = [
    {
        'id': 'legislation_policy_financing',
        'label': 'Legislation, Policy and Financing',
        'description': 'Legal and regulatory frameworks for public health emergency preparedness',
        'domain_links': [],
        'jee_domain': 'P.1',
    },
    {
        'id': 'ihr_coordination',
        'label': 'IHR Coordination, Communication and Advocacy',
        'description': 'Multi-sector coordination mechanisms for IHR implementation',
        'domain_links': [],
        'jee_domain': 'P.2',
    },
    {
        'id': 'antimicrobial_resistance',
        'label': 'Antimicrobial Resistance',
        'description': 'Detection and response to antimicrobial-resistant pathogens',
        'domain_links': ['health_metrics', 'vector_borne_disease'],
        'jee_domain': 'P.3',
    },
    {
        'id': 'zoonotic_disease',
        'label': 'Zoonotic Disease',
        'description': 'Surveillance and response at the human-animal-environment interface',
        'domain_links': ['vector_borne_disease', 'health_metrics'],
        'jee_domain': 'P.4',
    },
    {
        'id': 'food_safety',
        'label': 'Food Safety',
        'description': 'Detection and response to food safety events',
        'domain_links': ['health_metrics'],
        'jee_domain': 'P.5',
    },
    {
        'id': 'biosafety_biosecurity',
        'label': 'Biosafety and Biosecurity',
        'description': 'Laboratory biosafety and biosecurity measures',
        'domain_links': ['health_metrics'],
        'jee_domain': 'P.6',
    },
    {
        'id': 'immunization',
        'label': 'Immunization',
        'description': 'Vaccination coverage and immunization program capacity',
        'domain_links': ['health_metrics', 'vector_borne_disease'],
        'jee_domain': 'P.7',
    },
    {
        'id': 'national_laboratory_system',
        'label': 'National Laboratory System',
        'description': 'Laboratory capacity for pathogen detection and confirmation',
        'domain_links': ['health_metrics'],
        'jee_domain': 'D.1',
    },
    {
        'id': 'real_time_surveillance',
        'label': 'Real-time Surveillance',
        'description': 'Event-based and indicator-based surveillance systems',
        'domain_links': ['health_metrics', 'vector_borne_disease'],
        'jee_domain': 'D.2',
    },
    {
        'id': 'reporting',
        'label': 'Reporting to WHO',
        'description': 'Notification of potential public health events of international concern',
        'domain_links': [],
        'jee_domain': 'D.3',
    },
    {
        'id': 'workforce_development',
        'label': 'Human Resources',
        'description': 'Workforce capacity for IHR implementation',
        'domain_links': ['health_metrics'],
        'jee_domain': 'D.4',
    },
    {
        'id': 'preparedness',
        'label': 'Preparedness',
        'description': 'National emergency preparedness plans, exercises, and simulations',
        'domain_links': ['natural_hazards', 'conflict_displacement', 'mass_casualty'],
        'jee_domain': 'R.1',
    },
    {
        'id': 'emergency_response_operations',
        'label': 'Emergency Response Operations',
        'description': 'Emergency operation center capacity and multi-hazard response',
        'domain_links': ['natural_hazards', 'conflict_displacement', 'mass_casualty', 'extreme_heat'],
        'jee_domain': 'R.2',
    },
    {
        'id': 'linking_public_health_security',
        'label': 'Linking Public Health and Security Authorities',
        'description': 'Coordination between health and security sectors in emergencies',
        'domain_links': ['conflict_displacement', 'mass_casualty'],
        'jee_domain': 'R.3',
    },
    {
        'id': 'medical_countermeasures',
        'label': 'Medical Countermeasures and Personnel Deployment',
        'description': 'Access to and deployment of medical countermeasures',
        'domain_links': ['health_metrics', 'mass_casualty'],
        'jee_domain': 'R.4',
    },
    {
        'id': 'risk_communication',
        'label': 'Risk Communication',
        'description': 'Risk communication capacity and community engagement',
        'domain_links': ['conflict_displacement'],
        'jee_domain': 'R.5',
    },
    {
        'id': 'points_of_entry',
        'label': 'Points of Entry',
        'description': 'Health measures at international ports, airports, and ground crossings',
        'domain_links': ['health_metrics', 'conflict_displacement'],
        'jee_domain': 'PoE.1',
    },
    {
        'id': 'chemical_events',
        'label': 'Chemical Events',
        'description': 'Detection and response to chemical events',
        'domain_links': ['air_quality', 'mass_casualty'],
        'jee_domain': 'CE.1',
    },
    {
        'id': 'radiation_emergencies',
        'label': 'Radiation Emergencies',
        'description': 'Detection and response to radiological and nuclear events',
        'domain_links': ['mass_casualty'],
        'jee_domain': 'RE.1',
    },
]

PRIORITY_THRESHOLDS = {
    'critical': 0.70,
    'high': 0.50,
    'medium': 0.30,
    'low': 0.0,
}


class WHOIHRFramework(BaseFramework):
    """WHO International Health Regulations framework."""

    FRAMEWORK_ID = 'who_ihr'
    FRAMEWORK_NAME = 'WHO International Health Regulations (IHR 2005)'
    FRAMEWORK_URL = 'https://www.who.int/health-topics/international-health-regulations'

    def get_capabilities(self) -> List[Dict[str, Any]]:
        return IHR_CAPACITIES

    def get_capability_score(
        self,
        capability_id: str,
        domain_scores: Dict[str, float],
    ) -> float:
        cap = next((c for c in IHR_CAPACITIES if c['id'] == capability_id), None)
        if not cap or not cap['domain_links']:
            return 0.3
        linked_scores = [domain_scores.get(d, 0.3) for d in cap['domain_links']]
        return round(sum(linked_scores) / len(linked_scores), 4)

    def map_to_action_plan(
        self,
        domain_scores: Dict[str, float],
        jurisdiction_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        actions = []

        for cap in IHR_CAPACITIES:
            cap_score = self.get_capability_score(cap['id'], domain_scores)
            linked_scores = [domain_scores.get(d, 0) for d in cap['domain_links']]
            max_linked = max(linked_scores) if linked_scores else 0.0

            if max_linked >= PRIORITY_THRESHOLDS['critical']:
                priority = 'critical'
                timeframe = 'immediate'
            elif max_linked >= PRIORITY_THRESHOLDS['high']:
                priority = 'high'
                timeframe = '30_days'
            elif max_linked >= PRIORITY_THRESHOLDS['medium']:
                priority = 'medium'
                timeframe = '90_days'
            else:
                continue

            action_items = IHR_ACTIONS.get(cap['id'], [])
            for action in action_items:
                actions.append({
                    'capability': cap['id'],
                    'capability_label': cap['label'],
                    'priority': priority,
                    'action': action,
                    'domains': cap['domain_links'],
                    'timeframe': timeframe,
                    'jee_reference': cap.get('jee_domain', ''),
                })

        actions.sort(key=lambda x: list(PRIORITY_THRESHOLDS.keys()).index(x['priority']))
        return actions


IHR_ACTIONS = {
    'preparedness': [
        'Review and update national/subnational emergency preparedness plan',
        'Conduct multi-hazard tabletop exercise with all relevant sectors',
        'Ensure emergency operations center is operational and staffed',
        'Pre-position essential medicines, equipment, and supplies',
    ],
    'emergency_response_operations': [
        'Activate incident management system for identified high-risk events',
        'Establish 24/7 on-call emergency response roster',
        'Review and test emergency communication systems',
        'Coordinate with neighboring jurisdictions on cross-border response',
    ],
    'linking_public_health_security': [
        'Formalize memoranda of understanding with security authorities',
        'Conduct joint public health-security training exercises',
        'Establish protocols for health service delivery in insecure environments',
    ],
    'real_time_surveillance': [
        'Strengthen event-based surveillance for all high-risk domains',
        'Ensure laboratory confirmation capacity for priority pathogens',
        'Establish 24-hour reporting from sentinel surveillance sites',
    ],
    'risk_communication': [
        'Develop risk communication plan for highest-scoring risk domains',
        'Train community health workers on emergency communication',
        'Establish trusted community spokesperson network',
    ],
    'immunization': [
        'Review vaccination coverage for priority populations',
        'Identify and address gaps in cold chain infrastructure',
        'Plan supplementary immunization activities for high-risk groups',
    ],
    'medical_countermeasures': [
        'Review national stockpile adequacy for priority hazards',
        'Establish agreements for rapid medical countermeasure deployment',
    ],
    'points_of_entry': [
        'Review health screening protocols at international ports and airports',
        'Ensure capacity for quarantine and isolation at points of entry',
    ],
    'chemical_events': [
        'Review chemical hazard inventory and risk assessment',
        'Ensure clinical toxicology capacity for chemical exposure management',
    ],
}
