"""
Air Quality Risk Assessment Module

This module handles retrieval and processing of air quality data from the AirNow API
for Wisconsin counties. Air quality data includes AQI values, pollutant concentrations,
and health advisories used in environmental health risk calculations.
"""

import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from utils.api_key_manager import APIKeyManager, with_retry, api_key_required
from utils.persistent_cache import get_from_persistent_cache, set_in_persistent_cache
from utils.tribal_air_quality_mapping import get_tribal_coordinates, get_multi_point_coordinates, is_multi_point_jurisdiction

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Cache configuration
AIR_QUALITY_CACHE_PREFIX = "air_quality_"
AIR_QUALITY_CACHE_EXPIRY_HOURS = 1  # Air quality data changes hourly

# Wisconsin county coordinates for AirNow API calls
# Using approximate county center coordinates
WI_COUNTY_COORDINATES = {
    'adams': (44.0344, -89.7709),
    'ashland': (46.1158, -90.6718),
    'barron': (45.4036, -91.8501),
    'bayfield': (46.6108, -91.1015),
    'brown': (44.5133, -88.0133),
    'buffalo': (44.2636, -91.9040),
    'burnett': (45.8319, -92.4688),
    'calumet': (44.1858, -88.3085),
    'chippewa': (44.9358, -91.3929),
    'clark': (44.6275, -90.6643),
    'columbia': (43.4358, -89.3501),
    'crawford': (43.3108, -90.9801),
    'dane': (43.0642, -89.4012),
    'dodge': (43.4525, -88.7001),
    'door': (44.8694, -87.2734),
    'douglas': (46.6108, -92.0957),
    'dunn': (44.9525, -91.9040),
    'eau_claire': (44.6275, -91.4929),
    'florence': (45.9219, -88.1668),
    'fond_du_lac': (43.7730, -88.4476),
    'forest': (45.6719, -88.9168),
    'grant': (42.8608, -90.7179),
    'green': (42.6858, -89.6001),
    'green_lake': (43.8441, -89.0168),
    'iowa': (43.0358, -90.1501),
    'iron': (46.2608, -90.1668),
    'jackson': (44.3358, -90.8179),
    'jefferson': (43.0025, -88.8001),
    'juneau': (43.9025, -90.0168),
    'kenosha': (42.5847, -87.8212),
    'kewaunee': (44.4525, -87.5734),
    'la_crosse': (43.8319, -91.0790),
    'lafayette': (42.5358, -90.4001),
    'langlade': (45.1719, -89.0668),
    'lincoln': (45.4036, -89.7168),
    'manitowoc': (44.0886, -87.6148),
    'marathon': (44.9025, -89.6334),
    'marinette': (45.1719, -87.7301),
    'marquette': (43.7358, -89.5168),
    'menominee': (44.8858, -88.6334),
    'milwaukee': (43.0389, -87.9065),
    'monroe': (43.9691, -90.6374),
    'oconto': (44.8858, -88.1334),
    'oneida': (45.7036, -89.5334),
    'outagamie': (44.4858, -88.4085),
    'ozaukee': (43.3997, -87.8876),
    'pepin': (44.4358, -92.1501),
    'pierce': (44.7358, -92.6334),
    'polk': (45.4036, -92.6334),
    'portage': (44.4858, -89.5001),
    'price': (45.7036, -90.3334),
    'racine': (42.7261, -87.7829),
    'richland': (43.3358, -90.3851),
    'rock': (42.6858, -89.0751),
    'rusk': (45.4036, -91.1260),
    'st_croix': (44.9858, -92.6334),
    'sauk': (43.4691, -89.9501),
    'sawyer': (45.9036, -91.1260),
    'shawano': (44.7858, -88.6085),
    'sheboygan': (43.7508, -87.7148),
    'taylor': (45.4036, -90.4501),
    'trempealeau': (44.2691, -91.4260),
    'vernon': (43.6358, -90.7851),
    'vilas': (46.1719, -89.6334),
    'walworth': (42.6191, -88.5751),
    'washburn': (45.8319, -91.7793),
    'washington': (43.3997, -88.2376),
    'waukesha': (43.0119, -88.2315),
    'waupaca': (44.3525, -89.0835),
    'waushara': (44.1191, -89.2501),
    'winnebago': (44.0258, -88.5585),
    'wood': (44.3691, -90.1001)
}

