"""
Cache Configuration Module

This module defines optimal caching strategies for different data types based on 
their update frequency and importance for real-time accuracy.
"""

from typing import Dict, Any

# Cache durations in seconds
CACHE_DURATIONS = {
    # Real-time data (no caching or very short caching)
    "current_weather": 900,      # 15 minutes - weather changes frequently
    "air_quality": 900,          # 15 minutes - AQI updates hourly
    "weather_alerts": 300,       # 5 minutes - alerts are time-sensitive
    "disease_surveillance": 1800, # 30 minutes - DHS updates throughout day
    
    # Semi-frequent data (optimized for strategic planning)
    "extreme_heat_metrics": 86400,  # 24 hours - strategic planning doesn't need hourly updates
    "heat_vulnerability": 86400 * 7, # 7 days - vulnerability changes slowly for planning purposes
    "noaa_forecast": 3600,          # 1 hour - reduced frequency for strategic context
    "nws_alerts": 1800,             # 30 minutes - less frequent for planning mode
    
    # Baseline data (optimized for annual strategic planning)
    "census_data": 86400 * 90,      # 90 days - Extended for strategic planning stability
    "svi_data": 86400 * 90,         # 90 days - Extended for consistent baseline risk assessment
    "fema_nri": 86400 * 180,        # 180 days - FEMA NRI changes slowly, suitable for annual planning
    "fbi_crime": 86400 * 30,        # 30 days - Reduced refresh for strategic baseline
    "gva_data": 86400 * 30,         # 30 days - Reduced refresh for strategic baseline
    "county_boundaries": 86400 * 180, # 180 days - Boundaries very stable
    
    # Static reference data (long-term caching)
    "tribal_boundaries": 86400 * 180, # 180 days - Very stable
    "jurisdiction_mapping": 86400 * 30, # 30 days - Stable organizational data
    "nces_schools": 86400 * 90,      # 90 days - School data updates annually
    "mobile_home_data": 86400 * 90,  # 90 days - Housing data updates annually
}

# Cache strategies by data type
CACHE_STRATEGIES = {
    "real_time": {
        "description": "For data that changes frequently and needs to be current",
        "max_age": 900,  # 15 minutes
        "data_types": ["current_weather", "air_quality", "weather_alerts"],
        "strategy": "short_term_memory_cache"
    },
    
    "semi_frequent": {
        "description": "For data that changes daily but doesn't need to be real-time",
        "max_age": 3600,  # 1 hour
        "data_types": ["extreme_heat_metrics", "heat_vulnerability", "disease_surveillance"],
        "strategy": "memory_cache_with_persistent_backup"
    },
    
    "infrequent": {
        "description": "For data that changes monthly or less frequently",
        "max_age": 86400 * 30,  # 30 days
        "data_types": ["census_data", "svi_data", "fema_nri"],
        "strategy": "persistent_cache_primary"
    },
    
    "static": {
        "description": "For reference data that rarely changes",
        "max_age": 86400 * 180,  # 180 days
        "data_types": ["tribal_boundaries", "jurisdiction_mapping"],
        "strategy": "long_term_persistent_cache"
    }
}

def get_cache_duration(data_type: str) -> int:
    """Get appropriate cache duration for a data type"""
    return CACHE_DURATIONS.get(data_type, 3600)  # Default to 1 hour

def get_cache_strategy(data_type: str) -> str:
    """Get appropriate cache strategy for a data type"""
    for strategy, config in CACHE_STRATEGIES.items():
        if data_type in config["data_types"]:
            return config["strategy"]
    return "memory_cache_with_persistent_backup"  # Default strategy

def should_use_persistent_cache(data_type: str) -> bool:
    """Determine if persistent cache should be used for this data type"""
    strategy = get_cache_strategy(data_type)
    return strategy in ["persistent_cache_primary", "long_term_persistent_cache", "memory_cache_with_persistent_backup"]

def should_refresh_immediately(data_type: str) -> bool:
    """Determine if data should be refreshed immediately on each request"""
    strategy = get_cache_strategy(data_type)
    return strategy == "short_term_memory_cache" and data_type in ["weather_alerts", "air_quality"]