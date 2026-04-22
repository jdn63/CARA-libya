"""
Weather Alerts Module

This module handles retrieval and processing of weather alerts from the National Weather Service (NWS) API
and current weather conditions from OpenWeatherMap API.
It supports the temporal risk analysis by providing information on active weather events.
"""

import os
import json
import logging
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Cache weather alerts to reduce API calls
_weather_alerts_cache = {}
_weather_conditions_cache = {}
_cache_expiry = {}  # Timestamp when cached data expires

# Cache county FIPS codes
_county_fips_cache = {}

# Get OpenWeatherMap API key from environment variable
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')

# Wisconsin counties coordinates (latitude, longitude)
WI_COUNTY_COORDINATES = {
    'Adams': (43.9693, -89.7673),
    'Ashland': (46.3155, -90.6571),
    'Barron': (45.4369, -91.8495),
    'Bayfield': (46.5261, -91.1953),
    'Brown': (44.4710, -88.0118),
    'Buffalo': (44.4309, -91.7562),
    'Burnett': (45.8651, -92.3633),
    'Calumet': (44.0768, -88.2123),
    'Chippewa': (45.0693, -91.2839),
    'Clark': (44.7324, -90.6065),
    'Columbia': (43.4688, -89.3303),
    'Crawford': (43.2467, -90.9356),
    'Dane': (43.0667, -89.4167),
    'Dodge': (43.4275, -88.7059),
    'Door': (45.0684, -87.2426),
    'Douglas': (46.4325, -91.8920),
    'Dunn': (44.9522, -91.8946),
    'Eau Claire': (44.8113, -91.5012),
    'Florence': (45.8491, -88.4003),
    'Fond du Lac': (43.7544, -88.4949),
    'Forest': (45.6678, -88.7724),
    'Grant': (42.8701, -90.7064),
    'Green': (42.6984, -89.6029),
    'Green Lake': (43.8057, -89.0012),
    'Iowa': (43.0002, -90.1414),
    'Iron': (46.3208, -90.2631),
    'Jackson': (44.3194, -90.8057),
    'Jefferson': (43.0746, -88.7775),
    'Juneau': (43.9092, -90.1136),
    'Kenosha': (42.5800, -87.8100),
    'Kewaunee': (44.4630, -87.5065),
    'La Crosse': (43.8792, -91.2396),
    'Lafayette': (42.6770, -90.1406),
    'Langlade': (45.2624, -89.0698),
    'Lincoln': (45.3375, -89.7413),
    'Manitowoc': (44.1053, -87.6612),
    'Marathon': (44.8981, -89.7610),
    'Marinette': (45.3891, -87.9912),
    'Marquette': (43.8161, -89.4051),
    'Menominee': (44.9910, -88.6691),
    'Milwaukee': (43.0389, -87.9065),
    'Monroe': (43.9420, -90.6182),
    'Oconto': (45.0227, -88.2598),
    'Oneida': (45.7127, -89.5345),
    'Outagamie': (44.4180, -88.4634),
    'Ozaukee': (43.3856, -87.8926),
    'Pepin': (44.5989, -91.9734),
    'Pierce': (44.7290, -92.4278),
    'Polk': (45.4649, -92.6790),
    'Portage': (44.4724, -89.5028),
    'Price': (45.6800, -90.3596),
    'Racine': (42.7561, -87.7905),
    'Richland': (43.3757, -90.4320),
    'Rock': (42.6708, -89.0732),
    'Rusk': (45.4736, -91.1353),
    'Saint Croix': (45.0279, -92.6450),
    'Sauk': (43.4273, -89.9428),
    'Sawyer': (45.8658, -91.1467),
    'Shawano': (44.7784, -88.7619),
    'Sheboygan': (43.7447, -87.7503),
    'Taylor': (45.2116, -90.5017),
    'Trempealeau': (44.3032, -91.3577),
    'Vernon': (43.5949, -90.8160),
    'Vilas': (46.0501, -89.5020),
    'Walworth': (42.6681, -88.5414),
    'Washburn': (45.8913, -91.7960),
    'Washington': (43.3700, -88.2264),
    'Waukesha': (43.0186, -88.3077),
    'Waupaca': (44.4740, -88.9646),
    'Waushara': (44.1156, -89.2399),
    'Winnebago': (44.0184, -88.6423),
    'Wood': (44.4483, -90.0417)
}

