"""
Risk Alignment Utility

Provides centralized score computation for Action Plan and Risk Summary pages
to ensure consistent risk scoring and display across the application.
"""

import logging
from utils.metadata_config import EXCLUDED_RISK_FIELDS

logger = logging.getLogger(__name__)

def compute_display_scores(risk_data):
    """
    Compute canonical risk scores for display across Action Plan and Risk Summary pages.
    
    Args:
        risk_data: Risk data dictionary from process_risk_data()
        
    Returns:
        dict: Sorted dictionary with normalized keys and consistent scores
    """
    if not risk_data:
        return {}
    
    # Start with canonical score dictionary
    display_scores = {}
    
    # Process natural hazards from natural_hazards dict
    if 'natural_hazards' in risk_data and isinstance(risk_data['natural_hazards'], dict):
        for key, value in risk_data['natural_hazards'].items():
            # Skip metadata fields and ensure numeric values
            if key in EXCLUDED_RISK_FIELDS:
                continue
            try:
                score = float(value)
                display_scores[key] = score
            except (ValueError, TypeError):
                logger.warning(f"Skipping non-numeric natural hazard: {key}={value}")
                continue
    
    # Add major risk categories with normalized keys (remove "_risk" suffix)
    major_risks = {
        'health': 'health_risk',
        'active_shooter': 'active_shooter_risk', 
        'extreme_heat': 'extreme_heat_risk',
        'cybersecurity': 'cybersecurity_risk',
        'air_quality': 'air_quality_risk',
        'dam_failure': 'dam_failure_risk',
        'vector_borne_disease': 'vector_borne_disease_risk'
    }
    
    for normalized_key, field_name in major_risks.items():
        if field_name in risk_data and isinstance(risk_data[field_name], (int, float)):
            try:
                score = float(risk_data[field_name])
                display_scores[normalized_key] = score
            except (ValueError, TypeError):
                logger.warning(f"Skipping non-numeric major risk: {field_name}={risk_data[field_name]}")
                continue
    
    # Sort by score (highest first) for consistent ordering
    sorted_scores = dict(sorted(display_scores.items(), key=lambda x: x[1], reverse=True))
    
    logger.info(f"Computed {len(sorted_scores)} display scores: {list(sorted_scores.keys())}")
    return sorted_scores

def get_risk_score(display_scores, risk_key):
    """
    Get risk score for a specific risk type with fallback handling.
    
    Args:
        display_scores: Dictionary from compute_display_scores()
        risk_key: Risk key to lookup
        
    Returns:
        float: Risk score or 0.0 if not found
    """
    return display_scores.get(risk_key, 0.0)

def format_risk_name(risk_key):
    """
    Format risk key into display-friendly name.
    
    Args:
        risk_key: Normalized risk key
        
    Returns:
        str: Human-readable risk name
    """
    name_mapping = {
        'health': 'Health Risk',
        'active_shooter': 'Active Shooter Risk',
        'extreme_heat': 'Extreme Heat Risk',
        'cybersecurity': 'Cybersecurity Risk',
        'air_quality': 'Air Quality Risk',
        'dam_failure': 'Dam Failure Risk',
        'vector_borne_disease': 'Vector-Borne Disease Risk',
        'flood': 'Flood Risk',
        'tornado': 'Tornado Risk',
        'winter_storm': 'Winter Storm Risk',
        'thunderstorm': 'Thunderstorm Risk',
        'wildfire': 'Wildfire Risk',
        'drought': 'Drought Risk',
        'earthquake': 'Earthquake Risk',
        'hail': 'Hail Risk',
        'hurricane': 'Hurricane Risk',
        'ice_storm': 'Ice Storm Risk',
        'lightning': 'Lightning Risk',
        'riverine_flooding': 'Riverine Flooding Risk',
        'strong_wind': 'Strong Wind Risk',
        'volcanic_activity': 'Volcanic Activity Risk'
    }
    
    return name_mapping.get(risk_key, risk_key.replace('_', ' ').title())