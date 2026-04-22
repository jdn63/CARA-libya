"""
WEM (Wisconsin Emergency Management) Data Management Module

This module provides access to WEM region data, including county mappings,
emergency management resources, and aggregate statistics for each region.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Set up logging for this module
logger = logging.getLogger(__name__)

# Define cache to store WEM region data
_wem_regions_cache = None
_wem_statistics_cache = {}

def get_all_wem_regions() -> List[Dict[str, Any]]:
    """
    Get a list of all WEM regions in Wisconsin
    
    Returns:
        List of dictionaries, each containing WEM region information
    """
    global _wem_regions_cache
    
    # Use cached data if available
    if _wem_regions_cache is not None:
        return _wem_regions_cache
    
    try:
        # Load WEM regions from data file
        wem_regions_file = os.path.join('data', 'wem', 'wem_regions.json')
        
        # If the file doesn't exist, create a directory and file with default data
        if not os.path.exists(wem_regions_file):
            logger.info("WEM regions file not found, creating with default data")
            os.makedirs(os.path.dirname(wem_regions_file), exist_ok=True)
            
            # Default WEM regions data
            default_wem_regions = [
                {
                    "id": "1",
                    "name": "WEM Region 1 - West Central",
                    "counties": ["Barron", "Buffalo", "Chippewa", "Clark", "Dunn", "Eau Claire", "Jackson", "La Crosse", "Monroe", "Pepin", "Pierce", "Polk", "Rusk", "St. Croix", "Taylor", "Trempealeau"],
                    "color": "#FF9F1C"
                },
                {
                    "id": "2",
                    "name": "WEM Region 2 - Northwest",
                    "counties": ["Ashland", "Bayfield", "Burnett", "Douglas", "Iron", "Price", "Sawyer", "Washburn"],
                    "color": "#2EC4B6"
                },
                {
                    "id": "3",
                    "name": "WEM Region 3 - North Central",
                    "counties": ["Florence", "Forest", "Langlade", "Lincoln", "Marathon", "Oneida", "Portage", "Vilas", "Wood"],
                    "color": "#E71D36"
                },
                {
                    "id": "4",
                    "name": "WEM Region 4 - Northeast",
                    "counties": ["Brown", "Calumet", "Door", "Fond du Lac", "Green Lake", "Kewaunee", "Manitowoc", "Marinette", "Marquette", "Menominee", "Oconto", "Outagamie", "Shawano", "Sheboygan", "Waupaca", "Waushara", "Winnebago"],
                    "color": "#011627"
                },
                {
                    "id": "5",
                    "name": "WEM Region 5 - Southwest",
                    "counties": ["Crawford", "Grant", "Iowa", "Juneau", "Lafayette", "Richland", "Sauk", "Vernon"],
                    "color": "#6A4C93"
                },
                {
                    "id": "6",
                    "name": "WEM Region 6 - South Central",
                    "counties": ["Adams", "Columbia", "Dane", "Dodge", "Green", "Jefferson", "Rock"],
                    "color": "#1982C4"
                },
                {
                    "id": "7",
                    "name": "WEM Region 7 - Southeast",
                    "counties": ["Kenosha", "Milwaukee", "Ozaukee", "Racine", "Walworth", "Washington", "Waukesha"],
                    "color": "#8AC926"
                }
            ]
            
            with open(wem_regions_file, 'w') as f:
                json.dump(default_wem_regions, f, indent=2)
                
            _wem_regions_cache = default_wem_regions
            return default_wem_regions
        
        # Load data from file
        with open(wem_regions_file, 'r') as f:
            wem_regions = json.load(f)
            
        # Cache the data
        _wem_regions_cache = wem_regions
        return wem_regions
        
    except Exception as e:
        logger.error(f"Error loading WEM regions: {str(e)}")
        
        # Return empty list if an error occurs
        return []

def get_wem_statistics(wem_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed statistics for a specific WEM region
    
    Args:
        wem_id: ID of the WEM region
        
    Returns:
        Dictionary containing WEM region statistics including counties and emergency resources
    """
    global _wem_statistics_cache
    
    # Check cache
    if wem_id in _wem_statistics_cache:
        return _wem_statistics_cache[wem_id]
    
    try:
        # Get all WEM regions
        all_regions = get_all_wem_regions()
        
        # Find the specific region
        region = next((r for r in all_regions if r.get('id') == wem_id), None)
        
        if not region:
            logger.error(f"WEM region not found: {wem_id}")
            return None
        
        # Prepare statistics
        statistics_file = os.path.join('data', 'wem', f'region_{wem_id}_statistics.json')
        
        # Check if statistics file exists
        if not os.path.exists(statistics_file):
            logger.info(f"WEM region statistics file not found for region {wem_id}, creating with default data")
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
        _wem_statistics_cache[wem_id] = region_data
        return region_data
        
    except Exception as e:
        logger.error(f"Error loading WEM region statistics for region {wem_id}: {str(e)}")
        return None

def get_county_to_wem_mapping() -> Dict[str, str]:
    """
    Get a mapping of counties to their WEM region IDs
    
    Returns:
        Dictionary mapping county names to WEM region IDs
    """
    try:
        # Get all WEM regions
        all_regions = get_all_wem_regions()
        
        # Create mapping
        county_to_wem = {}
        for region in all_regions:
            region_id = region.get('id')
            counties = region.get('counties', [])
            
            for county in counties:
                county_to_wem[county] = region_id
                
        return county_to_wem
        
    except Exception as e:
        logger.error(f"Error creating county to WEM mapping: {str(e)}")
        return {}