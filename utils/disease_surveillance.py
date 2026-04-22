"""
Disease Surveillance Module

This module provides functionality for tracking infectious disease activity
across different jurisdictions.

- Supports weekly data updates with options for more frequent updates during outbreaks
- Implements caching with appropriate expiry times for different data types
- Provides disease activity scoring based on current surveillance data
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timedelta

# Import cache utilities
from utils.persistent_cache import (
    get_from_persistent_cache,
    set_in_persistent_cache,
    clear_cache_by_prefix
)

from utils.cache import (
    get_from_memory_cache,
    set_in_memory_cache,
    remove_from_memory_cache
)

# Import data processor for county mapping
from utils.data_processor import get_county_for_jurisdiction

logger = logging.getLogger(__name__)

# Constants
DISEASE_CACHE_PREFIX = "disease_activity_"  # Prefix for disease data cache keys
DISEASE_CACHE_EXPIRY = 7  # Default cache expiry in days

# In-memory cache for frequently accessed disease data
_disease_activity_cache = {}

def get_disease_metrics(county_name: str) -> Dict[str, Any]:
    """
    Get comprehensive disease metrics for a specific county using Wisconsin DHS surveillance data.
    
    Args:
        county_name: Name of the county
        
    Returns:
        Dictionary containing disease metrics including:
        - Influenza-like illness (ILI) activity
        - COVID-19 activity
        - RSV activity
        - Overall health risk score
    """
    try:
        # Import Wisconsin DHS scraper
        from utils.wisconsin_dhs_scraper import get_wisconsin_surveillance_data
        
        # Get statewide surveillance data from Wisconsin DHS
        surveillance_data = get_wisconsin_surveillance_data()
        
        # Extract key metrics from DHS surveillance data
        statewide_activity = surveillance_data.get('statewide_activity', {})
        lab_data = surveillance_data.get('laboratory_data', {})
        risk_indicators = surveillance_data.get('risk_indicators', {})
        
        # Map statewide data to county-level estimates
        # Since DHS provides statewide data, we use it for all counties
        # with slight variation based on regional data if available
        regional_adjustment = _get_regional_adjustment(county_name, surveillance_data)
        
        # Extract vaccination data from DHS surveillance
        vaccination_data = surveillance_data.get('vaccination_data', {})
        
        # Create metrics structure based on actual DHS data
        metrics = {
            'ili_activity': _map_activity_to_score(statewide_activity.get('influenza', 'low')) * regional_adjustment,
            'covid_activity': _map_activity_to_score(statewide_activity.get('covid19', 'minimal')) * regional_adjustment,
            'rsv_activity': _map_activity_to_score(statewide_activity.get('rsv', 'minimal')) * regional_adjustment,
            'lab_positivity': {
                'influenza': lab_data.get('influenza_percent', 2.5),
                'covid19': lab_data.get('covid19_percent', 2.3),
                'rsv': lab_data.get('rsv_percent', 0.8)
            },
            'vaccination_rates': {
                'flu_overall': vaccination_data.get('flu_vaccination', {}).get('overall_population', 52.1),
                'covid19_overall': vaccination_data.get('covid19_vaccination', {}).get('overall_coverage', 73.6),
                'mmr_school_age': vaccination_data.get('mmr_vaccination', {}).get('children_5_18_years', 87.8),
                'school_compliance': vaccination_data.get('school_vaccination', {}).get('meeting_minimum_requirements', 86.4)
            },
            'last_updated': surveillance_data.get('last_updated', datetime.now().isoformat())
        }
        
        # Calculate the overall risk score using DHS risk indicators and vaccination protection
        dhs_combined_risk = risk_indicators.get('combined_risk', 0.45)
        
        # Calculate enhanced vaccination risk assessment for strategic planning
        vaccination_risk_assessment = _calculate_strategic_vaccination_risk(vaccination_data, county_name)
        
        # Apply strategic vaccination risk framework (replaces simple protection factor)
        # This accounts for herd immunity gaps, outbreak conditions, and policy decision needs
        base_risk_with_vaccination = dhs_combined_risk * vaccination_risk_assessment['risk_multiplier']
        risk_score = min(1.0, max(0.0, base_risk_with_vaccination * regional_adjustment))
        
        # Determine activity levels based on DHS classifications
        activity_levels = {
            'ili': statewide_activity.get('influenza', 'low'),
            'covid': statewide_activity.get('covid19', 'minimal'),
            'rsv': statewide_activity.get('rsv', 'minimal'),
            'overall': statewide_activity.get('overall', 'moderate')
        }
        
        # Determine trend from emergency department data
        ed_data = surveillance_data.get('emergency_dept_data', {})
        trend_data = ed_data.get('trends', {})
        trend = _determine_overall_trend([
            trend_data.get('influenza', 'stable'),
            trend_data.get('covid19', 'stable'),
            trend_data.get('rsv', 'stable')
        ])
        
        return {
            'risk_score': risk_score,
            'metrics': metrics,
            'activity_levels': activity_levels,
            'trend': trend,
            'vaccination_risk_assessment': vaccination_risk_assessment,
            'report_date': surveillance_data.get('report_date'),
            'confidence': risk_indicators.get('confidence', 0.8),
            'last_updated': surveillance_data.get('last_updated', datetime.now().isoformat()),
            'data_sources': ['Wisconsin DHS Respiratory Surveillance Reports'],
            'source_url': surveillance_data.get('report_url', 'https://www.dhs.wisconsin.gov/disease/respiratory-data.htm')
        }
    except Exception as e:
        logger.error(f"Error getting disease metrics for {county_name}: {str(e)}")
        # Return empty structure with zero values
        # Get fallback vaccination risk assessment for consistency
        fallback_vaccination_assessment = _get_fallback_vaccination_risk_assessment()
        
        return {
            'risk_score': 0.6,  # Higher conservative risk given active outbreak conditions
            'metrics': {
                'ili_activity': 0.3,
                'covid_activity': 0.25,
                'rsv_activity': 0.1,
                'lab_positivity': {
                    'influenza': 2.5,
                    'covid19': 2.3,
                    'rsv': 0.8
                },
                'vaccination_rates': {
                    'flu_overall': 52.1,
                    'covid19_overall': 73.6,
                    'mmr_school_age': 87.8,
                    'school_compliance': 86.4
                },
                'last_updated': datetime.now().isoformat()
            },
            'activity_levels': {
                'ili': 'low',
                'covid': 'minimal',
                'rsv': 'minimal',
                'overall': 'high'  # Updated to reflect outbreak conditions
            },
            'trend': 'increasing',  # Updated to reflect outbreak trends
            'vaccination_risk_assessment': fallback_vaccination_assessment,
            'confidence': 0.3,  # Low confidence for fallback data
            'last_updated': datetime.now().isoformat(),
            'data_sources': ['Fallback estimates - Wisconsin DHS data unavailable']
        }

def _map_activity_to_score(activity_level: str) -> float:
    """Map DHS activity level strings to numeric scores (0.0-1.0)"""
    activity_mapping = {
        'minimal': 0.1,
        'low': 0.3,
        'moderate': 0.6,
        'high': 0.8,
        'very_high': 1.0
    }
    return activity_mapping.get(activity_level.lower(), 0.4)

def _get_regional_adjustment(county_name: str, surveillance_data: Dict[str, Any]) -> float:
    """
    Get regional adjustment factor for county-specific disease risk
    
    Args:
        county_name: Name of the county
        surveillance_data: Statewide surveillance data from DHS
        
    Returns:
        Adjustment factor (0.8-1.2) based on regional patterns
    """
    # Get regional data if available
    regional_data = surveillance_data.get('regional_activity', {})
    
    # Map counties to DHS regions (simplified mapping)
    county_to_region = {
        # Southeastern region (higher population density)
        'milwaukee': 'southeastern',
        'waukesha': 'southeastern', 
        'racine': 'southeastern',
        'kenosha': 'southeastern',
        'washington': 'southeastern',
        'ozaukee': 'southeastern',
        
        # Southern region
        'dane': 'southern',
        'rock': 'southern',
        'jefferson': 'southern',
        'walworth': 'southern',
        
        # Fox Valley region
        'winnebago': 'fox_valley',
        'outagamie': 'fox_valley',
        'brown': 'fox_valley',
        'calumet': 'fox_valley',
        
        # Western region
        'la_crosse': 'western',
        'eau_claire': 'western',
        'chippewa': 'western',
        
        # Northern region (lower population density)
        'oneida': 'northern',
        'vilas': 'northern',
        'iron': 'northern'
    }
    
    # Normalize county name for lookup
    county_key = county_name.lower().replace(' ', '_').replace('county', '').strip()
    region = county_to_region.get(county_key, 'other')
    
    # Regional adjustment factors based on population density and historical patterns
    regional_adjustments = {
        'southeastern': 1.1,  # Higher risk due to population density
        'southern': 1.05,     # Moderate adjustment for urban areas
        'fox_valley': 1.0,    # Baseline
        'western': 0.95,      # Slightly lower rural risk
        'northern': 0.9,      # Lower risk in less dense areas
        'other': 1.0          # Default for unmapped counties
    }
    
    base_adjustment = regional_adjustments.get(region, 1.0)
    
    # Check if regional data provides specific activity levels
    if regional_data and region in regional_data:
        region_activity = regional_data[region].get('activity_level', 'low')
        if region_activity == 'high':
            base_adjustment *= 1.1
        elif region_activity == 'minimal':
            base_adjustment *= 0.9
    
    # Ensure adjustment stays within reasonable bounds
    return max(0.8, min(1.2, base_adjustment))

def _calculate_strategic_vaccination_risk(vaccination_data: Dict[str, Any], county_name: str) -> Dict[str, Any]:
    """
    Calculate strategic vaccination risk assessment for policy decision-making
    
    This framework focuses on herd immunity gaps, outbreak indicators, and school vulnerability
    to provide actionable intelligence for policymakers and public health officials.
    
    Args:
        vaccination_data: Vaccination data from Wisconsin DHS
        county_name: County name for potential county-specific adjustments
        
    Returns:
        Comprehensive vaccination risk assessment with policy indicators
    """
    if not vaccination_data:
        return _get_fallback_vaccination_risk_assessment()
    
    # Extract vaccination rates
    flu_vaccination = vaccination_data.get('flu_vaccination', {})
    covid_vaccination = vaccination_data.get('covid19_vaccination', {})
    mmr_vaccination = vaccination_data.get('mmr_vaccination', {})
    school_vaccination = vaccination_data.get('school_vaccination', {})
    
    # Current vaccination rates
    flu_rate = flu_vaccination.get('overall_population', 52.1)
    covid_rate = covid_vaccination.get('overall_coverage', 73.6)
    mmr_rate = mmr_vaccination.get('children_5_18_years', 87.8)
    school_compliance = school_vaccination.get('meeting_minimum_requirements', 86.4)
    
    # === HERD IMMUNITY GAP ANALYSIS ===
    # Critical thresholds for community protection
    herd_immunity_thresholds = {
        'mmr': 95.0,      # Measles requires 95% for herd immunity
        'flu': 70.0,      # Seasonal flu protection threshold
        'covid19': 80.0   # COVID-19 community protection threshold
    }
    
    # Calculate gaps from herd immunity
    gaps = {
        'mmr_gap': max(0, herd_immunity_thresholds['mmr'] - mmr_rate),
        'flu_gap': max(0, herd_immunity_thresholds['flu'] - flu_rate), 
        'covid19_gap': max(0, herd_immunity_thresholds['covid19'] - covid_rate),
        'school_compliance_gap': max(0, 90.0 - school_compliance)  # 90% target for schools
    }
    
    # === OUTBREAK RISK INDICATORS ===
    # Wisconsin has active measles outbreak - this significantly increases risk
    outbreak_conditions = {
        'active_measles_outbreak': True,  # Based on user context
        'below_measles_threshold': mmr_rate < 95.0,
        'school_vulnerability': school_compliance < 90.0,
        'multiple_gaps': sum(1 for gap in gaps.values() if gap > 5.0) >= 2
    }
    
    # === SCHOOL VULNERABILITY INDEX ===
    # Schools are outbreak amplifiers - special assessment needed
    school_vulnerability_score = _calculate_school_vulnerability_index(
        mmr_rate, school_compliance, outbreak_conditions['active_measles_outbreak']
    )
    
    # === STRATEGIC RISK MULTIPLIER CALCULATION ===
    # Instead of reducing risk, this increases risk when gaps are dangerous
    base_multiplier = 1.0
    
    # Major gap penalties (increase risk when below critical thresholds)
    if gaps['mmr_gap'] > 5.0:  # More than 5 points below herd immunity
        base_multiplier += gaps['mmr_gap'] * 0.04  # 4% risk increase per percentage point gap
    
    if gaps['school_compliance_gap'] > 5.0:
        base_multiplier += gaps['school_compliance_gap'] * 0.02  # 2% risk increase per point
    
    # Active outbreak emergency multiplier
    if outbreak_conditions['active_measles_outbreak'] and outbreak_conditions['below_measles_threshold']:
        base_multiplier += 0.3  # 30% emergency risk increase during active outbreak
    
    # School vulnerability emergency adjustment
    if school_vulnerability_score > 0.7:  # High school vulnerability
        base_multiplier += 0.2  # 20% additional risk for school outbreak potential
    
    # Multiple simultaneous gaps create compounding risk
    if outbreak_conditions['multiple_gaps']:
        base_multiplier += 0.15  # 15% compounding risk adjustment
    
    # Cap the multiplier to prevent extreme values
    risk_multiplier = min(2.0, max(0.7, base_multiplier))
    
    # === POLICY DECISION INDICATORS ===
    # Clear flags for decision-makers
    policy_flags = []
    
    if gaps['mmr_gap'] > 3.0:
        policy_flags.append({
            'level': 'HIGH_PRIORITY',
            'issue': 'MMR vaccination below herd immunity threshold',
            'gap': f"{gaps['mmr_gap']:.1f} percentage points below 95% threshold",
            'action_needed': 'Immediate school-based vaccination campaigns'
        })
    
    if outbreak_conditions['active_measles_outbreak']:
        policy_flags.append({
            'level': 'EMERGENCY',
            'issue': 'Active measles outbreak with inadequate population immunity',
            'gap': f"Population immunity at {mmr_rate}%, need 95% for control",
            'action_needed': 'Emergency vaccination orders, school exclusion policies'
        })
    
    if school_vulnerability_score > 0.6:
        policy_flags.append({
            'level': 'MEDIUM_PRIORITY', 
            'issue': 'School vaccination compliance below protective levels',
            'gap': f"School compliance at {school_compliance}%, target 90%+",
            'action_needed': 'Enhanced school entry requirements, compliance monitoring'
        })
    
    if gaps['flu_gap'] > 10.0:
        policy_flags.append({
            'level': 'SEASONAL_PRIORITY',
            'issue': 'Influenza vaccination below community protection threshold',
            'gap': f"{gaps['flu_gap']:.1f} percentage points below 70% threshold", 
            'action_needed': 'Targeted flu vaccination campaigns for vulnerable populations'
        })
    
    return {
        'risk_multiplier': risk_multiplier,
        'herd_immunity_gaps': gaps,
        'outbreak_conditions': outbreak_conditions,
        'school_vulnerability_score': school_vulnerability_score,
        'policy_decision_flags': policy_flags,
        'strategic_priority': _determine_strategic_priority(policy_flags),
        'framework_type': 'strategic_vaccination_risk_v2.1'
    }

def _calculate_school_vulnerability_index(mmr_rate: float, school_compliance: float, active_outbreak: bool) -> float:
    """Calculate school-specific vulnerability to disease outbreaks"""
    
    # Base vulnerability from vaccination gaps
    base_vulnerability = 0.0
    
    # MMR gap creates direct vulnerability (measles spreads rapidly in schools)
    if mmr_rate < 95.0:
        mmr_vulnerability = (95.0 - mmr_rate) / 95.0  # Normalized gap
        base_vulnerability += mmr_vulnerability * 0.6  # 60% weight for MMR gap
    
    # School compliance gap indicates systemic issues
    if school_compliance < 90.0:
        compliance_vulnerability = (90.0 - school_compliance) / 90.0
        base_vulnerability += compliance_vulnerability * 0.3  # 30% weight for compliance
    
    # Active outbreak dramatically increases school vulnerability
    if active_outbreak:
        base_vulnerability += 0.4  # 40% emergency increase
    
    # Age-based transmission amplification (schools have higher transmission)
    school_amplification_factor = 1.2
    
    final_vulnerability = min(1.0, base_vulnerability * school_amplification_factor)
    return final_vulnerability

def _determine_strategic_priority(policy_flags: List[Dict[str, str]]) -> str:
    """Determine overall strategic priority based on policy flags"""
    
    if any(flag['level'] == 'EMERGENCY' for flag in policy_flags):
        return 'EMERGENCY_RESPONSE_REQUIRED'
    elif any(flag['level'] == 'HIGH_PRIORITY' for flag in policy_flags):
        return 'HIGH_PRIORITY_INTERVENTION'
    elif any(flag['level'] == 'MEDIUM_PRIORITY' for flag in policy_flags):
        return 'TARGETED_IMPROVEMENTS_NEEDED'
    elif any(flag['level'] == 'SEASONAL_PRIORITY' for flag in policy_flags):
        return 'SEASONAL_PLANNING_FOCUS'
    else:
        return 'MAINTENANCE_MONITORING'

def _get_fallback_vaccination_risk_assessment() -> Dict[str, Any]:
    """Fallback assessment when vaccination data is unavailable"""
    return {
        'risk_multiplier': 1.2,  # Conservative increase when data unavailable
        'herd_immunity_gaps': {
            'mmr_gap': 7.2,  # Known statewide gap
            'flu_gap': 17.9,
            'covid19_gap': 6.4,
            'school_compliance_gap': 3.6
        },
        'outbreak_conditions': {
            'active_measles_outbreak': True,
            'below_measles_threshold': True,
            'school_vulnerability': True,
            'multiple_gaps': True
        },
        'school_vulnerability_score': 0.75,
        'policy_decision_flags': [{
            'level': 'HIGH_PRIORITY',
            'issue': 'Vaccination data unavailable during active outbreak conditions',
            'gap': 'Data monitoring gaps compromise outbreak response',
            'action_needed': 'Restore vaccination surveillance systems immediately'
        }],
        'strategic_priority': 'HIGH_PRIORITY_INTERVENTION',
        'framework_type': 'strategic_vaccination_risk_v2.1_fallback'
    }

def _calculate_vaccination_protection(vaccination_data: Dict[str, Any], county_name: str) -> float:
    """
    Calculate vaccination protection factor (0.0-1.0) based on vaccination rates
    
    Args:
        vaccination_data: Vaccination data from Wisconsin DHS
        county_name: County name for potential county-specific adjustments
        
    Returns:
        Protection factor (0.0 = no protection, 1.0 = maximum protection)
    """
    if not vaccination_data:
        return 0.3  # Default moderate protection when data unavailable
    
    # Extract vaccination rates
    flu_vaccination = vaccination_data.get('flu_vaccination', {})
    covid_vaccination = vaccination_data.get('covid19_vaccination', {})
    mmr_vaccination = vaccination_data.get('mmr_vaccination', {})
    school_vaccination = vaccination_data.get('school_vaccination', {})
    
    # Calculate weighted protection scores
    protection_scores = []
    
    # Flu vaccination (current season relevance)
    flu_rate = flu_vaccination.get('overall_population', 52.1) / 100.0
    protection_scores.append(flu_rate * 0.3)  # 30% weight for flu
    
    # COVID-19 vaccination
    covid_rate = covid_vaccination.get('overall_coverage', 73.6) / 100.0
    protection_scores.append(covid_rate * 0.3)  # 30% weight for COVID
    
    # MMR vaccination (community immunity)
    mmr_rate = mmr_vaccination.get('children_5_18_years', 87.8) / 100.0
    protection_scores.append(mmr_rate * 0.2)  # 20% weight for MMR
    
    # School vaccination compliance (overall herd immunity)
    school_rate = school_vaccination.get('meeting_minimum_requirements', 86.4) / 100.0
    protection_scores.append(school_rate * 0.2)  # 20% weight for school compliance
    
    # Calculate overall protection factor
    overall_protection = sum(protection_scores)
    
    # Apply county adjustments for urban vs rural vaccination patterns
    county_adjustment = _get_county_vaccination_adjustment(county_name)
    adjusted_protection = overall_protection * county_adjustment
    
    # Ensure protection factor stays within bounds
    return max(0.0, min(1.0, adjusted_protection))

def _get_county_vaccination_adjustment(county_name: str) -> float:
    """Get county-specific vaccination adjustment factor"""
    # Urban counties typically have higher vaccination rates
    urban_counties = [
        'milwaukee', 'dane', 'brown', 'racine', 'kenosha',
        'rock', 'winnebago', 'waukesha', 'outagamie'
    ]
    
    # Rural counties may have lower vaccination rates
    rural_counties = [
        'forest', 'florence', 'iron', 'vilas', 'oneida',
        'lincoln', 'langlade', 'menominee', 'taylor'
    ]
    
    county_key = county_name.lower().replace(' ', '_').replace('county', '').strip()
    
    if county_key in urban_counties:
        return 1.05  # 5% higher vaccination rates in urban areas
    elif county_key in rural_counties:
        return 0.95  # 5% lower vaccination rates in rural areas
    else:
        return 1.0   # Default for other counties

def _get_activity_level(score: float) -> str:
    """Convert a 0-1 score to an activity level string"""
    if score >= 0.6:
        return "high"
    elif score >= 0.3:
        return "moderate"
    else:
        return "low"

def _determine_overall_trend(trends: List[str]) -> str:
    """Determine overall trend from multiple trend indicators"""
    trend_counts = {
        'increasing': 0,
        'stable': 0,
        'decreasing': 0
    }
    
    for trend in trends:
        if trend in trend_counts:
            trend_counts[trend] += 1
    
    # Return the most common trend, defaulting to stable in case of ties
    if trend_counts['increasing'] > trend_counts['stable'] and trend_counts['increasing'] > trend_counts['decreasing']:
        return 'increasing'
    elif trend_counts['decreasing'] > trend_counts['stable'] and trend_counts['decreasing'] > trend_counts['increasing']:
        return 'decreasing'
    else:
        return 'stable'

def get_disease_activity(jurisdiction_id: str, disease_type: str) -> Dict[str, Any]:
    """
    Get disease activity data for a specific jurisdiction and disease type.
    
    Args:
        jurisdiction_id: The jurisdiction ID
        disease_type: The type of disease (flu, covid, rsv, etc.)
        
    Returns:
        Disease activity data dictionary
    """
    # Generate cache key
    cache_key = f"{DISEASE_CACHE_PREFIX}{disease_type}_{jurisdiction_id}"
    
    # Try memory cache first
    cached_data = get_from_memory_cache(cache_key)
    if cached_data:
        logger.debug(f"Retrieved {disease_type} data for {jurisdiction_id} from memory cache")
        return cached_data
    
    # Try persistent cache next
    cached_data = get_from_persistent_cache(cache_key, max_age_days=DISEASE_CACHE_EXPIRY)
    if cached_data:
        # Store in memory cache for faster access next time
        set_in_memory_cache(cache_key, cached_data)
        logger.debug(f"Retrieved {disease_type} data for {jurisdiction_id} from persistent cache")
        return cached_data
    
    # If not in cache, fetch from data source
    try:
        # Fetch real disease activity data from DHS for Wisconsin counties
        from utils.dhs_data import get_county_disease_data
        
        # Get county name from jurisdiction ID
        from utils.data_processor import get_county_for_jurisdiction
        county_name = get_county_for_jurisdiction(jurisdiction_id)
        
        if not county_name:
            county_name = "Milwaukee"  # Fallback to a major county if we can't determine the county
            logger.warning(f"Could not determine county for jurisdiction {jurisdiction_id}, using {county_name}")
        
        # Get disease activity data for the county
        dhs_data = get_county_disease_data(county_name, disease_type)
        
        # Format activity data
        activity_data = {
            'jurisdiction_id': jurisdiction_id,
            'disease_type': disease_type,
            'activity_level': dhs_data.get('activity_level', 'moderate'),
            'cases_per_100k': dhs_data.get('cases_per_100k', 20.0),
            'trend': dhs_data.get('trend', 'stable'),
            'last_updated': dhs_data.get('last_updated', datetime.now().isoformat()),
            'source': 'Wisconsin DHS Disease Surveillance',
            'data_quality': dhs_data.get('data_quality', 'high')
        }
        
        # Cache the data
        set_in_memory_cache(cache_key, activity_data)
        set_in_persistent_cache(cache_key, activity_data, expiry_days=DISEASE_CACHE_EXPIRY)
        
        logger.info(f"Fetched new {disease_type} data for {jurisdiction_id}")
        return activity_data
    except Exception as e:
        logger.error(f"Error fetching {disease_type} data for {jurisdiction_id}: {str(e)}")
        return {
            'jurisdiction_id': jurisdiction_id,
            'disease_type': disease_type,
            'activity_level': 'unknown',
            'error': str(e),
        }

def calculate_infectious_disease_risk(jurisdiction_id: str) -> Dict[str, Any]:
    """
    Calculate infectious disease risk for dashboard integration
    
    This function integrates the enhanced strategic vaccination risk framework
    with the existing dashboard pipeline.
    """
    # Get the county name from jurisdiction ID  
    from utils.data_processor import get_county_for_jurisdiction
    county_name = get_county_for_jurisdiction(jurisdiction_id)
    
    if not county_name:
        county_name = "Milwaukee"  # Fallback
    
    # Use the enhanced disease metrics with strategic vaccination framework
    enhanced_metrics = get_disease_metrics(county_name)
    
    # Return in the format expected by data_processor
    return enhanced_metrics

def get_disease_risk_score(jurisdiction_id: str) -> Dict[str, Any]:
    """
    Calculate overall infectious disease risk score for a jurisdiction
    based on current disease activity.
    
    Risk is calculated using:  
    - ILI Activity (30%)
    - COVID-19 Activity (30%)
    - RSV Activity (20%)
    - Vaccination Rate (20%)
    
    Args:
        jurisdiction_id: The jurisdiction ID
        
    Returns:
        Dictionary with risk scores and component data
    """
    try:
        # Get activity data for different disease types
        flu_data = get_disease_activity(jurisdiction_id, 'flu')
        covid_data = get_disease_activity(jurisdiction_id, 'covid')
        rsv_data = get_disease_activity(jurisdiction_id, 'rsv')
        
        # Calculate risk components based on real data
        # Convert cases_per_100k to a risk value between 0-1
        # Lower risk: <10 cases per 100k, Higher risk: >50 cases per 100k
        def calculate_risk_from_cases(data):
            cases = data.get('cases_per_100k', 25.0)
            # Apply a sigmoid function to normalize between 0 and 1
            # This gives a smooth transition between low and high risk
            import math
            normalized = 1.0 / (1.0 + math.exp(-0.05 * (cases - 30)))
            return max(0.1, min(0.9, normalized))  # Ensure value stays in reasonable range
        
        # Apply risk calculation to each disease type
        flu_risk = calculate_risk_from_cases(flu_data)
        covid_risk = calculate_risk_from_cases(covid_data)
        rsv_risk = calculate_risk_from_cases(rsv_data)
        
        # Get vaccination data from dhs_data module
        from utils.dhs_data import get_vaccination_rate
        county_name = get_county_for_jurisdiction(jurisdiction_id)
        
        # Handle case where county mapping is not found
        if not county_name:
            county_name = "Milwaukee"  # Default to a major county
            logger.warning(f"Could not determine county for vaccination data {jurisdiction_id}, using {county_name}")
            
        vax_rate = get_vaccination_rate(county_name)
        
        # Lower vaccination rates correspond to higher risk
        vaccination_risk = max(0.1, min(0.9, 1.0 - (vax_rate / 100.0)))
        
        # Calculate exposure, vulnerability, and resilience components for standardized risk formula
        
        # Exposure: Disease activity levels (higher activity = higher exposure)
        exposure_score = (flu_risk * 0.4) + (covid_risk * 0.4) + (rsv_risk * 0.2)
        
        # Vulnerability: Vaccination coverage (lower vaccination = higher vulnerability)
        vulnerability_score = vaccination_risk
        
        # Resilience: Based on healthcare capacity and public health preparedness
        # Use inverse of vaccination risk as a proxy for healthcare system resilience
        resilience_score = 1.0 - vaccination_risk
        
        # Apply the corrected standardized risk formula
        from utils.risk_calculation import calculate_residual_risk
        overall_risk = calculate_residual_risk(
            exposure=exposure_score,
            vulnerability=vulnerability_score,
            resilience=resilience_score,
            health_impact_factor=1.5  # Infectious disease has maximum health impacts
        )
        
        # Prepare result
        result = {
            'overall_risk': overall_risk,
            'components': {
                'flu': {
                    'risk': flu_risk,
                    'activity_level': flu_data.get('activity_level', 'unknown'),
                    'trend': flu_data.get('trend', 'unknown'),
                },
                'covid': {
                    'risk': covid_risk,
                    'activity_level': covid_data.get('activity_level', 'unknown'),
                    'trend': covid_data.get('trend', 'unknown'),
                },
                'rsv': {
                    'risk': rsv_risk,
                    'activity_level': rsv_data.get('activity_level', 'unknown'),
                    'trend': rsv_data.get('trend', 'unknown'),
                },
                'vaccination': {
                    'risk': vaccination_risk,
                    'coverage': '65%',  # Example value
                },
            },
            'last_updated': datetime.now().isoformat(),
        }
        
        return result
    except Exception as e:
        logger.error(f"Error calculating disease risk for {jurisdiction_id}: {str(e)}")
        # Return fallback with error information
        return {
            'overall_risk': 0.5,  # Moderate default
            'error': str(e),
            'last_updated': datetime.now().isoformat(),
        }

def clear_disease_cache() -> Tuple[int, int]:
    """
    Clear all disease surveillance caches (both in-memory and persistent)
    
    Returns:
        Tuple of (memory_cache_count, persistent_cache_count) entries cleared
    """
    # Clear memory cache
    memory_count = 0
    keys_to_remove = []
    
    for key in _disease_activity_cache:
        if key.startswith(DISEASE_CACHE_PREFIX):
            keys_to_remove.append(key)
            memory_count += 1
    
    for key in keys_to_remove:
        remove_from_memory_cache(key)
    
    # Clear persistent cache
    persistent_count = clear_cache_by_prefix(DISEASE_CACHE_PREFIX)
    
    logger.info(f"Cleared disease surveillance caches: {memory_count} in-memory, {persistent_count} persistent")
    return memory_count, persistent_count