# AQI categories and risk scoring
AQI_CATEGORIES = {
    'good': {'min': 0, 'max': 50, 'risk_score': 0.1, 'color': '#00E400'},
    'moderate': {'min': 51, 'max': 100, 'risk_score': 0.3, 'color': '#FFFF00'},
    'unhealthy_sensitive': {'min': 101, 'max': 150, 'risk_score': 0.6, 'color': '#FF7E00'},
    'unhealthy': {'min': 151, 'max': 200, 'risk_score': 0.8, 'color': '#FF0000'},
    'very_unhealthy': {'min': 201, 'max': 300, 'risk_score': 0.9, 'color': '#8F3F97'},
    'hazardous': {'min': 301, 'max': 500, 'risk_score': 1.0, 'color': '#7E0023'}
}

# In-memory cache for frequently accessed data
_air_quality_cache = {}


def get_air_quality_risk(county_name: str) -> Dict[str, Any]:
    """
    Get air quality risk assessment for a Wisconsin county or tribal jurisdiction
    
    Args:
        county_name: Name of the Wisconsin county or tribal jurisdiction ID
        
    Returns:
        Dictionary with air quality risk data
    """
    global _air_quality_cache
    
    # Normalize county name
    county_name = county_name.strip().lower()
    
    # Check in-memory cache first
    if county_name in _air_quality_cache:
        logger.info(f"Using in-memory cached air quality data for {county_name.title()}")
        return _air_quality_cache[county_name]
    
    # Check database cache (pre-computed data from scheduled refresh)
    try:
        from utils.data_cache_manager import get_air_quality_from_cache
        db_cached = get_air_quality_from_cache(county_name)
        if db_cached:
            logger.info(f"Using database cached air quality data for {county_name.title()}")
            _air_quality_cache[county_name] = db_cached
            return db_cached
    except Exception as e:
        logger.debug(f"Database cache check failed: {e}")
    
    # Check persistent file cache
    cache_key = f"{AIR_QUALITY_CACHE_PREFIX}{county_name}"
    # Convert hours to days for the cache function (ensure it's an int)
    cache_days = int(AIR_QUALITY_CACHE_EXPIRY_HOURS / 24.0) or 1
    cached_data = get_from_persistent_cache(cache_key, max_age_days=cache_days)
    
    if cached_data:
        # Store in memory cache for faster access
        _air_quality_cache[county_name] = cached_data
        return cached_data
    
    # CACHE-ONLY MODE: Do not call external APIs during user requests
    # This ensures assessments never hit live endpoints
    # Data should be pre-populated by scheduled refresh jobs
    logger.warning(f"No cached air quality data available for {county_name.title()} - returning statewide baseline")
    
    # Return strategic planning baseline as controlled fallback
    default_data = {
        "county": county_name.title(),
        "strategic_assessment": "moderate_concern",
        "risk_score": 0.50,  # Statewide baseline
        "data_source": "statewide_baseline",
        "_cache_miss": True,
        "climate_projections": {
            "ozone_increase": "40% by 2050",
            "wildfire_smoke": "110% increase in episodes"
        },
        "planning_horizon": "2025-2050",
        "last_updated": datetime.now().isoformat()
    }
    
    # Store in memory cache for consistency
    _air_quality_cache[county_name] = default_data
    
    return default_data


