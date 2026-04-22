"""
Wisconsin City to County Mapping

This module provides mapping functionality to connect Wisconsin cities to their respective counties.
This is used to enhance GVA data processing by properly attributing city-based incidents to the
correct county jurisdiction.
"""

import logging
from typing import Dict, Optional, List, Set

# Setup logging
logger = logging.getLogger(__name__)

# Wisconsin city to county mapping
# This covers major cities and municipalities in Wisconsin
WI_CITY_TO_COUNTY = {
    # Major cities
    'madison': 'Dane',
    'milwaukee': 'Milwaukee',
    'green bay': 'Brown',
    'kenosha': 'Kenosha',
    'racine': 'Racine',
    'appleton': 'Outagamie',
    'waukesha': 'Waukesha',
    'eau claire': 'Eau Claire',
    'oshkosh': 'Winnebago',
    'janesville': 'Rock',
    'west allis': 'Milwaukee',
    'la crosse': 'La Crosse',
    'sheboygan': 'Sheboygan',
    'wauwatosa': 'Milwaukee',
    'fond du lac': 'Fond du Lac',
    'new berlin': 'Waukesha',
    'brookfield': 'Waukesha',
    'greenfield': 'Milwaukee',
    'beloit': 'Rock',
    'superior': 'Douglas',
    'stevens point': 'Portage',
    'manitowoc': 'Manitowoc',
    'oak creek': 'Milwaukee',
    'menomonee falls': 'Waukesha',
    'fitchburg': 'Dane',
    'west bend': 'Washington',
    'sun prairie': 'Dane',
    'franklin': 'Milwaukee',
    'mequon': 'Ozaukee',
    
    # Selected smaller cities
    'whitewater': 'Walworth',
    'beaver dam': 'Dodge',
    'de pere': 'Brown',
    'menasha': 'Winnebago',
    'neenah': 'Winnebago',
    'middleton': 'Dane',
    'watertown': 'Jefferson',
    'weston': 'Marathon',
    'cudahy': 'Milwaukee',
    'marshfield': 'Wood',
    'wisconsin rapids': 'Wood',
    'south milwaukee': 'Milwaukee',
    'glendale': 'Milwaukee',
    'richfield': 'Washington',
    'hartford': 'Washington',
    'oconomowoc': 'Waukesha',
    'platteville': 'Grant',
    'rhinelander': 'Oneida',
    'stoughton': 'Dane',
    'hudson': 'St. Croix',
    'monona': 'Dane',
    'baraboo': 'Sauk',
    'sturgeon bay': 'Door',
    
    # Tribal communities
    'hayward': 'Sawyer',  # Near Lac Courte Oreilles
    'keshena': 'Menominee',  # Menominee Reservation
    'odanah': 'Ashland',  # Bad River Reservation
    'bayfield': 'Bayfield',  # Red Cliff Reservation
    'crandon': 'Forest',  # Near Sokaogon Chippewa
    'black river falls': 'Jackson',  # Near Ho-Chunk areas
    'webster': 'Burnett',  # Near St. Croix Chippewa
    'lac du flambeau': 'Vilas',  # Lac du Flambeau Reservation
}

# List of all 72 Wisconsin counties for reference
WI_COUNTIES = {
    'Adams', 'Ashland', 'Barron', 'Bayfield', 'Brown', 'Buffalo', 'Burnett', 'Calumet',
    'Chippewa', 'Clark', 'Columbia', 'Crawford', 'Dane', 'Dodge', 'Door', 'Douglas',
    'Dunn', 'Eau Claire', 'Florence', 'Fond du Lac', 'Forest', 'Grant', 'Green', 'Green Lake',
    'Iowa', 'Iron', 'Jackson', 'Jefferson', 'Juneau', 'Kenosha', 'Kewaunee', 'La Crosse',
    'Lafayette', 'Langlade', 'Lincoln', 'Manitowoc', 'Marathon', 'Marinette', 'Marquette',
    'Menominee', 'Milwaukee', 'Monroe', 'Oconto', 'Oneida', 'Outagamie', 'Ozaukee', 'Pepin',
    'Pierce', 'Polk', 'Portage', 'Price', 'Racine', 'Richland', 'Rock', 'Rusk', 'Sauk',
    'Sawyer', 'Shawano', 'Sheboygan', 'St. Croix', 'Taylor', 'Trempealeau', 'Vernon', 'Vilas',
    'Walworth', 'Washburn', 'Washington', 'Waukesha', 'Waupaca', 'Waushara', 'Winnebago', 'Wood'
}

def get_county_for_city(city: str) -> Optional[str]:
    """
    Get the Wisconsin county for a given city name
    
    Args:
        city: City name (case insensitive)
        
    Returns:
        County name or None if not found
    """
    if not city:
        return None
        
    # Normalize city name
    city_normalized = city.strip().lower()
    
    # Direct lookup
    if city_normalized in WI_CITY_TO_COUNTY:
        return WI_CITY_TO_COUNTY[city_normalized]
    
    # Check for partial matches (for cities with multiple words)
    for known_city, county in WI_CITY_TO_COUNTY.items():
        if known_city in city_normalized or city_normalized in known_city:
            logger.info(f"Partial city match: '{city}' → '{known_city}' in {county} County")
            return county
    
    # Check if the input is already a county name
    for county in WI_COUNTIES:
        if county.lower() in city_normalized or city_normalized in county.lower():
            return county
            
    logger.warning(f"Could not find county for Wisconsin city: {city}")
    return None

def get_counties_for_cities(cities: List[str]) -> Set[str]:
    """
    Get a set of Wisconsin counties for a list of cities
    
    Args:
        cities: List of city names
        
    Returns:
        Set of county names
    """
    counties = set()
    for city in cities:
        county = get_county_for_city(city)
        if county:
            counties.add(county)
    return counties