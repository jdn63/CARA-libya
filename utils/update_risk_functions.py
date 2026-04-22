"""
This script updates all the risk calculation functions to include the health impact factor.
It will eventually be merged back into data_processor.py after testing.
"""
import os
import logging
import random
from typing import Dict, List, Optional, Union, Any

from utils.risk_calculation import calculate_residual_risk, get_health_impact_factor
from utils.svi_data import get_svi_data

logger = logging.getLogger(__name__)

def calculate_flood_risk_with_health_factor(county_name: str) -> dict:
    """
    Enhanced flood risk calculation with health impact factor from FEMA NRI data.
    
    Calculate multi-dimensional flood risk based on three components:
    1. Exposure: Likelihood and magnitude of flooding events
    2. Vulnerability: Population and infrastructure susceptibility
    3. Resilience: Community capacity to mitigate, respond, and recover
    
    Also incorporates health-related consequences based on FEMA NRI data.
    
    Returns a dictionary with component scores and an overall risk score.
    """
    # Check if this is a tribal jurisdiction and handle differently
    is_tribal = any(tribal_name in county_name for tribal_name in ['Ho-Chunk', 'Menominee', 'Oneida', 'Lac du Flambeau', 'Bad River', 'Red Cliff', 'Potawatomi', 'St. Croix', 'Sokaogon', 'Lac Courte Oreilles'])
    # Add special case for HoChunk variation
    is_tribal = is_tribal or 'HoChunk' in county_name
    
    # For tribal areas, map to appropriate county
    if is_tribal:
        # Find appropriate county for this tribal area
        tribal_county_mapping = {
            'HoChunk': 'Jackson',
            'Ho-Chunk': 'Jackson',
            'Menominee': 'Menominee',
            'Oneida': 'Brown',
            'Lac du Flambeau': 'Vilas',
            'Bad River': 'Ashland',
            'Red Cliff': 'Bayfield',
            'Potawatomi': 'Forest',
            'St. Croix': 'Burnett',
            'Sokaogon': 'Forest',
            'Lac Courte Oreilles': 'Sawyer'
        }
        
        mapped_county = None
        for tribal_name, mapped in tribal_county_mapping.items():
            if tribal_name in county_name:
                mapped_county = mapped
                break
                
        if mapped_county:
            logger.info(f"Using {mapped_county} County data for {county_name} flood risk")
            county_name = mapped_county
    
    # Get base flood risk from NRI data
    from utils.data_processor import load_nri_data
    county_risk = load_nri_data().get(county_name, {'flood_risk': 0.3})
    base_flood_risk = county_risk['flood_risk']
    
    # Get SVI data for vulnerability analysis
    svi_data = get_svi_data(county_name)
    housing_svi = svi_data.get('housing_transportation', 0.5)
    socioeconomic_svi = svi_data.get('socioeconomic', 0.5)
    
    # 1. EXPOSURE COMPONENT (40% of total) - Based on historical data and geographical factors
    # Higher values = higher exposure
    exposure_factors = {
        'historical_events': base_flood_risk * 0.7,  # 70% from NRI historical data
        'proximity_to_water': 0.0,                   # Will be calculated below
        'terrain_risk': 0.0,                         # Will be calculated below
        'precipitation_patterns': 0.0                # Will be calculated below
    }
    
    # Adjust for county-specific geographical factors
    river_counties = ['Buffalo', 'Crawford', 'Grant', 'La Crosse', 'Pepin', 'Pierce', 
                     'Trempealeau', 'Vernon', 'Richland', 'Sauk', 'Columbia', 'Dodge',
                     'Jefferson', 'Waukesha', 'Milwaukee', 'Racine', 'Kenosha']
    
    lake_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Florence', 
                    'Marinette', 'Oconto', 'Brown', 'Kewaunee', 'Door', 'Manitowoc',
                    'Sheboygan', 'Ozaukee', 'Milwaukee', 'Racine', 'Kenosha']
    
    flat_terrain_counties = ['Columbia', 'Dodge', 'Fond du Lac', 'Green Lake', 'Marquette',
                            'Winnebago', 'Calumet', 'Outagamie', 'Brown']
    
    high_precip_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Florence']
    
    if county_name in river_counties:
        exposure_factors['proximity_to_water'] += 0.3
    
    if county_name in lake_counties:
        exposure_factors['proximity_to_water'] += 0.2
    
    if county_name in flat_terrain_counties:
        exposure_factors['terrain_risk'] = 0.25
    else:
        # Steeper terrain can mean flash flooding but less standing water
        exposure_factors['terrain_risk'] = 0.15
    
    if county_name in high_precip_counties:
        exposure_factors['precipitation_patterns'] = 0.25
    else:
        exposure_factors['precipitation_patterns'] = 0.15
    
    # Calculate exposure score
    exposure_score = (
        (exposure_factors['historical_events'] * 0.7) +
        (exposure_factors['proximity_to_water'] * 0.15) +
        (exposure_factors['terrain_risk'] * 0.1) +
        (exposure_factors['precipitation_patterns'] * 0.05)
    )
    
    # 2. VULNERABILITY COMPONENT (35% of total) - Based on population and infrastructure susceptibility
    # Higher values = higher vulnerability
    vulnerability_score = (
        (housing_svi * 0.6) +                # 60% from housing/transportation SVI
        (socioeconomic_svi * 0.4)            # 40% from socioeconomic SVI
    )
    
    # 3. RESILIENCE COMPONENT (25% of total) - Based on community capacity and mitigation
    # Higher values = LOWER resilience (worse)
    resilience_raw = 0.5  # Base resilience score
    
    # Higher socioeconomic status correlates with better resources for flood recovery
    resilience_raw -= (socioeconomic_svi * 0.3)  # 0-0.3 reduction based on resources
    
    # Adjust for known protection infrastructure
    protected_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'Racine']
    if county_name in protected_counties:
        resilience_raw -= 0.2  # Better infrastructure reduces vulnerability
    
    # Ensure resilience_raw is between 0-1 for calculations
    resilience_raw = max(0.1, min(0.9, resilience_raw))
    
    # For risk calculation, invert resilience (higher score = higher risk)
    resilience_score = 1.0 - resilience_raw
    
    # Calculate traditional weighted risk score (for comparison/backward compatibility)
    traditional_risk = min(1.0, (
        (exposure_score * 0.4) +        # 40% exposure factors
        (vulnerability_score * 0.35) +  # 35% vulnerability factors
        (resilience_score * 0.25)       # 25% resilience factors (inverted)
    ))
    
    # Get health impact factor for flooding from FEMA NRI data
    health_factor = get_health_impact_factor(county_name, 'flood')
    
    # Calculate the new residual risk using our formula with health impact factor
    # Note: we use resilience_raw (not inverted) since the formula expects higher=better
    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )
    
    # Calculate metrics based on component scores
    metrics = {
        'historical_flood_events': int(5 + (exposure_score * 15)),       # 5-20 events in past decade
        'percent_in_floodplain': int(5 + (vulnerability_score * 25)),    # 5-30% population in floodplain
        'recovery_time_days': int(10 + (resilience_score * 50)),         # 10-60 days avg recovery
        'mitigation_projects': int(10 - (resilience_score * 7))          # 3-10 active projects (inverse)
    }
    
    return {
        'overall': residual_risk,  # Use the new residual risk as overall score
        'traditional_risk': traditional_risk,  # Keep the old calculation for reference
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,  # Raw score (not inverted) for display
            'health_impact': health_factor  # Include health impact factor in output
        },
        'metrics': metrics
    }

