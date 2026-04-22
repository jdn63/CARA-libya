"""
Main Risk Calculator for CARA

This module orchestrates the overall risk calculation by combining all risk domains
with configurable weights, normalization, and comprehensive contribution logging.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from utils.config_manager import get_config_manager
from utils.temporal_risk import TemporalRiskComponent
from utils.active_shooter_risk import ActiveShooterRiskModel
from utils.risk_calculation import calculate_residual_risk

logger = logging.getLogger(__name__)

class CARARiskCalculator:
    """
    Main risk calculator that orchestrates all risk domain calculations
    with configurable weights and normalization.
    """
    
    def __init__(self, jurisdiction_id: Optional[str] = None):
        self.jurisdiction_id = jurisdiction_id
        self.config_manager = get_config_manager()
        self.overall_weights = self.config_manager.get_overall_weights(jurisdiction_id)
        
        # Validate weights
        if not self.config_manager.validate_weights(self.overall_weights):
            logger.warning(f"Invalid overall weights for jurisdiction {jurisdiction_id}")
    
    def calculate_comprehensive_risk(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score across all domains with normalization and logging.
        
        Args:
            risk_data: Dictionary containing all risk assessment data
            
        Returns:
            Comprehensive risk assessment results with detailed breakdown
        """
        logger.info(f"Starting comprehensive risk calculation for jurisdiction {self.jurisdiction_id}")
        
        # Extract or calculate individual domain scores
        domain_scores = {}
        domain_contributions = []
        domain_details = {}
        
        # 1. Natural Hazards Risk
        natural_hazards_score = self._calculate_natural_hazards_risk(risk_data)
        domain_scores['natural_hazards'] = natural_hazards_score
        domain_details['natural_hazards'] = risk_data.get('natural_hazards', {})
        
        # 2. Health Metrics Risk  
        health_metrics_score = self._calculate_health_metrics_risk(risk_data)
        domain_scores['health_metrics'] = health_metrics_score
        domain_details['health_metrics'] = risk_data.get('health_metrics', {})
        
        # 3. Active Shooter Risk
        active_shooter_score = self._calculate_active_shooter_risk(risk_data)
        domain_scores['active_shooter'] = active_shooter_score
        domain_details['active_shooter'] = risk_data.get('active_shooter_analysis', {})
        
        # 4. Extreme Heat Risk
        extreme_heat_score = self._calculate_extreme_heat_risk(risk_data)
        domain_scores['extreme_heat'] = extreme_heat_score
        domain_details['extreme_heat'] = risk_data.get('extreme_heat', {})
        
        # 5. Cybersecurity Risk
        cybersecurity_score = self._calculate_cybersecurity_risk(risk_data)
        domain_scores['cybersecurity'] = cybersecurity_score
        domain_details['cybersecurity'] = risk_data.get('cybersecurity', {})
        
        # Apply normalization across domains
        normalized_scores = self.config_manager.normalize_scores(domain_scores, 'overall_risk')
        
        # Calculate weighted overall risk score
        overall_risk_score = 0.0
        for domain, score in normalized_scores.items():
            weight = self.overall_weights.get(domain, 0.0)
            contribution = score * weight
            overall_risk_score += contribution
            
            domain_contributions.append((
                domain, 
                contribution, 
                {'raw_score': domain_scores[domain], 'normalized_score': score, 'weight': weight}
            ))
        
        # Ensure score is in valid range
        overall_risk_score = max(0.0, min(1.0, overall_risk_score))
        
        # Log overall risk contributions
        self.config_manager.log_contribution(
            domain='overall_risk',
            variable_contributions=domain_contributions,
            final_score=overall_risk_score,
            jurisdiction_id=self.jurisdiction_id
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_risk_score)
        
        # Compile comprehensive results
        results = {
            'total_risk_score': round(overall_risk_score, 4),
            'risk_level': risk_level,
            'jurisdiction_id': self.jurisdiction_id,
            'domain_scores': {k: round(v, 4) for k, v in domain_scores.items()},
            'normalized_scores': {k: round(v, 4) for k, v in normalized_scores.items()},
            'domain_weights': self.overall_weights,
            'domain_contributions': {
                domain: {
                    'weighted_score': round(contrib, 4),
                    'percentage_of_total': round((contrib / overall_risk_score * 100) if overall_risk_score > 0 else 0, 2)
                }
                for domain, contrib, _ in domain_contributions
            },
            'domain_details': domain_details,
            'configuration_info': self.config_manager.get_config_info()
        }
        
        logger.info(f"Comprehensive risk calculation completed: {overall_risk_score:.4f} ({risk_level})")
        return results
    
    def _calculate_natural_hazards_risk(self, risk_data: Dict[str, Any]) -> float:
        """Calculate natural hazards risk from risk data"""
        natural_hazards = risk_data.get('natural_hazards', {})
        if not natural_hazards:
            return 0.0
        
        # Get sub-domain weights
        weights = self.config_manager.get_domain_weights('natural_hazards')
        if not weights:
            # Use equal weights if no configuration
            hazards = ['flood', 'tornado', 'winter_storm', 'thunderstorm']
            weights = {hazard: 1.0/len(hazards) for hazard in hazards}
        
        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0
        
        for hazard, weight in weights.items():
            if hazard in natural_hazards:
                score = natural_hazards[hazard]
                total_score += score * weight
                total_weight += weight
        
        # Normalize by actual weights used
        if total_weight > 0:
            return total_score / total_weight
        return 0.0
    
    def _calculate_health_metrics_risk(self, risk_data: Dict[str, Any]) -> float:
        """Calculate health metrics risk from risk data"""
        health_metrics = risk_data.get('health_metrics', {})
        if not health_metrics:
            return 0.0
        
        # Get sub-domain weights
        weights = self.config_manager.get_domain_weights('health_metrics')
        if not weights:
            # Default weights
            weights = {
                'respiratory_illness': 0.40,
                'vaccination_coverage': 0.25,
                'healthcare_capacity': 0.20,
                'vulnerable_populations': 0.15
            }
        
        # Map health metrics to our weight categories
        score_mapping = {
            'respiratory_illness': (health_metrics.get('ili_activity', 0) + 
                                  health_metrics.get('covid_activity', 0) + 
                                  health_metrics.get('rsv_activity', 0)) / 3,
            'vaccination_coverage': 1.0 - health_metrics.get('vaccination_rate', 0.8),  # Invert for risk
            'healthcare_capacity': health_metrics.get('healthcare_strain', 0.2),
            'vulnerable_populations': health_metrics.get('vulnerable_population_risk', 0.3)
        }
        
        # Calculate weighted score
        total_score = 0.0
        for category, weight in weights.items():
            score = score_mapping.get(category, 0.0)
            total_score += score * weight
        
        return min(1.0, total_score)
    
    def _calculate_active_shooter_risk(self, risk_data: Dict[str, Any]) -> float:
        """Calculate active shooter risk from risk data"""
        # Check for direct risk score first
        if 'active_shooter_risk' in risk_data:
            return risk_data['active_shooter_risk']
        
        # Fallback to analysis structure
        active_shooter_data = risk_data.get('active_shooter_analysis', {})
        if active_shooter_data:
            return active_shooter_data.get('active_shooter_risk', 0.0)
        
        return 0.0
    
    def _calculate_extreme_heat_risk(self, risk_data: Dict[str, Any]) -> float:
        """Calculate extreme heat risk from risk data"""
        # Check for direct risk score first
        if 'extreme_heat_risk' in risk_data:
            return risk_data['extreme_heat_risk']
        
        # Fallback to component structure
        extreme_heat = risk_data.get('extreme_heat', {})
        if not extreme_heat:
            return 0.0
        
        # Get sub-domain weights
        weights = self.config_manager.get_domain_weights('extreme_heat')
        if not weights:
            weights = {
                'vulnerability_index': 0.40,
                'urban_heat_island': 0.30,
                'climate_projections': 0.20,
                'adaptation_capacity': 0.10
            }
        
        # Calculate weighted score
        total_score = 0.0
        for component, weight in weights.items():
            if component in extreme_heat:
                score = extreme_heat[component]
                total_score += score * weight
        
        return min(1.0, total_score)
    
    def _calculate_cybersecurity_risk(self, risk_data: Dict[str, Any]) -> float:
        """Calculate cybersecurity risk from risk data"""
        # Placeholder for cybersecurity risk calculation
        # This would integrate with cybersecurity assessment data
        return risk_data.get('cybersecurity_risk', 0.2)  # Default moderate risk
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score >= 0.7:
            return "High"
        elif score >= 0.4:
            return "Moderate"
        elif score >= 0.2:
            return "Low"
        else:
            return "Very Low"

def calculate_comprehensive_risk(risk_data: Dict[str, Any], 
                               jurisdiction_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for comprehensive risk calculation.
    
    Args:
        risk_data: Risk assessment data
        jurisdiction_id: Optional jurisdiction identifier
        
    Returns:
        Comprehensive risk assessment results
    """
    calculator = CARARiskCalculator(jurisdiction_id)
    return calculator.calculate_comprehensive_risk(risk_data)