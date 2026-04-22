"""
CDC Public Health Emergency Preparedness (PHEP) assessment framework.

Maps CARA domain scores to the 15 PHEP capabilities defined by the CDC
Public Health Emergency Preparedness cooperative agreement.

PHEP capabilities: https://www.cdc.gov/cpr/readiness/capabilities.htm

This framework is used by the US state profile.
"""

import logging
from typing import Any, Dict, List, Optional
from utils.frameworks.base_framework import BaseFramework

logger = logging.getLogger(__name__)

PHEP_CAPABILITIES = [
    {
        'id': 'community_preparedness',
        'label': 'Community Preparedness',
        'description': 'Engage the whole community to strengthen preparedness and resilience',
        'domain_links': ['health_metrics'],
    },
    {
        'id': 'community_recovery',
        'label': 'Community Recovery',
        'description': 'Collaborate with community-based organizations to restore public health',
        'domain_links': ['natural_hazards', 'extreme_heat'],
    },
    {
        'id': 'emergency_operations_coordination',
        'label': 'Emergency Operations Coordination',
        'description': 'Activate and operate an emergency operations center',
        'domain_links': ['natural_hazards', 'mass_casualty', 'extreme_heat'],
    },
    {
        'id': 'emergency_public_information_and_warning',
        'label': 'Emergency Public Information and Warning',
        'description': 'Develop and deliver timely, accurate public health information',
        'domain_links': ['health_metrics', 'extreme_heat'],
    },
    {
        'id': 'fatality_management',
        'label': 'Fatality Management',
        'description': 'Collaborate with death care organizations for mass fatality events',
        'domain_links': ['mass_casualty', 'natural_hazards'],
    },
    {
        'id': 'healthcare_preparedness',
        'label': 'Healthcare Preparedness',
        'description': 'Coordinate healthcare coalitions for medical surge and mass casualty',
        'domain_links': ['mass_casualty', 'health_metrics'],
    },
    {
        'id': 'information_sharing',
        'label': 'Information Sharing',
        'description': 'Identify and manage public health information sharing needs',
        'domain_links': ['health_metrics'],
    },
    {
        'id': 'mass_care',
        'label': 'Mass Care',
        'description': 'Coordinate with partner agencies for sheltering and feeding populations',
        'domain_links': ['natural_hazards', 'extreme_heat'],
    },
    {
        'id': 'medical_countermeasure_dispensing',
        'label': 'Medical Countermeasure Dispensing and Administration',
        'description': 'Dispense and administer medical countermeasures to at-risk populations',
        'domain_links': ['health_metrics', 'vector_borne_disease'],
    },
    {
        'id': 'medical_materiel_management',
        'label': 'Medical Materiel Management and Distribution',
        'description': 'Acquire, manage, and distribute medical materiel for health incidents',
        'domain_links': ['health_metrics', 'mass_casualty'],
    },
    {
        'id': 'medical_surge',
        'label': 'Medical Surge',
        'description': 'Assess and support the healthcare system during high-demand events',
        'domain_links': ['health_metrics', 'mass_casualty', 'natural_hazards'],
    },
    {
        'id': 'non_pharmaceutical_interventions',
        'label': 'Non-Pharmaceutical Interventions',
        'description': 'Implement community mitigation strategies for infectious disease',
        'domain_links': ['health_metrics', 'vector_borne_disease'],
    },
    {
        'id': 'public_health_laboratory_testing',
        'label': 'Public Health Laboratory Testing',
        'description': 'Conduct rapid laboratory testing to support emergency response',
        'domain_links': ['health_metrics', 'vector_borne_disease'],
    },
    {
        'id': 'public_health_surveillance',
        'label': 'Public Health Surveillance and Epidemiological Investigation',
        'description': 'Conduct surveillance and epidemiological investigation during emergencies',
        'domain_links': ['health_metrics', 'vector_borne_disease', 'air_quality'],
    },
    {
        'id': 'responder_safety_and_health',
        'label': 'Responder Safety and Health',
        'description': 'Protect responders from physical and mental health hazards',
        'domain_links': ['mass_casualty', 'air_quality', 'extreme_heat'],
    },
]

PRIORITY_THRESHOLDS = {
    'critical': 0.70,
    'high': 0.50,
    'medium': 0.30,
    'low': 0.0,
}


class CDCPHEPFramework(BaseFramework):
    """CDC Public Health Emergency Preparedness framework."""

    FRAMEWORK_ID = 'cdc_phep'
    FRAMEWORK_NAME = 'CDC Public Health Emergency Preparedness (PHEP)'
    FRAMEWORK_URL = 'https://www.cdc.gov/cpr/readiness/capabilities.htm'

    def get_capabilities(self) -> List[Dict[str, Any]]:
        return PHEP_CAPABILITIES

    def get_capability_score(
        self,
        capability_id: str,
        domain_scores: Dict[str, float],
    ) -> float:
        cap = next((c for c in PHEP_CAPABILITIES if c['id'] == capability_id), None)
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

        for cap in PHEP_CAPABILITIES:
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

            for action in PHEP_ACTIONS.get(cap['id'], []):
                actions.append({
                    'capability': cap['id'],
                    'capability_label': cap['label'],
                    'priority': priority,
                    'action': action,
                    'domains': cap['domain_links'],
                    'timeframe': timeframe,
                })

        actions.sort(key=lambda x: list(PRIORITY_THRESHOLDS.keys()).index(x['priority']))
        return actions


PHEP_ACTIONS = {
    'emergency_operations_coordination': [
        'Activate the health department emergency operations center',
        'Establish Incident Command System structure and fill key positions',
        'Conduct operational briefings at scheduled intervals',
    ],
    'medical_surge': [
        'Assess hospital capacity and activate surge protocols',
        'Coordinate with healthcare coalition on resource sharing',
        'Identify and open alternate care sites as needed',
    ],
    'public_health_surveillance': [
        'Increase surveillance frequency for highest-risk disease categories',
        'Ensure 24-hour reporting from sentinel surveillance sites',
        'Submit required CDC and state-level situation reports',
    ],
    'medical_countermeasure_dispensing': [
        'Review SNS request process and points of dispensing plans',
        'Conduct medication dispensing exercise or drill',
        'Identify and address cold chain vulnerabilities',
    ],
    'healthcare_preparedness': [
        'Convene healthcare coalition emergency planning meeting',
        'Test hospital notification system',
        'Review and update mutual aid agreements',
    ],
    'mass_care': [
        'Coordinate with emergency management on shelter-in-place protocols',
        'Review and update memoranda of understanding with Red Cross and Salvation Army',
        'Identify accessible shelter facilities for special needs populations',
    ],
    'community_preparedness': [
        'Engage community-based organizations in preparedness planning',
        'Update community health emergency plan',
        'Conduct public preparedness awareness campaign',
    ],
    'responder_safety_and_health': [
        'Brief all deployed staff on personal protective equipment protocols',
        'Activate employee assistance program for mental health support',
        'Establish responder decontamination protocols',
    ],
    'non_pharmaceutical_interventions': [
        'Review isolation and quarantine authorities and protocols',
        'Develop public communication plan for NPI implementation',
        'Coordinate school closure decision-making with education authorities',
    ],
    'fatality_management': [
        'Activate mass fatality management plan',
        'Coordinate with medical examiner and funeral directors',
        'Establish family assistance center operations',
    ],
}
