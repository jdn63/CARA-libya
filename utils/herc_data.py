"""
HERC (Healthcare Emergency Readiness Coalition) Data Management Module

This module provides access to HERC region data, including county mappings,
healthcare facilities, and aggregate statistics for each region.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Set up logging for this module
logger = logging.getLogger(__name__)

# Define cache to store HERC region data
_herc_regions_cache = None
_herc_statistics_cache = {}

def get_all_herc_regions() -> List[Dict[str, Any]]:
    """
    Get a list of all HERC regions in Wisconsin
    
    Returns:
        List of dictionaries, each containing HERC region information
    """
    global _herc_regions_cache
    
    # Use cached data if available
    if _herc_regions_cache is not None:
        return _herc_regions_cache
    
    try:
        # Load HERC regions from data file
        herc_regions_file = os.path.join('data', 'herc', 'herc_regions.json')
        
        # If the file doesn't exist, create a directory and file with default data
        if not os.path.exists(herc_regions_file):
            logger.info("HERC regions file not found, creating with default data")
            os.makedirs(os.path.dirname(herc_regions_file), exist_ok=True)
            
            # Default HERC regions data
            default_herc_regions = [
                {
                    "id": "1",
                    "name": "HERC Region 1 (Northwest)",
                    "counties": ["Ashland", "Barron", "Bayfield", "Burnett", "Chippewa", "Douglas", "Dunn", "Eau Claire", "Pepin", "Pierce", "Polk", "Rusk", "Sawyer", "St. Croix", "Washburn"],
                    "color": "#FF9F1C"
                },
                {
                    "id": "2",
                    "name": "HERC Region 2 (North Central)",
                    "counties": ["Clark", "Forest", "Iron", "Langlade", "Lincoln", "Marathon", "Oneida", "Portage", "Price", "Taylor", "Vilas", "Wood"],
                    "color": "#2EC4B6"
                },
                {
                    "id": "3",
                    "name": "HERC Region 3 (Northeast)",
                    "counties": ["Brown", "Door", "Florence", "Kewaunee", "Manitowoc", "Marinette", "Oconto"],
                    "color": "#E71D36"
                },
                {
                    "id": "4",
                    "name": "HERC Region 4 (Western)",
                    "counties": ["Buffalo", "Crawford", "Jackson", "La Crosse", "Monroe", "Trempealeau", "Vernon"],
                    "color": "#011627"
                },
                {
                    "id": "5",
                    "name": "HERC Region 5 (South Central)",
                    "counties": ["Adams", "Columbia", "Dane", "Dodge", "Grant", "Green", "Iowa", "Jefferson", "Juneau", "Lafayette", "Marquette", "Richland", "Rock", "Sauk"],
                    "color": "#6A4C93"
                },
                {
                    "id": "6",
                    "name": "HERC Region 6 (Fox Valley)",
                    "counties": ["Calumet", "Green Lake", "Menominee", "Outagamie", "Shawano", "Waupaca", "Waushara", "Winnebago"],
                    "color": "#1982C4"
                },
                {
                    "id": "7",
                    "name": "HERC Region 7 (Southeast)",
                    "counties": ["Fond du Lac", "Kenosha", "Milwaukee", "Ozaukee", "Racine", "Sheboygan", "Walworth", "Washington", "Waukesha"],
                    "color": "#8AC926"
                }
            ]
            
            with open(herc_regions_file, 'w') as f:
                json.dump(default_herc_regions, f, indent=2)
                
            _herc_regions_cache = default_herc_regions
            return default_herc_regions
        
        # Load data from file
        with open(herc_regions_file, 'r') as f:
            herc_regions = json.load(f)
            
        # Cache the data
        _herc_regions_cache = herc_regions
        return herc_regions
        
    except Exception as e:
        logger.error(f"Error loading HERC regions: {str(e)}")
        
        # Return empty list if an error occurs
        return []

def get_herc_statistics(herc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed statistics for a specific HERC region
    
    Args:
        herc_id: ID of the HERC region
        
    Returns:
        Dictionary containing HERC region statistics including counties and healthcare capacity
    """
    global _herc_statistics_cache
    
    # Check cache
    if herc_id in _herc_statistics_cache:
        return _herc_statistics_cache[herc_id]
    
    try:
        # Get all HERC regions
        all_regions = get_all_herc_regions()
        
        # Find the specific region
        region = next((r for r in all_regions if r.get('id') == herc_id), None)
        
        if not region:
            logger.error(f"HERC region not found: {herc_id}")
            return None
        
        # Prepare statistics
        statistics_file = os.path.join('data', 'herc', f'region_{herc_id}_statistics.json')
        
        # Check if statistics file exists
        if not os.path.exists(statistics_file):
            logger.info(f"HERC region statistics file not found for region {herc_id}, creating with default data")
            os.makedirs(os.path.dirname(statistics_file), exist_ok=True)
            
            counties = region.get('counties', [])
            
            default_statistics = {}
            
            with open(statistics_file, 'w') as f:
                json.dump(default_statistics, f, indent=2)
                
            statistics = default_statistics
        else:
            # Load statistics from file
            with open(statistics_file, 'r') as f:
                statistics = json.load(f)
        
        # Combine region info with statistics
        region_data = {
            "id": region.get('id'),
            "name": region.get('name'),
            "counties": region.get('counties', []),
            "color": region.get('color'),
            "statistics": statistics
        }
        
        # Cache the data
        _herc_statistics_cache[herc_id] = region_data
        return region_data
        
    except Exception as e:
        logger.error(f"Error loading HERC region statistics for region {herc_id}: {str(e)}")
        return None