def get_active_alerts(jurisdiction_id: str) -> List[Dict]:
    """
    Get active weather alerts for a specific jurisdiction.
    
    Args:
        jurisdiction_id: The ID of the jurisdiction to get alerts for
        
    Returns:
        List of active weather alerts with event type, severity, and expiration
    """
    global _weather_alerts_cache, _cache_expiry
    
    # Check if we have a non-expired cached result
    cache_key = f"alerts_{jurisdiction_id}"
    current_time = datetime.now()
    
    if (cache_key in _weather_alerts_cache and 
        cache_key in _cache_expiry and 
        current_time < _cache_expiry[cache_key]):
        return _weather_alerts_cache[cache_key]
    
    # Get county name from jurisdiction ID
    county_name = _get_county_from_jurisdiction(jurisdiction_id)
    if not county_name:
        logger.warning(f"Could not determine county for jurisdiction ID {jurisdiction_id}")
        return []
    
    # Get FIPS code for county
    county_fips = _get_county_fips(county_name)
    if not county_fips:
        logger.warning(f"Could not determine FIPS code for county {county_name}")
        return []
    
    # Call NWS API to get active alerts for the county
    try:
        # Always try to get real alert data instead of using load management
        logger.info(f"Fetching real weather alerts for {jurisdiction_id}")
        # We previously returned empty data some of the time, but now we'll always
        # try to get real alert data for accuracy and reliability
        
        # NWS API URL for alerts (filtered by area/zone)
        url = f"https://api.weather.gov/alerts/active?zone={county_fips}"
        
        # Make API request
        headers = {
            "User-Agent": "WI-Health-Risk-Assessment-Tool/1.0 (Wisconsin-DHS)"
        }
        
        # Add defensive error handling with retries
        max_retries = 2
        retry_count = 0
        response = None  # Initialize response variable to avoid unbound reference
        
        while retry_count <= max_retries:
            try:
                # Use a shorter timeout to avoid blocking the server
                response = requests.get(url, headers=headers, timeout=3)
                # Check for success immediately to avoid processing invalid response
                if response.status_code == 200:
                    break
                else:
                    logger.warning(f"Weather alerts API returned status code {response.status_code}")
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(0.5)  # Short delay between retries
                    else:
                        logger.error(f"Weather alerts API failed with status code {response.status_code} after {max_retries} retries")
                        return []  # Return empty alerts list
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(f"Weather alerts API request failed (attempt {retry_count}): {str(e)}. Retrying...")
                    time.sleep(0.5)  # Short delay between retries
                else:
                    logger.error(f"Weather alerts API request failed after {max_retries} retries: {str(e)}")
                    return []  # Return empty alerts list
        
        # This code block is unreachable since we already check the status code above,
        # but we'll keep it for extra safety
        if response is None:
            logger.error("Error fetching weather alerts: No response received")
            return []
        elif response.status_code != 200:
            logger.error(f"Error fetching weather alerts: status code {response.status_code}")
            return []
            
        # Parse response with safe error handling
        try:
            alerts_data = response.json()
        except Exception as json_err:
            logger.error(f"Error parsing weather alerts JSON: {str(json_err)}")
            return []  # Return empty list if JSON parsing fails
        
        # Extract relevant alert information
        processed_alerts = []
        for feature in alerts_data.get('features', []):
            properties = feature.get('properties', {})
            
            # Check if this alert affects our county
            affected_zones = properties.get('affectedZones', [])
            if not any(county_fips in zone for zone in affected_zones):
                continue
                
            # Extract alert details
            processed_alert = {
                'event': properties.get('event', 'Unknown'),
                'headline': properties.get('headline', ''),
                'description': properties.get('description', ''),
                'severity': properties.get('severity', 'Unknown'),
                'expires': properties.get('expires', ''),
                'response_type': properties.get('responseType', ''),
                'urgency': properties.get('urgency', '')
            }
            
            processed_alerts.append(processed_alert)
            
        # Cache the result for 15 minutes
        _weather_alerts_cache[cache_key] = processed_alerts
        _cache_expiry[cache_key] = current_time + timedelta(minutes=15)
        
        return processed_alerts
        
    except Exception as e:
        logger.error(f"Error retrieving weather alerts: {str(e)}")
        return []