def calculate_tornado_risk_with_health_factor(county_name: str) -> dict:
    """
    Enhanced tornado risk calculation with health impact factor from FEMA NRI data.
    
    Calculate multi-dimensional tornado risk based on three components:
    1. Exposure: Likelihood and magnitude of tornado events
    2. Vulnerability: Population and infrastructure susceptibility 
    3. Resilience: Community capacity to respond and recover
    
    Also incorporates health-related consequences based on FEMA NRI data.
    
    Returns a dictionary with component scores and an overall risk score.
    """
    # Check if this is a tribal jurisdiction and handle differently
    is_tribal = any(tribal_name in county_name for tribal_name in ['Ho-Chunk', 'Menominee', 'Oneida', 'Lac du Flambeau', 'Bad River', 'Red Cliff', 'Potawatomi', 'St. Croix', 'Sokaogon', 'Lac Courte Oreilles'])
    # Add special case for HoChunk variation
    is_tribal = is_tribal or 'HoChunk' in county_name
    
    # For tribal areas, map to appropriate county
    if is_tribal:
        # Find appropriate county for this tribal area
        tribal_county_mapping = {
            'HoChunk': 'Jackson',
            'Ho-Chunk': 'Jackson',
            'Menominee': 'Menominee',
            'Oneida': 'Brown',
            'Lac du Flambeau': 'Vilas',
            'Bad River': 'Ashland',
            'Red Cliff': 'Bayfield',
            'Potawatomi': 'Forest',
            'St. Croix': 'Burnett',
            'Sokaogon': 'Forest',
            'Lac Courte Oreilles': 'Sawyer'
        }
        
        mapped_county = None
        for tribal_name, mapped in tribal_county_mapping.items():
            if tribal_name in county_name:
                mapped_county = mapped
                break
                
        if mapped_county:
            logger.info(f"Using {mapped_county} County data for {county_name} tornado risk")
            county_name = mapped_county
    
    # Get base tornado risk from NRI data
    from utils.data_processor import load_nri_data, get_mobile_home_percentage
    county_risk = load_nri_data().get(county_name, {'tornado_risk': 0.3})
    base_tornado_risk = county_risk['tornado_risk']
    
    # Get SVI data for vulnerability analysis
    svi_data = get_svi_data(county_name)
    housing_svi = svi_data.get('housing_transportation', 0.5)
    socioeconomic_svi = svi_data.get('socioeconomic', 0.5)
    
    # Get mobile home percentage as a key vulnerability factor for tornados
    mobile_home_pct = get_mobile_home_percentage(county_name)
    # Normalize to 0-1 range (typical US range is 0-20%)
    mobile_home_factor = min(1.0, mobile_home_pct / 20.0)
    
    # 1. EXPOSURE COMPONENT (45% of total) - Based on historical data and geographical factors
    # Higher values = higher exposure
    exposure_factors = {
        'historical_events': base_tornado_risk * 0.8,  # 80% from NRI historical data
        'tornado_alley_proximity': 0.0,              # Will be calculated below
        'terrain_factors': 0.0                       # Will be calculated below
    }
    
    # Adjust for county-specific geographical factors
    tornado_alley_counties = ['Grant', 'Iowa', 'Lafayette', 'Green', 'Rock', 'Walworth', 
                             'Jefferson', 'Waukesha', 'Dane', 'Columbia', 'Sauk']
    
    open_terrain_counties = ['Columbia', 'Dodge', 'Fond du Lac', 'Green Lake', 'Marquette',
                            'Winnebago', 'Calumet', 'Outagamie', 'Brown', 'Rock', 'Walworth']
    
    if county_name in tornado_alley_counties:
        exposure_factors['tornado_alley_proximity'] = 0.4
    else:
        # Calculate proximity based on latitude (simplified)
        exposure_factors['tornado_alley_proximity'] = 0.2
    
    if county_name in open_terrain_counties:
        exposure_factors['terrain_factors'] = 0.3
    else:
        # Hilly or forested terrain can disrupt tornado formation
        exposure_factors['terrain_factors'] = 0.1
    
    # Calculate exposure score
    exposure_score = (
        (exposure_factors['historical_events'] * 0.7) +
        (exposure_factors['tornado_alley_proximity'] * 0.2) +
        (exposure_factors['terrain_factors'] * 0.1)
    )
    
    # 2. VULNERABILITY COMPONENT (35% of total) - Based on population and infrastructure susceptibility
    # Higher values = higher vulnerability
    vulnerability_score = (
        (housing_svi * 0.4) +           # 40% from housing/transportation SVI
        (socioeconomic_svi * 0.2) +     # 20% from socioeconomic SVI  
        (mobile_home_factor * 0.4)      # 40% from mobile home density
    )
    
    # 3. RESILIENCE COMPONENT (20% of total) - Based on community capacity and mitigation
    # Higher values = BETTER resilience (lower risk)
    resilience_raw = 0.5  # Base resilience score
    
    # Higher socioeconomic status correlates with better resources for recovery
    resilience_raw += ((1.0 - socioeconomic_svi) * 0.3)  # 0-0.3 addition based on resources
    
    # Adjust for known tornado shelters and warning systems
    prepared_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'La Crosse']
    if county_name in prepared_counties:
        resilience_raw += 0.2  # Better infrastructure increases resilience
    
    # Population density affects evacuation capability
    urban_counties = ['Milwaukee', 'Dane', 'Waukesha', 'Brown', 'Racine', 'Kenosha']
    if county_name in urban_counties:
        resilience_raw -= 0.1  # Denser populations can be harder to evacuate/shelter
    
    # Ensure resilience_raw is between 0-1 for calculations
    resilience_raw = max(0.1, min(0.9, resilience_raw))
    
    # Get health impact factor for tornados from FEMA NRI data
    health_factor = get_health_impact_factor(county_name, 'tornado')
    
    # Calculate the residual risk using our formula with health impact factor
    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )
    
    # Calculate metrics based on component scores
    metrics = {
        'annual_tornado_probability': int(5 + (exposure_score * 25)),      # 5-30% annual probability
        'vulnerable_structures_pct': int(10 + (vulnerability_score * 40)), # 10-50% vulnerable structures
        'warning_lead_time_min': int(20 - (exposure_score * 15)),          # 5-20 minutes warning time
        'shelter_capacity_pct': int(40 + (resilience_raw * 50))            # 40-90% population can be sheltered
    }
    
    return {
        'overall': residual_risk,
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,  # Raw score for display
            'health_impact': health_factor
        },
        'metrics': metrics
    }

