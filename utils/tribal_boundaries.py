"""
Module for integrating tribal boundaries into the risk assessment application.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
import shapely.geometry as geometry
from shapely.geometry import Point, shape

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Path to the filtered tribal boundaries GeoJSON
TRIBAL_BOUNDARIES_FILE = "data/tribal/wisconsin_tribal_boundaries_filtered.geojson"

# Dictionary mapping Tribal Nations to their jurisdiction IDs
TRIBAL_JURISDICTION_IDS = {
    "Bad River Band of Lake Superior Chippewa": "T01",
    "Forest County Potawatomi Community": "T02",
    "Ho-Chunk Nation": "T03",
    "Lac Courte Oreilles Band of Lake Superior Chippewa": "T04",
    "Lac du Flambeau Band of Lake Superior Chippewa": "T05",
    "Menominee Indian Tribe of Wisconsin": "T06",
    "Oneida Nation": "T07",
    "Red Cliff Band of Lake Superior Chippewa": "T08",
    "Sokaogon Chippewa Community (Mole Lake)": "T09",
    "St. Croix Chippewa Indians of Wisconsin": "T10",
    "Stockbridge-Munsee Community": "T11"
}

# Dictionary mapping Tribal Nation jurisdiction IDs to the counties they overlap with
TRIBAL_COUNTY_OVERLAPS = {
    "T01": ["Ashland"],               # Bad River
    "T02": ["Forest"],                # Forest County Potawatomi
    "T03": ["Jackson", "Sauk", "Wood", "Monroe", "Shawano"],  # Ho-Chunk Nation
    "T04": ["Sawyer"],                # Lac Courte Oreilles
    "T05": ["Vilas"],                 # Lac du Flambeau
    "T06": ["Menominee", "Shawano"],  # Menominee
    "T07": ["Brown", "Outagamie"],    # Oneida
    "T08": ["Bayfield"],              # Red Cliff
    "T09": ["Forest"],                # Sokaogon (Mole Lake)
    "T10": ["Burnett", "Polk"],       # St. Croix
    "T11": ["Shawano"]                # Stockbridge-Munsee
}

# Initial tribal boundaries GeoJSON for when the actual boundaries file doesn't exist
INITIAL_TRIBAL_BOUNDARIES = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-90.7, 46.5],  # Bad River approximate boundaries
                    [-90.5, 46.5],
                    [-90.5, 46.3],
                    [-90.7, 46.3],
                    [-90.7, 46.5]
                ]]
            },
            "properties": {
                "tribe": "Bad River Band of Lake Superior Chippewa",
                "jurisdiction_id": "T01"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-88.9, 45.5],  # Forest County Potawatomi approximate boundaries
                    [-88.7, 45.5],
                    [-88.7, 45.3],
                    [-88.9, 45.3],
                    [-88.9, 45.5]
                ]]
            },
            "properties": {
                "tribe": "Forest County Potawatomi Community",
                "jurisdiction_id": "T02"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-90.8, 44.3],  # Ho-Chunk approximate boundaries
                    [-90.6, 44.3],
                    [-90.6, 44.1],
                    [-90.8, 44.1],
                    [-90.8, 44.3]
                ]]
            },
            "properties": {
                "tribe": "Ho-Chunk Nation",
                "jurisdiction_id": "T03"
            }
        }
    ]
}


def initialize_tribal_boundaries():
    """
    Initialize tribal boundaries data if it doesn't exist.
    
    Creates a simplified tribal boundaries GeoJSON file with initial data
    when the processed shapefile data is not available.
    
    Returns:
        bool: True if initialization was successful
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(TRIBAL_BOUNDARIES_FILE), exist_ok=True)
    
    if not os.path.exists(TRIBAL_BOUNDARIES_FILE):
        logger.info(f"Creating initial tribal boundaries file: {TRIBAL_BOUNDARIES_FILE}")
        
        try:
            with open(TRIBAL_BOUNDARIES_FILE, 'w') as f:
                json.dump(INITIAL_TRIBAL_BOUNDARIES, f)
            logger.info(f"Created initial tribal boundaries with {len(INITIAL_TRIBAL_BOUNDARIES.get('features', []))} features")
            return True
        except Exception as e:
            logger.error(f"Error creating initial tribal boundaries: {str(e)}")
            return False
    return True

def load_tribal_boundaries():
    """
    Load the tribal boundaries from the GeoJSON file.
    
    Returns:
        dict: The GeoJSON data with tribal boundaries
    """
    # Ensure tribal boundaries file exists
    initialize_tribal_boundaries()
    
    try:
        with open(TRIBAL_BOUNDARIES_FILE, 'r') as f:
            geojson_data = json.load(f)
        
        logger.info(f"Loaded {len(geojson_data.get('features', []))} tribal boundary features")
        return geojson_data
    except Exception as e:
        logger.error(f"Error loading tribal boundaries: {str(e)}")
        # Fall back to initial data if loading fails
        return INITIAL_TRIBAL_BOUNDARIES