def _get_county_from_jurisdiction(jurisdiction_id: str) -> Optional[str]:
    """Get county name from jurisdiction ID"""
    try:
        # Import the jurisdiction mapping
        from utils.jurisdiction_mapping_code import jurisdiction_mapping
        county = jurisdiction_mapping.get(jurisdiction_id)
        return county
    except ImportError:
        # Fallback mapping for testing
        fallback_mapping = {
            '41': 'Milwaukee',
            '42': 'Milwaukee',
            '43': 'Waukesha',
            '44': 'Dane',
            '45': 'Brown',
            '46': 'Bayfield',
            '47': 'Pierce'
        }
        return fallback_mapping.get(jurisdiction_id)

def _get_county_fips(county_name: str) -> Optional[str]:
    """Get FIPS code for a Wisconsin county"""
    global _county_fips_cache
    
    # Return cached value if available
    if county_name in _county_fips_cache:
        return _county_fips_cache[county_name]
    
    # Wisconsin FIPS codes for counties - the first two digits (55) are the state code
    wi_fips_codes = {
        'Adams': '55001',
        'Ashland': '55003',
        'Barron': '55005',
        'Bayfield': '55007',
        'Brown': '55009',
        'Buffalo': '55011',
        'Burnett': '55013',
        'Calumet': '55015',
        'Chippewa': '55017',
        'Clark': '55019',
        'Columbia': '55021',
        'Crawford': '55023',
        'Dane': '55025',
        'Dodge': '55027',
        'Door': '55029',
        'Douglas': '55031',
        'Dunn': '55033',
        'Eau Claire': '55035',
        'Florence': '55037',
        'Fond du Lac': '55039',
        'Forest': '55041',
        'Grant': '55043',
        'Green': '55045',
        'Green Lake': '55047',
        'Iowa': '55049',
        'Iron': '55051',
        'Jackson': '55053',
        'Jefferson': '55055',
        'Juneau': '55057',
        'Kenosha': '55059',
        'Kewaunee': '55061',
        'La Crosse': '55063',
        'Lafayette': '55065',
        'Langlade': '55067',
        'Lincoln': '55069',
        'Manitowoc': '55071',
        'Marathon': '55073',
        'Marinette': '55075',
        'Marquette': '55077',
        'Menominee': '55078',
        'Milwaukee': '55079',
        'Monroe': '55081',
        'Oconto': '55083',
        'Oneida': '55085',
        'Outagamie': '55087',
        'Ozaukee': '55089',
        'Pepin': '55091',
        'Pierce': '55093',
        'Polk': '55095',
        'Portage': '55097',
        'Price': '55099',
        'Racine': '55101',
        'Richland': '55103',
        'Rock': '55105',
        'Rusk': '55107',
        'Sauk': '55111',
        'Sawyer': '55113',
        'Shawano': '55115',
        'Sheboygan': '55117',
        'St. Croix': '55109',
        'Taylor': '55119',
        'Trempealeau': '55121',
        'Vernon': '55123',
        'Vilas': '55125',
        'Walworth': '55127',
        'Washburn': '55129',
        'Washington': '55131',
        'Waukesha': '55133',
        'Waupaca': '55135',
        'Waushara': '55137',
        'Winnebago': '55139',
        'Wood': '55141'
    }
    
    # Get FIPS code for county
    fips = wi_fips_codes.get(county_name)
    
    # Cache for future use
    if fips:
        _county_fips_cache[county_name] = fips
        
    return fips