def fetch_live_air_quality_data(county_name: str) -> Dict[str, Any]:
    """
    Fetch fresh air quality data from external sources - FOR SCHEDULER USE ONLY.
    
    This function bypasses all caches and always hits the external sources.
    Used by scheduled refresh jobs to populate the database cache.
    
    Args:
        county_name: Name of the Wisconsin county
        
    Returns:
        Dictionary with air quality data from APIs or fallback
    """
    county_name = county_name.strip().lower()
    
    try:
        # Use strategic air quality module for consistent long-term data
        from utils.strategic_air_quality import get_strategic_air_quality_assessment
        
        air_quality_data = get_strategic_air_quality_assessment(county_name)
        
        if air_quality_data:
            return air_quality_data
        
        # Fallback if strategic assessment fails
        logger.warning(f"Could not fetch live air quality data for {county_name.title()}")
        return {
            "county": county_name.title(),
            "strategic_assessment": "moderate_concern",
            "risk_score": 0.50,
            "data_source": "statewide_baseline",
            "_fallback": True,
            "_fallback_reason": "Strategic assessment returned no data",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching live air quality data for {county_name.title()}: {str(e)}")
        return {
            "county": county_name.title(),
            "strategic_assessment": "moderate_concern",
            "risk_score": 0.50,
            "data_source": "statewide_baseline",
            "_fallback": True,
            "_fallback_reason": str(e),
            "last_updated": datetime.now().isoformat()
        }


@api_key_required('AIRNOW_API_KEY')
@with_retry(max_retries=2, base_delay=1.0)
def fetch_multi_point_air_quality_data(jurisdiction_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch air quality data from multiple points for geographically distributed tribal jurisdictions
    
    Args:
        jurisdiction_id: Tribal jurisdiction ID (e.g., 'T03')
        
    Returns:
        Dictionary with weighted average air quality data from multiple points
    """
    try:
        multi_points = get_multi_point_coordinates(jurisdiction_id)
        if not multi_points:
            logger.error(f"No multi-point coordinates found for jurisdiction: {jurisdiction_id}")
            return None
        
        # Get API key
        api_manager = APIKeyManager()
        api_key = api_manager.get_api_key('AIRNOW_API_KEY')
        
        if not api_key:
            logger.error("AirNow API key not available")
            return None
        
        air_quality_samples = []
        total_weight = 0
        
        for lat, lon, weight in multi_points:
            try:
                # AirNow API endpoint for current conditions
                base_url = "https://www.airnowapi.org/aq/observation/latLong/current/"
                
                # Query parameters
                params = {
                    'format': 'application/json',
                    'latitude': lat,
                    'longitude': lon,
                    'distance': 25,  # Search within 25 miles
                    'API_KEY': api_key
                }
                
                logger.info(f"Fetching air quality data for {jurisdiction_id} point (lat: {lat}, lon: {lon}, weight: {weight})")
                
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data:
                    processed_data = process_airnow_data(data, f"{jurisdiction_id}_point")
                    if processed_data and processed_data.get('aqi') is not None:
                        air_quality_samples.append({
                            'data': processed_data,
                            'weight': weight,
                            'coordinates': (lat, lon)
                        })
                        total_weight += weight
                        logger.info(f"Successfully collected AQI {processed_data.get('aqi')} from point ({lat:.3f}, {lon:.3f})")
                
            except Exception as e:
                logger.warning(f"Failed to get air quality data for point ({lat}, {lon}): {str(e)}")
                continue
        
        if not air_quality_samples:
            logger.error(f"No valid air quality data collected for {jurisdiction_id}")
            return None
        
        # Calculate weighted averages
        weighted_aqi = 0
        weighted_risk_score = 0
        pollutant_totals = {}
        
        for sample in air_quality_samples:
            data = sample['data']
            weight = sample['weight']
            
            if data.get('aqi') is not None:
                weighted_aqi += data['aqi'] * weight
            
            weighted_risk_score += data.get('risk_score', 0.5) * weight
            
            # Aggregate pollutant data
            for pollutant, value in data.get('pollutants', {}).items():
                if pollutant not in pollutant_totals:
                    pollutant_totals[pollutant] = 0
                pollutant_totals[pollutant] += value * weight
        
        # Normalize by total weight
        if total_weight > 0:
            final_aqi = int(weighted_aqi / total_weight)
            final_risk_score = weighted_risk_score / total_weight
            
            final_pollutants = {}
            for pollutant, total in pollutant_totals.items():
                final_pollutants[pollutant] = total / total_weight
        else:
            logger.error(f"Total weight is zero for {jurisdiction_id}")
            return None
        
        # Determine category and color from final AQI
        category, _, color = get_aqi_category_and_risk(final_aqi)
        
        logger.info(f"Multi-point air quality for {jurisdiction_id}: AQI {final_aqi} ({category}) from {len(air_quality_samples)} sample points")
        
        return {
            "jurisdiction": jurisdiction_id,
            "aqi": final_aqi,
            "category": category,
            "risk_score": final_risk_score,
            "color": color,
            "pollutants": final_pollutants,
            "sample_points": len(air_quality_samples),
            "sampling_method": "weighted_multi_point",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in multi-point air quality sampling for {jurisdiction_id}: {str(e)}")
        return None


@api_key_required('AIRNOW_API_KEY')
@with_retry(max_retries=3, base_delay=1.0)
def fetch_air_quality_data(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch current air quality data from AirNow API
    
    Args:
        county_name: Name of the Wisconsin county or tribal jurisdiction ID
        
    Returns:
        Dictionary with air quality data from AirNow API, or None if failed
    """
    try:
        # Get coordinates for county or tribal jurisdiction
        county_key = county_name.strip().lower()
        coordinates = None
        
        # Check if it's a tribal jurisdiction (starts with 'T' when uppercase)
        if county_key.upper().startswith('T'):
            jurisdiction_id = county_key.upper()
            
            # Check if this jurisdiction requires multi-point sampling
            if is_multi_point_jurisdiction(jurisdiction_id):
                return fetch_multi_point_air_quality_data(jurisdiction_id)
            
            coordinates = get_tribal_coordinates(jurisdiction_id)
            if coordinates:
                logger.info(f"Using tribal coordinates for {jurisdiction_id}: {coordinates}")
        else:
            # Regular county lookup
            coordinates = WI_COUNTY_COORDINATES.get(county_key)
        
        if not coordinates:
            logger.error(f"No coordinates found for location: {county_name}")
            return None
        
        lat, lon = coordinates
        
        # Get API key
        api_manager = APIKeyManager()
        api_key = api_manager.get_api_key('AIRNOW_API_KEY')
        
        if not api_key:
            logger.error("AirNow API key not available")
            return None
        
        # AirNow API endpoint for current conditions
        base_url = "https://www.airnowapi.org/aq/observation/latLong/current/"
        
        # Query parameters
        params = {
            'format': 'application/json',
            'latitude': lat,
            'longitude': lon,
            'distance': 25,  # Search within 25 miles
            'API_KEY': api_key
        }
        
        logger.info(f"Fetching air quality data for {county_name.title()} (lat: {lat}, lon: {lon}) from AirNow API")
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            logger.warning(f"No air quality data returned for {county_name.title()} from AirNow API")
            return None
        
        # Process the AirNow data
        processed_data = process_airnow_data(data, county_name)
        
        if processed_data:
            logger.info(f"Successfully fetched air quality data for {county_name.title()} - AQI: {processed_data.get('aqi', 'N/A')}")
            return processed_data
        else:
            logger.warning(f"Failed to process air quality data for {county_name.title()}")
            return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching air quality data for {county_name.title()}: {str(e)}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Data processing error for air quality data for {county_name.title()}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching air quality data for {county_name.title()}: {str(e)}")
        return None


def process_airnow_data(raw_data: List[Dict], county_name: str) -> Optional[Dict[str, Any]]:
    """
    Process raw AirNow API response into structured air quality data
    
    Args:
        raw_data: Raw response from AirNow API
        county_name: Name of the county
        
    Returns:
        Processed air quality data dictionary
    """
    if not raw_data:
        return None
    
    try:
        # Group data by pollutant
        pollutants = {}
        max_aqi = 0
        primary_pollutant = None
        
        for observation in raw_data:
            parameter = observation.get('ParameterName', '')
            aqi = observation.get('AQI', 0)
            concentration = observation.get('Value', 0)
            unit = observation.get('Unit', '')
            date_observed = observation.get('DateObserved', '')
            hour_observed = observation.get('HourObserved', '')
            
            # Store pollutant data
            pollutants[parameter] = {
                'aqi': aqi,
                'concentration': concentration,
                'unit': unit,
                'date_observed': date_observed,
                'hour_observed': hour_observed
            }
            
            # Track the highest AQI value
            if aqi > max_aqi:
                max_aqi = aqi
                primary_pollutant = parameter
        
        # Determine AQI category and risk score
        category, risk_score, color = get_aqi_category_and_risk(max_aqi)
        
        # Create comprehensive air quality assessment
        air_quality_data = {
            'county': county_name.title(),
            'aqi': max_aqi,
            'category': category,
            'risk_score': risk_score,
            'color': color,
            'primary_pollutant': primary_pollutant,
            'pollutants': pollutants,
            'data_source': 'AirNow API',
            'last_updated': datetime.now().isoformat(),
            'observation_count': len(raw_data)
        }
        
        return air_quality_data
        
    except Exception as e:
        logger.error(f"Error processing AirNow data for {county_name}: {str(e)}")
        return None


def get_aqi_category_and_risk(aqi: int) -> Tuple[str, float, str]:
    """
    Determine AQI category, risk score, and color based on AQI value
    
    Args:
        aqi: Air Quality Index value
        
    Returns:
        Tuple of (category, risk_score, color)
    """
    for category, info in AQI_CATEGORIES.items():
        if info['min'] <= aqi <= info['max']:
            return category, info['risk_score'], info['color']
    
    # For values outside normal range
    if aqi > 500:
        return 'hazardous', 1.0, '#7E0023'
    else:
        return 'good', 0.1, '#00E400'


def get_air_quality_forecast(county_name: str) -> Dict[str, Any]:
    """
    Get air quality forecast data for a Wisconsin county
    
    Args:
        county_name: Name of the Wisconsin county
        
    Returns:
        Dictionary with air quality forecast data
    """
    # This would use the AirNow forecast endpoint
    # For now, return current conditions with a note
    current_data = get_air_quality_risk(county_name)
    
    forecast_data = {
        'county': county_name.title(),
        'current': current_data,
        'forecast': {
            'today': current_data,
            'tomorrow': None,  # Would fetch from forecast endpoint
            'note': 'Forecast data available via AirNow forecast API'
        },
        'last_updated': datetime.now().isoformat()
    }
    
    return forecast_data


def clear_air_quality_cache():
    """
    Clear all air quality data caches
    """
    global _air_quality_cache
    
    # Clear in-memory cache
    _air_quality_cache.clear()
    
    # Clear persistent cache
    from utils.persistent_cache import clear_cache_by_prefix
    cleared_count = clear_cache_by_prefix(AIR_QUALITY_CACHE_PREFIX)
    
    logger.info(f"Cleared air quality cache: {cleared_count} entries removed from persistent cache")


def update_air_quality_data(county_name: str, air_quality_data: Dict[str, Any]):
    """
    Update air quality data for a county
    
    Args:
        county_name: Name of the Wisconsin county
        air_quality_data: Dictionary with updated air quality data
    """
    county_key = county_name.strip().lower()
    
    # Update in-memory cache
    global _air_quality_cache
    _air_quality_cache[county_key] = air_quality_data
    
    # Update persistent cache
    cache_key = f"{AIR_QUALITY_CACHE_PREFIX}{county_key}"
    # Convert hours to days for the cache function (ensure it's an int)
    cache_days = int(AIR_QUALITY_CACHE_EXPIRY_HOURS / 24.0) or 1
    set_in_persistent_cache(cache_key, air_quality_data, expiry_days=cache_days)
    
    logger.info(f"Updated air quality data for {county_name.title()}")


def get_air_quality_summary() -> Dict[str, Any]:
    """
    Get summary of air quality conditions across Wisconsin
    
    Returns:
        Dictionary with statewide air quality summary
    """
    # This would aggregate data from multiple counties
    # For now, return a basic summary structure
    summary = {
        'state': 'Wisconsin',
        'data_source': 'AirNow API',
        'last_updated': datetime.now().isoformat(),
        'summary': 'Air quality monitoring across Wisconsin counties',
        'available_counties': len(WI_COUNTY_COORDINATES),
        'monitoring_stations': 'Variable by county'
    }
    
    return summary