"""
Social Vulnerability Index (SVI) Data Module

This module handles retrieval and processing of CDC Social Vulnerability Index data
for Wisconsin counties. The SVI data is used in risk calculations to identify communities
that may need additional support before, during, or after disasters.
"""

import json
import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Local imports
from utils.persistent_cache import get_from_persistent_cache, set_in_persistent_cache, clear_cache_by_prefix
from utils.api_key_manager import api_key_required, with_retry

# Constants
SVI_CACHE_PREFIX = "svi_data_"  # Prefix for SVI data cache keys
SVI_CACHE_EXPIRY_DAYS = 90  # SVI data changes quarterly

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Wisconsin FIPS code
WI_FIPS = "55"

# Wisconsin county FIPS codes
WI_COUNTY_FIPS = {
    "adams": "55001",
    "ashland": "55003",
    "barron": "55005",
    "bayfield": "55007",
    "brown": "55009",
    "buffalo": "55011",
    "burnett": "55013",
    "calumet": "55015",
    "chippewa": "55017",
    "clark": "55019",
    "columbia": "55021",
    "crawford": "55023",
    "dane": "55025",
    "dodge": "55027",
    "door": "55029",
    "douglas": "55031",
    "dunn": "55033",
    "eau claire": "55035",
    "florence": "55037",
    "fond du lac": "55039",
    "forest": "55041",
    "grant": "55043",
    "green": "55045",
    "green lake": "55047",
    "iowa": "55049",
    "iron": "55051",
    "jackson": "55053",
    "jefferson": "55055",
    "juneau": "55057",
    "kenosha": "55059",
    "kewaunee": "55061",
    "la crosse": "55063",
    "lafayette": "55065",
    "langlade": "55067",
    "lincoln": "55069",
    "manitowoc": "55071",
    "marathon": "55073",
    "marinette": "55075",
    "marquette": "55077",
    "menominee": "55078",
    "milwaukee": "55079",
    "monroe": "55081",
    "oconto": "55083",
    "oneida": "55085",
    "outagamie": "55087",
    "ozaukee": "55089",
    "pepin": "55091",
    "pierce": "55093",
    "polk": "55095",
    "portage": "55097",
    "price": "55099",
    "racine": "55101",
    "richland": "55103",
    "rock": "55105",
    "rusk": "55107",
    "sauk": "55111",
    "sawyer": "55113",
    "shawano": "55115",
    "sheboygan": "55117",
    "st. croix": "55109",
    "taylor": "55119",
    "trempealeau": "55121",
    "vernon": "55123",
    "vilas": "55125",
    "walworth": "55127",
    "washburn": "55129",
    "washington": "55131",
    "waukesha": "55133",
    "waupaca": "55135",
    "waushara": "55137",
    "winnebago": "55139",
    "wood": "55141"
}

# In-memory cache for frequently accessed data
_svi_data_cache = {}

def get_svi_data(county_name: str) -> Dict[str, float]:
    """
    Get Social Vulnerability Index (SVI) data for a Wisconsin county
    
    Args:
        county_name: Name of the Wisconsin county
        
    Returns:
        Dictionary with SVI data
    """
    global _svi_data_cache
    
    # Normalize county name
    county_name = county_name.strip().lower()
    
    # Check in-memory cache first
    if county_name in _svi_data_cache:
        logger.info(f"Using in-memory cached SVI data for {county_name.title()}")
        return _svi_data_cache[county_name]
    
    # Check database cache (pre-computed data from scheduled refresh)
    try:
        from utils.data_cache_manager import get_svi_from_cache
        db_cached = get_svi_from_cache(county_name)
        if db_cached:
            logger.info(f"Using database cached SVI data for {county_name.title()}")
            _svi_data_cache[county_name] = db_cached
            return db_cached
    except Exception as e:
        logger.debug(f"Database cache check failed: {e}")
    
    # Check persistent file cache
    cache_key = f"{SVI_CACHE_PREFIX}{county_name}"
    cached_data = get_from_persistent_cache(cache_key, max_age_days=SVI_CACHE_EXPIRY_DAYS)
    
    if cached_data:
        # Store in memory cache for faster access
        _svi_data_cache[county_name] = cached_data
        return cached_data
    
    # CACHE-ONLY MODE: Do not call external APIs during user requests
    # This ensures assessments never hit live endpoints
    # Data should be pre-populated by scheduled refresh jobs
    logger.warning(f"No cached SVI data available for {county_name.title()} - returning statewide default")
    
    # Return statewide average as controlled fallback
    default_data = {
        "county": county_name.title(),
        "overall": 0.5,
        "socioeconomic": 0.5,
        "household_composition": 0.5,
        "minority_status": 0.5,
        "housing_transportation": 0.5,
        "data_source": "statewide_average",
        "_cache_miss": True,
        "last_updated": datetime.now().isoformat()
    }
    
    # Store in memory cache for consistency
    _svi_data_cache[county_name] = default_data
    
    return default_data


