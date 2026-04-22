"""Module for managing geographic boundary data for Wisconsin regions"""
import geopandas as gpd
import json
import os
import logging
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

def load_boundary_data(region_type: str) -> Dict:
    """
    Load GeoJSON boundary data for Wisconsin regions
    region_type: Either 'HERC' or 'WEM'
    """
    try:
        # Get the absolute path to the data directory
        data_dir = Path(__file__).parent.parent / 'data'
        boundaries_file = data_dir / f'wi_{region_type.lower()}_regions.geojson'
        
        logger.info(f"Looking for boundary file: {boundaries_file}")

        if not boundaries_file.exists():
            logger.warning(f"Boundary file not found: {boundaries_file}")
            return generate_simplified_boundaries(region_type)
        
        logger.info(f"Found boundary file: {boundaries_file}, attempting to read")
        
        # Try simple file reading first to see if the file is accessible
        try:
            with open(boundaries_file, 'r') as f:
                raw_geojson = f.read()
                logger.info(f"Successfully read boundary file, length: {len(raw_geojson)} bytes")
                # Try to directly parse as JSON instead of using geopandas
                geojson_data = json.loads(raw_geojson)
                logger.info(f"Successfully parsed GeoJSON data, found {len(geojson_data.get('features', []))} features")
                
                # Skip geopandas validation and go straight to adding styling
                for feature in geojson_data.get('features', []):
                    if 'properties' not in feature:
                        feature['properties'] = {}
                    if 'color' not in feature['properties']:
                        # Assign default colors based on region type
                        if region_type == 'HERC':
                            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#D4A5A5', '#9FA8DA', '#FFB347']
                        else:  # WEM
                            colors = ['#FF9F1C', '#2EC4B6', '#E71D36', '#011627', '#6B818C', '#BF1363']
                        feature['properties']['color'] = colors[geojson_data['features'].index(feature) % len(colors)]
                
                return geojson_data
        except Exception as file_error:
            logger.error(f"Error reading boundary file directly: {str(file_error)}")
            # Fall back to geopandas if direct JSON parsing fails
            
        # If direct JSON parsing fails, try geopandas
        try:
            logger.info("Attempting to read file with geopandas")
            gdf = gpd.read_file(str(boundaries_file))
            logger.info(f"Successfully read with geopandas, found {len(gdf)} records")
            
            # Ensure the GeoJSON is valid
            if not gdf.is_valid.all():
                logger.warning("Invalid geometries found, attempting to fix...")
                gdf = gdf.buffer(0)  # This creates valid geometries

            # Convert to standard GeoJSON format
            geojson_data = json.loads(gdf.to_json())
            logger.info(f"Successfully converted to GeoJSON format")

            # Add custom styling properties if not present
            for feature in geojson_data['features']:
                if 'properties' not in feature:
                    feature['properties'] = {}
                if 'color' not in feature['properties']:
                    # Assign default colors based on region type and index
                    if region_type == 'HERC':
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#D4A5A5', '#9FA8DA', '#FFB347']
                    else:  # WEM
                        colors = ['#FF9F1C', '#2EC4B6', '#E71D36', '#011627', '#6B818C', '#BF1363']
                    feature['properties']['color'] = colors[geojson_data['features'].index(feature) % len(colors)]

            return geojson_data

        except Exception as e:
            logger.error(f"Error processing GeoJSON file: {str(e)}")
            return generate_simplified_boundaries(region_type)

    except Exception as e:
        logger.error(f"Error loading boundary data: {str(e)}")
        return generate_simplified_boundaries(region_type)