def get_county_to_herc_mapping() -> Dict[str, str]:
    """
    Get a mapping of counties to their HERC region IDs
    
    Returns:
        Dictionary mapping county names to HERC region IDs
    """
    try:
        # Get all HERC regions
        all_regions = get_all_herc_regions()
        
        # Create mapping
        county_to_herc = {}
        for region in all_regions:
            region_id = region.get('id')
            counties = region.get('counties', [])
            
            for county in counties:
                county_to_herc[county] = region_id
                
        return county_to_herc
        
    except Exception as e:
        logger.error(f"Error creating county to HERC mapping: {str(e)}")
        return {}

def get_herc_boundaries():
    """
    Get GeoJSON data for HERC regional boundaries
    
    Returns:
        GeoJSON data for HERC regions
    """
    try:
        boundaries_file = os.path.join('data', 'geojson', 'herc_boundaries.geojson')
        
        # If file doesn't exist, create a simplified version
        if not os.path.exists(boundaries_file):
            logger.info("HERC boundaries file not found, creating simplified version")
            os.makedirs(os.path.dirname(boundaries_file), exist_ok=True)
            
            # Get all HERC regions
            all_regions = get_all_herc_regions()
            
            # Create simplified GeoJSON with basic rectangular polygons
            features = []
            for i, region in enumerate(all_regions):
                region_id = region.get('id')
                name = region.get('name')
                color = region.get('color', '#' + format(hash(name) % 0xFFFFFF, '06x'))
                
                # Create a simple polygon based on region ID
                # These are just placeholders - in a real system, actual GeoJSON boundaries would be used
                region_num = int(region_id) if region_id and region_id.isdigit() else 1
                x_offset = (region_num - 1) % 4 * 2 - 4
                y_offset = (region_num - 1) // 4 * 2 - 2
                
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "color": color,
                        "region_id": region_id
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [x_offset, y_offset],
                            [x_offset + 1.5, y_offset],
                            [x_offset + 1.5, y_offset + 1.5],
                            [x_offset, y_offset + 1.5],
                            [x_offset, y_offset]
                        ]]
                    }
                }
                features.append(feature)
            
            # Create GeoJSON structure
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            with open(boundaries_file, 'w') as f:
                json.dump(geojson, f, indent=2)
                
            return geojson
        
        # Load GeoJSON from file
        with open(boundaries_file, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error loading HERC boundaries: {str(e)}")
        
        # Return empty GeoJSON on error
        return {
            "type": "FeatureCollection",
            "features": []
        }