def fetch_bulk_svi_data() -> Dict[str, Dict[str, Any]]:
    """
    Fetch CDC/ATSDR SVI 2022 data for ALL Wisconsin counties in a single
    API call. Much more efficient than 72 individual requests.

    Returns:
        Dictionary keyed by lowercase county name with SVI data for each county.
        On failure, returns an empty dict.
    """
    try:
        url = ("https://onemap.cdc.gov/OneMapServices/rest/services/SVI/"
               "CDC_ATSDR_Social_Vulnerability_Index_2022_USA/"
               "FeatureServer/1/query")
        params = {
            'where': "ST_ABBR='WI'",
            'outFields': ('FIPS,COUNTY,STATE,RPL_THEMES,RPL_THEME1,'
                          'RPL_THEME2,RPL_THEME3,RPL_THEME4,E_TOTPOP'),
            'f': 'json',
            'returnGeometry': 'false',
            'resultRecordCount': 100
        }
        logger.info("Fetching bulk CDC SVI 2022 data for all Wisconsin counties")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get('features', [])

        if not features:
            logger.warning("CDC SVI bulk query returned no features")
            return {}

        def _clean(v):
            if v is None or v == -999:
                return None
            return round(max(0, min(1, v)), 4)

        result = {}
        for feature in features:
            attrs = feature['attributes']
            county = attrs.get('COUNTY', '').replace(' County', '').strip().lower()
            if not county:
                continue
            result[county] = {
                "county": county.title(),
                "overall": _clean(attrs.get('RPL_THEMES')),
                "socioeconomic": _clean(attrs.get('RPL_THEME1')),
                "household_composition": _clean(attrs.get('RPL_THEME2')),
                "minority_status": _clean(attrs.get('RPL_THEME3')),
                "housing_transportation": _clean(attrs.get('RPL_THEME4')),
                "total_population": attrs.get('E_TOTPOP', 0),
                "fips": attrs.get('FIPS', ''),
                "data_source": "CDC/ATSDR SVI 2022",
                "last_updated": datetime.now().isoformat()
            }

        logger.info(f"Bulk SVI fetch returned data for {len(result)} counties")
        return result

    except Exception as e:
        logger.error(f"Bulk SVI fetch failed: {e}")
        return {}


def fetch_live_svi_data(county_name: str) -> Dict[str, Any]:
    """
    Fetch fresh SVI data from external API - FOR SCHEDULER USE ONLY.
    
    This function bypasses all caches and always hits the external API.
    Used by scheduled refresh jobs to populate the database cache.
    
    Args:
        county_name: Name of the Wisconsin county
        
    Returns:
        Dictionary with SVI data from API or fallback
    """
    county_name = county_name.strip().lower()
    
    try:
        county_data = fetch_real_svi_data(county_name)
        
        if not county_data:
            logger.warning(f"Could not fetch live SVI data for {county_name.title()}")
            return {
                "county": county_name.title(),
                "overall": 0.5,
                "socioeconomic": 0.5,
                "household_composition": 0.5,
                "minority_status": 0.5,
                "housing_transportation": 0.5,
                "data_source": "statewide_average",
                "_fallback": True,
                "_fallback_reason": "API returned no data",
                "last_updated": datetime.now().isoformat()
            }
        
        return county_data
        
    except Exception as e:
        logger.error(f"Error fetching live SVI data for {county_name.title()}: {str(e)}")
        return {
            "county": county_name.title(),
            "overall": 0.5,
            "socioeconomic": 0.5,
            "household_composition": 0.5,
            "minority_status": 0.5,
            "housing_transportation": 0.5,
            "data_source": "statewide_average",
            "_fallback": True,
            "_fallback_reason": str(e),
            "last_updated": datetime.now().isoformat()
        }