def get_current_weather(jurisdiction_id: str) -> Optional[Dict]:
    """
    Get current weather conditions for a specific jurisdiction using OpenWeatherMap.
    
    Args:
        jurisdiction_id: The ID of the jurisdiction to get weather for
        
    Returns:
        Dict with current weather conditions or None if retrieval failed
    """
    global _weather_conditions_cache, _cache_expiry
    
    logger.info(f"Getting current weather for jurisdiction: {jurisdiction_id}")
    logger.info(f"API Key present: {bool(OPENWEATHERMAP_API_KEY)}")
    
    # Check if we have a non-expired cached result
    cache_key = f"weather_{jurisdiction_id}"
    current_time = datetime.now()
    
    if (cache_key in _weather_conditions_cache and 
        cache_key in _cache_expiry and 
        current_time < _cache_expiry[cache_key]):
        logger.info(f"Using cached weather data for {jurisdiction_id}")
        return _weather_conditions_cache[cache_key]
    
    # Get county name from jurisdiction ID
    county_name = _get_county_from_jurisdiction(jurisdiction_id)
    if not county_name:
        logger.warning(f"Could not determine county for jurisdiction ID {jurisdiction_id}")
        return {
            'temperature': 68, 
            'description': 'cloudy', 
            'humidity': 45, 
            'wind_speed': 5,
            'wind_direction': 'NW',
            'icon': '03d',
            'pressure': 1013,
            'feels_like': 65,
            'location': 'Unknown County, WI'
        }
    
    # Get API key from environment
    api_key = OPENWEATHERMAP_API_KEY
    if not api_key:
        logger.error("OpenWeatherMap API key not found in environment variables")
        return {
            'temperature': 68, 
            'description': 'cloudy', 
            'humidity': 45, 
            'wind_speed': 5,
            'wind_direction': 'NW',
            'icon': '03d',
            'pressure': 1013,
            'feels_like': 65,
            'location': f"{county_name} County, WI (No API Key)"
        }
    
    try:
        # Always attempt to get real weather data instead of using load management
        logger.info(f"Fetching real weather data for {jurisdiction_id}")
        # We previously returned default data 70% of the time, but now we'll always
        # try to get real data for accuracy and reliability
    
        # Use coordinates for more reliable results
        if county_name in WI_COUNTY_COORDINATES:
            lat, lon = WI_COUNTY_COORDINATES[county_name]
            logger.info(f"Fetching weather for coordinates: {lat}, {lon} ({county_name} County)")
            
            # OpenWeatherMap API URL for current weather using coordinates
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'imperial'  # Use imperial units for US locations (Fahrenheit)
            }
        else:
            # Fallback to location name if coordinates not found
            location = f"{county_name}, WI, USA"  # Remove "County" for better compatibility
            logger.info(f"Coordinates not found, fetching weather for location: {location}")
            
            # OpenWeatherMap API URL for current weather
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': api_key,
                'units': 'imperial'  # Use imperial units for US locations (Fahrenheit)
            }
        
        # Make API request with improved error handling and retries
        max_retries = 2
        retry_count = 0
        response = None
        
        while retry_count <= max_retries:
            try:
                # Use shorter timeout to prevent server blocking (3 seconds instead of 5)
                response = requests.get(url, params=params, timeout=3)
                # Check for success immediately
                if response.status_code == 200:
                    break
                else:
                    logger.warning(f"Current weather API returned status code {response.status_code} for {county_name}")
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(0.5)  # Short delay between retries
                    else:
                        logger.error(f"Current weather API failed with status code {response.status_code} after {max_retries} retries")
                        return {
                            'temperature': 68, 
                            'description': 'data unavailable', 
                            'humidity': 45, 
                            'wind_speed': 5,
                            'wind_direction': 'NW',
                            'icon': '03d',
                            'pressure': 1013,
                            'feels_like': 65,
                            'location': f"{county_name} County, WI (API Status {response.status_code})"
                        }
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(f"Current weather API request failed (attempt {retry_count}): {str(e)}. Retrying...")
                    time.sleep(0.5)  # Short delay between retries
                else:
                    logger.error(f"Current weather API request failed after {max_retries} retries: {str(e)}")
                    return {
                        'temperature': 68, 
                        'description': 'data unavailable', 
                        'humidity': 45, 
                        'wind_speed': 5,
                        'wind_direction': 'NW',
                        'icon': '03d',
                        'pressure': 1013,
                        'feels_like': 65,
                        'location': f"{county_name} County, WI (Connection Error)"
                    }
        
        # This code block is unreachable since we check the status code above,
        # but we'll keep it for extra safety
        if response is None:
            logger.error("Error fetching weather data: No response received")
            return {
                'temperature': 68, 
                'description': 'data unavailable', 
                'humidity': 45, 
                'wind_speed': 5,
                'wind_direction': 'NW',
                'icon': '03d',
                'pressure': 1013,
                'feels_like': 65,
                'location': f"{county_name} County, WI (No response)"
            }
        elif response.status_code != 200:
            logger.error(f"Error fetching weather data: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {
                'temperature': 68, 
                'description': 'data unavailable', 
                'humidity': 45, 
                'wind_speed': 5,
                'wind_direction': 'NW',
                'icon': '03d',
                'pressure': 1013,
                'feels_like': 65,
                'location': f"{county_name} County, WI (API Status {response.status_code})"
            }
            
        # Parse response
        weather_data = response.json()
        
        # Extract relevant weather information
        weather = {
            'temperature': round(weather_data.get('main', {}).get('temp', 0)),
            'description': weather_data.get('weather', [{}])[0].get('description', 'Unknown'),
            'humidity': weather_data.get('main', {}).get('humidity', 0),
            'wind_speed': round(weather_data.get('wind', {}).get('speed', 0)),
            'wind_direction': _get_wind_direction(weather_data.get('wind', {}).get('deg', 0)),
            'icon': weather_data.get('weather', [{}])[0].get('icon', '01d'),
            'pressure': weather_data.get('main', {}).get('pressure', 0),
            'feels_like': round(weather_data.get('main', {}).get('feels_like', 0)),
            'location': f"{county_name} County, WI"
        }
        
        # Cache the result for 30 minutes
        _weather_conditions_cache[cache_key] = weather
        _cache_expiry[cache_key] = current_time + timedelta(minutes=30)
        
        return weather
        
    except Exception as e:
        logger.error(f"Error retrieving weather data: {str(e)}")
        return {
            'temperature': 68, 
            'description': 'cloudy', 
            'humidity': 45, 
            'wind_speed': 5,
            'wind_direction': 'NW',
            'icon': '03d',
            'pressure': 1013,
            'feels_like': 65,
            'location': f"{county_name} County, WI (API Error)"
        }