def generate_simplified_boundaries(region_type: str) -> Dict:
    """
    Generate simplified boundary data based on official Wisconsin regional divisions.
    
    This function creates simplified GeoJSON boundary data for Wisconsin health regions
    when detailed boundary files are not available. It provides fallback geographic
    data for HERC (Health Emergency Readiness Coalition) and WEM (Wisconsin Emergency
    Management) regional boundaries.
    
    Args:
        region_type (str): Type of regional boundaries to generate.
                          Must be either 'HERC' or 'WEM'.
    
    Returns:
        Dict: GeoJSON FeatureCollection containing simplified boundary polygons
              with properties including region name, color, and county lists.
              
    Note:
        The coordinates are simplified approximations for visualization purposes.
        For precise boundary analysis, use official GeoJSON boundary files.
        
    Example:
        >>> boundaries = generate_simplified_boundaries('HERC')
        >>> print(boundaries['type'])
        'FeatureCollection'
    """
    if region_type == 'HERC':
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "name": "HERC 1",
                        "color": "#FF6B6B",
                        "counties": ["Ashland", "Bayfield", "Burnett", "Douglas", "Iron", "Price", "Rusk", "Sawyer", "Taylor", "Washburn"]
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-92.888, 46.938], # Northwest Wisconsin
                            [-91.688, 46.855],
                            [-90.623, 46.843],
                            [-90.115, 46.905],
                            [-90.118, 46.271],
                            [-90.421, 45.892],
                            [-90.129, 45.234],
                            [-91.294, 45.321],
                            [-92.359, 45.322],
                            [-92.888, 45.234],
                            [-92.888, 46.938]
                        ]]
                    }
                }
                # Additional HERC regions would be defined here
            ]
        }
    else:  # WEM regions
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "name": "WEM 1",
                        "color": "#FF9F1C",
                        "counties": ["Barron", "Chippewa", "Clark", "Dunn", "Eau Claire", "Pepin", "Pierce", "Polk", "St. Croix"]
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-92.888, 45.512], # West Central
                            [-91.852, 45.321],
                            [-90.623, 45.321],
                            [-90.512, 45.512],
                            [-90.512, 44.812],
                            [-90.623, 44.512],
                            [-90.512, 44.234],
                            [-91.294, 44.321],
                            [-92.484, 44.321],
                            [-92.888, 44.234],
                            [-92.888, 45.512]
                        ]]
                    }
                }
                # Additional WEM regions would be defined here
            ]
        }

def get_region_style(region_type: str, properties: Dict) -> Dict:
    """
    Get styling options for region boundaries in mapping visualizations.
    
    This function returns appropriate styling parameters for different regional
    boundary types when rendering maps. Different region types get distinct
    visual styling to help users differentiate between HERC and WEM boundaries.
    
    Args:
        region_type (str): Type of region ('HERC' or 'WEM')
        properties (Dict): Region properties dictionary containing color and other metadata
        
    Returns:
        Dict: Folium-compatible styling dictionary with parameters like:
              - weight: Border line thickness
              - opacity: Border line transparency  
              - color: Border color from properties
              - fillOpacity: Fill transparency
              - dashArray: Line dash pattern (differs by region type)
              - smoothFactor: Polygon smoothing factor
              
    Example:
        >>> style = get_region_style('HERC', {'color': '#FF6B6B'})
        >>> print(style['dashArray'])
        '3,5'
    """
    base_style = {
        'weight': 2,
        'opacity': 0.8,
        'color': properties.get('color', '#000000'),
        'fillOpacity': 0.2,
        'smoothFactor': 1.5
    }
    
    if region_type == 'HERC':
        base_style['dashArray'] = '3,5'
    else:  # WEM
        base_style['dashArray'] = '5,8'
    
    return base_style

def get_herc_region_boundaries() -> Dict:
    """
    Get HERC region boundary data for Wisconsin.
    Returns GeoJSON data for HERC regions.
    """
    try:
        return load_boundary_data('HERC')
    except Exception as e:
        logger.error(f"Error getting HERC region boundaries: {str(e)}")
        return generate_simplified_boundaries('HERC')

def get_wem_region_boundaries() -> Dict:
    """
    Get WEM region boundary data for Wisconsin.
    Returns GeoJSON data for WEM regions.
    """
    try:
        return load_boundary_data('WEM')
    except Exception as e:
        logger.error(f"Error getting WEM region boundaries: {str(e)}")
        return generate_simplified_boundaries('WEM')