def calculate_winter_storm_risk_with_health_factor(county_name: str) -> dict:
    """
    Enhanced winter storm risk calculation with health impact factor from FEMA NRI data.
    
    Calculate multi-dimensional winter storm risk based on three components:
    1. Exposure: Likelihood and magnitude of winter storm events
    2. Vulnerability: Population and infrastructure susceptibility
    3. Resilience: Community capacity to prepare, respond, and recover
    
    Also incorporates health-related consequences based on FEMA NRI data.
    
    Returns a dictionary with component scores and an overall risk score.
    """
    # Check if this is a tribal jurisdiction and handle differently
    is_tribal = any(tribal_name in county_name for tribal_name in ['Ho-Chunk', 'Menominee', 'Oneida', 'Lac du Flambeau', 'Bad River', 'Red Cliff', 'Potawatomi', 'St. Croix', 'Sokaogon', 'Lac Courte Oreilles'])
    # Add special case for HoChunk variation
    is_tribal = is_tribal or 'HoChunk' in county_name
    
    # For tribal areas, map to appropriate county
    if is_tribal:
        # Find appropriate county for this tribal area
        tribal_county_mapping = {
            'HoChunk': 'Jackson',
            'Ho-Chunk': 'Jackson',
            'Menominee': 'Menominee',
            'Oneida': 'Brown',
            'Lac du Flambeau': 'Vilas',
            'Bad River': 'Ashland',
            'Red Cliff': 'Bayfield',
            'Potawatomi': 'Forest',
            'St. Croix': 'Burnett',
            'Sokaogon': 'Forest',
            'Lac Courte Oreilles': 'Sawyer'
        }
        
        mapped_county = None
        for tribal_name, mapped in tribal_county_mapping.items():
            if tribal_name in county_name:
                mapped_county = mapped
                break
                
        if mapped_county:
            logger.info(f"Using {mapped_county} County data for {county_name} winter storm risk")
            county_name = mapped_county
    
    # Get base winter storm risk from NRI data
    from utils.data_processor import load_nri_data, get_elderly_population_pct
    county_risk = load_nri_data().get(county_name, {'winter_storm_risk': 0.3})
    base_winter_risk = county_risk['winter_storm_risk']
    
    # Get SVI data for vulnerability analysis
    svi_data = get_svi_data(county_name)
    housing_svi = svi_data.get('housing_transportation', 0.5)
    socioeconomic_svi = svi_data.get('socioeconomic', 0.5)
    
    # Get population aged 65+ percentage as a key vulnerability factor for winter storms
    elderly_pct = get_elderly_population_pct(county_name)
    # Normalize to 0-1 range (typical US range is 10-30%)
    elderly_factor = min(1.0, max(0.1, (elderly_pct - 10) / 20.0))
    
    # 1. EXPOSURE COMPONENT (40% of total) - Based on historical data and geographical factors
    # Higher values = higher exposure
    exposure_factors = {
        'historical_events': base_winter_risk * 0.8,  # 80% from NRI historical data
        'northern_location': 0.0,                   # Will be calculated below
        'lake_effect': 0.0                         # Will be calculated below
    }
    
    # Adjust for county-specific geographical factors
    northern_counties = ['Douglas', 'Bayfield', 'Ashland', 'Iron', 'Vilas', 'Forest', 
                        'Florence', 'Marinette', 'Langlade', 'Lincoln', 'Sawyer', 
                        'Price', 'Oneida', 'Taylor', 'Rusk', 'Barron', 'Washburn', 
                        'Burnett', 'Polk', 'Chippewa']
    
    lake_effect_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Florence', 
                           'Kenosha', 'Racine', 'Milwaukee', 'Ozaukee', 'Sheboygan', 
                           'Manitowoc', 'Kewaunee', 'Door', 'Brown', 'Oconto', 'Marinette']
    
    if county_name in northern_counties:
        exposure_factors['northern_location'] = 0.6  # Northern counties get higher exposure
    elif county_name in ['Marathon', 'Clark', 'Eau Claire', 'Dunn', 'St. Croix']:
        exposure_factors['northern_location'] = 0.4  # Central-north counties
    else:
        exposure_factors['northern_location'] = 0.2  # Southern counties
    
    if county_name in lake_effect_counties:
        exposure_factors['lake_effect'] = 0.5  # Lake effect snow is significant
    else:
        exposure_factors['lake_effect'] = 0.1  # Less lake effect impact
    
    # Calculate exposure score
    exposure_score = (
        (exposure_factors['historical_events'] * 0.6) +
        (exposure_factors['northern_location'] * 0.3) +
        (exposure_factors['lake_effect'] * 0.1)
    )
    
    # 2. VULNERABILITY COMPONENT (35% of total) - Based on population and infrastructure susceptibility
    # Higher values = higher vulnerability
    vulnerability_score = (
        (housing_svi * 0.4) +           # 40% from housing/transportation SVI
        (socioeconomic_svi * 0.2) +     # 20% from socioeconomic SVI  
        (elderly_factor * 0.4)          # 40% from elderly population percentage
    )
    
    # 3. RESILIENCE COMPONENT (25% of total) - Based on community capacity and mitigation
    # Higher values = BETTER resilience (lower risk)
    resilience_raw = 0.5  # Base resilience score
    
    # Higher socioeconomic status correlates with better resources for recovery
    resilience_raw += ((1.0 - socioeconomic_svi) * 0.2)  # 0-0.2 addition based on resources
    
    # Adjust for known snow removal and emergency response capabilities
    prepared_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'La Crosse', 'Marathon']
    if county_name in prepared_counties:
        resilience_raw += 0.2  # Better infrastructure increases resilience
    
    # Northern counties typically have better winter preparedness
    if county_name in northern_counties:
        resilience_raw += 0.1  # Better winter preparedness in northern counties
    
    # Ensure resilience_raw is between 0-1 for calculations
    resilience_raw = max(0.1, min(0.9, resilience_raw))
    
    # Get health impact factor for winter storms from FEMA NRI data
    health_factor = get_health_impact_factor(county_name, 'winter_storm')
    
    # Calculate the residual risk using our formula with health impact factor
    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )
    
    # Calculate metrics based on component scores
    metrics = {
        'annual_major_storms': int(3 + (exposure_score * 10)),           # 3-13 storms per year
        'snow_removal_cost': int(500000 + (exposure_score * 1500000)),   # $500K-$2M per year
        'power_outages_annual': int(2 + (vulnerability_score * 10)),     # 2-12 weather-related outages
        'response_time_hours': int(12 - (resilience_raw * 8))            # 4-12 hour response time (inverse)
    }
    
    return {
        'overall': residual_risk,
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,  # Raw score for display
            'health_impact': health_factor
        },
        'metrics': metrics
    }