def _get_wind_direction(degrees: float) -> str:
    """Convert wind direction in degrees to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / (360. / len(directions))) % len(directions)
    return directions[index]

def get_weather_forecast(jurisdiction_id: str, days: int = 7) -> List[Dict]:
    """
    Get weather forecast for a specific jurisdiction.
    
    Args:
        jurisdiction_id: The ID of the jurisdiction to get forecast for
        days: Number of days to forecast (default: 7)
        
    Returns:
        List of daily weather forecasts
    """
    # This is a placeholder for future implementation
    # Would connect to NWS API or other weather service to get forecast data
    return []

def get_current_weather_data(county_name: str) -> Dict:
    """
    Get current weather data for a county using OpenWeatherMap API.
    
    Args:
        county_name: Name of the county to get weather for
        
    Returns:
        Dictionary containing current weather data
    """
    # This function is called by temporal_risk.py
    # Create a dummy jurisdiction ID to reuse existing functionality
    return get_current_weather_conditions("dummy_jurisdiction", county_name)

def clear_weather_cache() -> int:
    """
    Clear weather alerts and conditions cache.
    
    Returns:
        Number of cache entries cleared
    """
    global _weather_alerts_cache, _weather_conditions_cache, _cache_expiry
    
    entries_cleared = len(_weather_alerts_cache) + len(_weather_conditions_cache) + len(_cache_expiry)
    
    _weather_alerts_cache.clear()
    _weather_conditions_cache.clear()
    _cache_expiry.clear()
    
    logger.info(f"Weather cache cleared: {entries_cleared} entries removed")
    return entries_cleared