def get_tribal_geometries() -> Dict[str, Any]:
    """
    Get the geometries for tribal areas.
    
    Returns:
        dict: A dictionary mapping jurisdiction IDs to geometry objects
    """
    geojson_data = load_tribal_boundaries()
    if not geojson_data:
        return {}
    
    tribal_geometries = {}
    
    for feature in geojson_data.get('features', []):
        properties = feature.get('properties', {})
        tribe = properties.get('tribe')
        
        # Get the jurisdiction ID for this tribe
        jurisdiction_id = TRIBAL_JURISDICTION_IDS.get(tribe)
        if jurisdiction_id:
            # If we already have a geometry for this tribe, merge them
            try:
                if jurisdiction_id in tribal_geometries:
                    try:
                        existing_shape = shape(tribal_geometries[jurisdiction_id])
                        new_shape = shape(feature.get('geometry'))
                        merged_shape = existing_shape.union(new_shape)
                        # Handle potential errors in converting to __geo_interface__
                        try:
                            tribal_geometries[jurisdiction_id] = merged_shape.__geo_interface__
                        except Exception as geo_error:
                            logger.warning(f"Error getting geo_interface for {jurisdiction_id}, using original: {str(geo_error)}")
                            # Keep original if there's an error
                    except Exception as merge_error:
                        logger.warning(f"Error merging shapes for {jurisdiction_id}: {str(merge_error)}")
                        # Use the new geometry if we can't merge
                        tribal_geometries[jurisdiction_id] = feature.get('geometry')
                else:
                    tribal_geometries[jurisdiction_id] = feature.get('geometry')
            except Exception as e:
                logger.error(f"Error processing tribal geometry for {jurisdiction_id}: {str(e)}")
                # Skip this one if there's an error
    
    logger.info(f"Retrieved geometries for {len(tribal_geometries)} tribal jurisdictions")
    return tribal_geometries


def get_county_weights_for_tribe(jurisdiction_id: str) -> Dict[str, float]:
    """
    Get the weights for counties that a tribal area overlaps with.
    Currently using predefined weights based on known overlaps.
    
    Args:
        jurisdiction_id: The jurisdiction ID for the tribal area
        
    Returns:
        dict: A dictionary mapping county names to weights (0.0-1.0)
    """
    counties = TRIBAL_COUNTY_OVERLAPS.get(jurisdiction_id, [])
    
    if not counties:
        logger.warning(f"No county overlaps defined for tribal jurisdiction {jurisdiction_id}")
        return {}
    
    # For now, distribute weight evenly across counties
    weight_per_county = 1.0 / len(counties)
    return {county: weight_per_county for county in counties}


def overlay_analysis(tribal_jurisdiction_id: str) -> Dict[str, float]:
    """
    Perform overlay analysis to determine how much a tribal area overlaps with counties.
    This uses the predefined county overlaps for now, but could be enhanced with actual
    spatial analysis.
    
    Args:
        tribal_jurisdiction_id: The jurisdiction ID for the tribal area
        
    Returns:
        dict: A dictionary mapping county names to overlap weights (0.0-1.0)
    """
    return get_county_weights_for_tribe(tribal_jurisdiction_id)


def get_tribal_attributes(jurisdiction_id: str) -> Dict[str, Any]:
    """
    Get attributes for a tribal jurisdiction based on its boundaries and the
    counties it overlaps with.
    
    Args:
        jurisdiction_id: The tribal jurisdiction ID
        
    Returns:
        dict: A dictionary of attributes for the tribal jurisdiction
    """
    # Get the county weights for this tribe
    county_weights = get_county_weights_for_tribe(jurisdiction_id)
    
    # If no weights, return minimal data
    if not county_weights:
        return {
            "county_weights": {},
            "primary_county": None,
            "total_weight": 0.0
        }
    
    # Find the primary county (the one with the highest weight)
    primary_county = max(county_weights.items(), key=lambda x: x[1])[0]
    
    return {
        "county_weights": county_weights,
        "primary_county": primary_county,
        "total_weight": sum(county_weights.values())
    }


def calculate_tribal_risk(jurisdiction_id: str, risk_calculator_func) -> Dict[str, Any]:
    """
    Calculate risk for a tribal jurisdiction based on weighted county data.
    
    Args:
        jurisdiction_id: The tribal jurisdiction ID
        risk_calculator_func: A function that calculates risk for a county
        
    Returns:
        dict: The calculated risk data for the tribal jurisdiction
    """
    # Get county weights for this tribe
    attributes = get_tribal_attributes(jurisdiction_id)
    county_weights = attributes["county_weights"]
    
    if not county_weights:
        logger.warning(f"No county weights for tribal jurisdiction {jurisdiction_id}")
        return {}
    
    # Calculate weighted risk scores from each county
    risk_data = {}
    for county, weight in county_weights.items():
        # Get risk data for this county
        county_risk = risk_calculator_func(county)
        
        # For each risk type, calculate the weighted value
        for risk_type, score in county_risk.items():
            # Only process numerical values to avoid type issues
            if isinstance(score, (int, float)):
                if risk_type not in risk_data:
                    risk_data[risk_type] = 0.0
                risk_data[risk_type] += score * weight
    
    # Store tribal jurisdiction metadata in separate fields that won't be used in numerical calculations
    risk_data["tribal_status"] = True
    risk_data["tribal_counties"] = ','.join(county_weights.keys())
    risk_data["tribal_primary_county"] = attributes["primary_county"]
    
    # Make sure all values are float or int to avoid type errors in calculations
    for key in list(risk_data.keys()):
        if not isinstance(risk_data[key], (float, int)):
            # Skip non-numerical values in risk calculations
            if key not in ["tribal_status", "tribal_counties", "tribal_primary_county"]:
                logger.warning(f"Removing non-numerical risk factor: {key}={risk_data[key]}")
                risk_data.pop(key)
    
    return risk_data