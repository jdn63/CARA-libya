"""
Planning Mode Configuration Module

This module defines configuration settings optimized for different planning modes:
- Annual Strategic Planning (default): Optimized for yearly preparedness planning
- Dynamic Monitoring (advanced): Optimized for frequent tactical decision-making
"""

from typing import Dict, Any

# Planning mode configurations
PLANNING_MODES = {
    "annual_strategic": {
        "name": "Annual Strategic Planning",
        "description": "Optimized for yearly preparedness planning with stable, strategic risk focus",
        "default": True,
        "temporal_weights": {
            "baseline": 0.6,   # Emphasize structural/foundational risks
            "seasonal": 0.25,  # Enhanced seasonal preparedness guidance
            "trend": 0.15,     # Long-term awareness without noise
            "acute": 0.0       # Context only, doesn't drive strategic decisions
        },
        "cache_multipliers": {
            "real_time": 2.0,      # 2x longer caching for weather/alerts
            "semi_frequent": 8.0,   # 8x longer for heat metrics, etc.
            "baseline": 3.0,       # 3x longer for census, SVI data
            "static": 2.0          # 2x longer for boundaries, reference data
        },
        "ui_settings": {
            "show_acute_details": False,    # Minimize acute event noise
            "emphasize_seasonal": True,     # Highlight seasonal preparedness
            "show_trend_context": True,     # Show trends but don't overwhelm
            "planning_indicators": True,    # Show "Strategic Planning Mode" context
            "simplified_navigation": True   # Focus on core planning tools
        }
    },
    
    "dynamic_monitoring": {
        "name": "Dynamic Monitoring",
        "description": "Optimized for frequent monitoring with real-time event awareness",
        "default": False,
        "temporal_weights": {
            "baseline": 0.4,   # Maintain structural foundation
            "seasonal": 0.2,   # Standard seasonal awareness
            "trend": 0.2,      # Medium-term tracking
            "acute": 0.2       # Enhanced real-time response capability
        },
        "cache_multipliers": {
            "real_time": 1.0,      # Standard caching for current events
            "semi_frequent": 1.0,   # Standard refresh rates
            "baseline": 1.0,       # Standard refresh for stability
            "static": 1.0          # Standard static data refresh
        },
        "ui_settings": {
            "show_acute_details": True,     # Highlight current events
            "emphasize_seasonal": False,    # Standard seasonal display
            "show_trend_context": True,     # Enhanced trend awareness
            "planning_indicators": False,   # Show "Dynamic Mode" context
            "simplified_navigation": False  # Full navigation options
        }
    }
}

def get_planning_mode(mode_name: str = "annual_strategic") -> Dict[str, Any]:
    """
    Get configuration for specified planning mode
    
    Args:
        mode_name: Name of planning mode ("annual_strategic" or "dynamic_monitoring")
        
    Returns:
        Dictionary containing mode configuration
    """
    return PLANNING_MODES.get(mode_name, PLANNING_MODES["annual_strategic"])

def get_default_mode() -> Dict[str, Any]:
    """
    Get the default planning mode configuration
    
    Returns:
        Default mode configuration (annual_strategic)
    """
    for mode_name, config in PLANNING_MODES.items():
        if config.get("default", False):
            return config
    return PLANNING_MODES["annual_strategic"]

def apply_cache_multipliers(base_durations: Dict[str, int], mode_name: str = "annual_strategic") -> Dict[str, int]:
    """
    Apply planning mode cache multipliers to base cache durations
    
    Args:
        base_durations: Base cache durations from cache_config.py
        mode_name: Planning mode to use for multipliers
        
    Returns:
        Adjusted cache durations for the specified planning mode
    """
    mode_config = get_planning_mode(mode_name)
    multipliers = mode_config["cache_multipliers"]
    
    # Category mapping for cache duration types
    category_mapping = {
        "current_weather": "real_time",
        "air_quality": "real_time", 
        "weather_alerts": "real_time",
        "disease_surveillance": "semi_frequent",
        "extreme_heat_metrics": "semi_frequent",
        "heat_vulnerability": "semi_frequent",
        "noaa_forecast": "semi_frequent",
        "nws_alerts": "real_time",
        "census_data": "baseline",
        "svi_data": "baseline",
        "fema_nri": "baseline",
        "fbi_crime": "baseline",
        "gva_data": "baseline",
        "county_boundaries": "static",
        "tribal_boundaries": "static",
        "jurisdiction_mapping": "static",
        "nces_schools": "static",
        "mobile_home_data": "static"
    }
    
    adjusted_durations = {}
    for data_type, base_duration in base_durations.items():
        category = category_mapping.get(data_type, "semi_frequent")
        multiplier = multipliers.get(category, 1.0)
        adjusted_durations[data_type] = int(base_duration * multiplier)
    
    return adjusted_durations