@with_retry(max_retries=3, base_delay=1.0)
def fetch_real_svi_data(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real Social Vulnerability Index data from CDC ArcGIS REST API
    
    Args:
        county_name: Name of the Wisconsin county
        
    Returns:
        Dictionary with SVI data from CDC, or None if failed
    """
    try:
        # Normalize county name and get FIPS code
        county_key = county_name.strip().lower()
        county_fips = WI_COUNTY_FIPS.get(county_key)
        
        if not county_fips:
            logger.error(f"No FIPS code found for county: {county_name}")
            return None
        
        # CDC SVI 2022 ArcGIS REST API endpoint - Layer 1 is county-level data
        base_url = "https://onemap.cdc.gov/OneMapServices/rest/services/SVI/CDC_ATSDR_Social_Vulnerability_Index_2022_USA/FeatureServer/1/query"
        
        # Query parameters
        params = {
            'where': f"FIPS='{county_fips}'",  # Query by county FIPS code
            'outFields': 'FIPS,COUNTY,STATE,RPL_THEMES,RPL_THEME1,RPL_THEME2,RPL_THEME3,RPL_THEME4,E_TOTPOP',
            'f': 'json',
            'returnGeometry': 'false'
        }
        
        logger.info(f"Fetching real SVI data for {county_name.title()} (FIPS: {county_fips}) from CDC API")
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'features' not in data or not data['features']:
            logger.warning(f"No SVI data returned for {county_name.title()} from CDC API")
            return None
        
        # Extract the first (and typically only) feature
        feature = data['features'][0]
        attributes = feature.get('attributes', {})
        
        # Process the CDC SVI data
        svi_data = {
            'county': county_name.title(),
            'fips': attributes.get('FIPS', county_fips),
            'data_source': 'CDC/ATSDR SVI 2022 API',
            'last_updated': datetime.now().isoformat(),
            
            # Overall SVI percentile ranking (0-1, where 1 is most vulnerable)
            'overall': attributes.get('RPL_THEMES'),
            
            # Theme-specific percentile rankings
            'socioeconomic': attributes.get('RPL_THEME1'),  # Theme 1: Socioeconomic Status
            'household_composition': attributes.get('RPL_THEME2'),  # Theme 2: Household Characteristics
            'minority_status': attributes.get('RPL_THEME3'),  # Theme 3: Racial & Ethnic Minority Status
            'housing_transportation': attributes.get('RPL_THEME4'),  # Theme 4: Housing Type & Transportation
            
            # Additional metadata
            'total_population': attributes.get('E_TOTPOP', 0),
            'state': attributes.get('STATE', 'Wisconsin')
        }
        
        # Validate the data - ensure all percentiles are valid numbers
        for key in ['overall', 'socioeconomic', 'household_composition', 'minority_status', 'housing_transportation']:
            value = svi_data[key]
            if value is None or value < 0 or value > 1:
                # Handle missing or invalid data
                if value == -999:  # CDC uses -999 for missing data
                    svi_data[key] = None
                else:
                    logger.warning(f"Invalid SVI value for {key}: {value} in {county_name.title()}")
                    if value is not None and (value < 0 or value > 1):
                        svi_data[key] = max(0, min(1, value))  # Clamp to valid range
        
        logger.info(f"Successfully fetched real SVI data for {county_name.title()} - Overall SVI: {svi_data['overall']}")
        return svi_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching SVI data for {county_name.title()}: {str(e)}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Data processing error for SVI data for {county_name.title()}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching SVI data for {county_name.title()}: {str(e)}")
        return None


def create_default_svi_data():
    """
    Populate SVI data file by fetching real CDC/ATSDR SVI 2022 data for all
    72 Wisconsin counties via the ArcGIS REST API. Falls back to statewide
    neutral defaults only if the API is unreachable.
    """
    svi_data_path = "./data/svi/wisconsin_svi_data.json"
    os.makedirs(os.path.dirname(svi_data_path), exist_ok=True)

    svi_data = {}

    try:
        url = ("https://onemap.cdc.gov/OneMapServices/rest/services/SVI/"
               "CDC_ATSDR_Social_Vulnerability_Index_2022_USA/"
               "FeatureServer/1/query")
        params = {
            'where': "ST_ABBR='WI'",
            'outFields': ('FIPS,COUNTY,STATE,RPL_THEMES,RPL_THEME1,'
                          'RPL_THEME2,RPL_THEME3,RPL_THEME4,E_TOTPOP'),
            'f': 'json',
            'returnGeometry': 'false',
            'resultRecordCount': 100
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get('features', [])

        if features:
            def _clean(v):
                if v is None or v == -999:
                    return None
                return round(max(0, min(1, v)), 4)

            for feature in features:
                attrs = feature['attributes']
                county = attrs.get('COUNTY', '').replace(' County', '').strip().lower()
                if not county:
                    continue
                svi_data[county] = {
                    "overall": _clean(attrs.get('RPL_THEMES')),
                    "socioeconomic": _clean(attrs.get('RPL_THEME1')),
                    "household_composition": _clean(attrs.get('RPL_THEME2')),
                    "minority_status": _clean(attrs.get('RPL_THEME3')),
                    "housing_transportation": _clean(attrs.get('RPL_THEME4')),
                    "total_population": attrs.get('E_TOTPOP', 0),
                    "fips": attrs.get('FIPS', ''),
                    "data_source": "CDC/ATSDR SVI 2022",
                    "last_updated": datetime.now().isoformat()
                }

            valid = [v for v in svi_data.values() if v['overall'] is not None]
            if valid:
                def _avg(key):
                    vals = [v[key] for v in valid if v.get(key) is not None]
                    return round(sum(vals) / len(vals), 4) if vals else 0.5

                svi_data["state_average"] = {
                    "overall": _avg("overall"),
                    "socioeconomic": _avg("socioeconomic"),
                    "household_composition": _avg("household_composition"),
                    "minority_status": _avg("minority_status"),
                    "housing_transportation": _avg("housing_transportation"),
                    "total_population": sum(v['total_population'] for v in valid),
                    "data_source": "CDC/ATSDR SVI 2022 (state average computed from county data)",
                    "last_updated": datetime.now().isoformat()
                }

            logger.info(f"Fetched real CDC SVI 2022 data for {len(features)} Wisconsin counties")
    except Exception as e:
        logger.warning(f"Could not fetch CDC SVI data: {e}. Using neutral statewide defaults.")

    if not svi_data:
        for county_key in WI_COUNTY_FIPS:
            svi_data[county_key] = {
                "overall": 0.5,
                "socioeconomic": 0.5,
                "household_composition": 0.5,
                "minority_status": 0.5,
                "housing_transportation": 0.5,
                "data_source": "statewide_average_fallback",
                "last_updated": datetime.now().isoformat()
            }
        svi_data["state_average"] = {
            "overall": 0.5,
            "socioeconomic": 0.5,
            "household_composition": 0.5,
            "minority_status": 0.5,
            "housing_transportation": 0.5,
            "data_source": "statewide_average_fallback",
            "last_updated": datetime.now().isoformat()
        }

    svi_data_sorted = dict(sorted(svi_data.items()))
    with open(svi_data_path, 'w') as f:
        json.dump(svi_data_sorted, f, indent=2)

    logger.info(f"Wrote SVI data file at {svi_data_path} with {len(svi_data_sorted)} entries")

def clear_svi_cache():
    """
    Clear all SVI data caches
    """
    global _svi_data_cache
    
    # Clear in-memory cache
    _svi_data_cache = {}
    
    # Clear persistent cache
    from utils.persistent_cache import clear_cache_by_prefix
    count = clear_cache_by_prefix("svi_data_")
    
    logger.info(f"Cleared SVI data cache: {count} entries removed from persistent cache")
    return count

@with_retry(max_retries=3, base_delay=1.0, backoff_factor=2.0)
def fetch_svi_data_from_api(county_fips: str) -> Optional[Dict[str, Any]]:
    """
    Fetch SVI data from CDC API with automatic retry logic
    
    Args:
        county_fips: County FIPS code (e.g., "55025" for Dane County)
        
    Returns:
        Dictionary with SVI data or None if unavailable
    """
    try:
        # CDC SVI API endpoint (example - actual endpoint may vary)
        url = f"https://www.atsdr.cdc.gov/placeandhealth/hvi/api/svi/{county_fips}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched SVI data for county {county_fips}")
        
        return {
            "overall": data.get("RPL_THEMES", 0.5),
            "socioeconomic": data.get("RPL_THEME1", 0.5),
            "household_composition": data.get("RPL_THEME2", 0.5),
            "minority_status": data.get("RPL_THEME3", 0.5),
            "housing_transportation": data.get("RPL_THEME4", 0.5),
            "last_updated": datetime.now().isoformat()
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch SVI data for county {county_fips}: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing SVI data for county {county_fips}: {e}")
        return None

def update_svi_data(county_name: str, svi_data: Dict[str, float]):
    """
    Update SVI data for a county
    
    Args:
        county_name: Name of the Wisconsin county
        svi_data: Dictionary with updated SVI data
    """
    # Normalize county name
    county_name = county_name.strip().lower()
    
    # Add timestamp
    svi_data["last_updated"] = datetime.now().isoformat()
    
    # Update data file
    svi_data_path = "./data/svi/wisconsin_svi_data.json"
    
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(svi_data_path), exist_ok=True)
        
        # Check if data file exists
        if not os.path.exists(svi_data_path):
            # Create default data with placeholder values
            create_default_svi_data()
            
        # Load existing data
        with open(svi_data_path, 'r') as f:
            all_counties_data = json.load(f)
            
        # Update county data
        all_counties_data[county_name] = svi_data
        
        # Save updated data
        with open(svi_data_path, 'w') as f:
            json.dump(all_counties_data, f, indent=2)
            
        # Update cache
        cache_key = f"{SVI_CACHE_PREFIX}{county_name}"
        set_in_persistent_cache(cache_key, svi_data, expiry_days=SVI_CACHE_EXPIRY_DAYS)
        
        # Update in-memory cache
        global _svi_data_cache
        _svi_data_cache[county_name] = svi_data
        
        logger.info(f"Updated SVI data for {county_name.title()}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating SVI data for {county_name.title()}: {str(e)}")
        return False