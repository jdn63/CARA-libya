"""
GIS Export Utilities for CARA Risk Assessment Data

This module provides functionality to export jurisdiction-level risk scores
to CSV and GeoJSON formats for use in ArcGIS and other GIS platforms.
"""

import json
import csv
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import geopandas as gpd
import pandas as pd
from utils.tribal_boundaries import load_tribal_boundaries, TRIBAL_JURISDICTION_IDS

logger = logging.getLogger(__name__)

class CARAGISExporter:
    """
    Exports CARA risk assessment data to GIS-compatible formats.
    """
    
    def __init__(self):
        self.exports_dir = Path('exports')
        self.exports_dir.mkdir(exist_ok=True)
        
        # Load Wisconsin jurisdiction geometries (county/city)
        self.county_geojson_path = 'attached_assets/Wisconsin_Local_Public_Health_Department_Office_Boundaries.geojson'
        # Tribal boundaries path
        self.tribal_geojson_path = 'data/tribal/wisconsin_tribal_boundaries_filtered.geojson'
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def _load_jurisdiction_geometries(self) -> Optional[gpd.GeoDataFrame]:
        """Load county/city jurisdiction geometries from GeoJSON file."""
        try:
            if os.path.exists(self.county_geojson_path):
                gdf = gpd.read_file(self.county_geojson_path)
                logger.info(f"Loaded {len(gdf)} county/city jurisdiction geometries")
                return gdf
            else:
                logger.warning(f"County/city GeoJSON file not found: {self.county_geojson_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading county/city geometries: {e}")
            return None
    
    def _load_tribal_geometries(self) -> Optional[gpd.GeoDataFrame]:
        """Load tribal jurisdiction geometries from GeoJSON file."""
        try:
            if os.path.exists(self.tribal_geojson_path):
                gdf = gpd.read_file(self.tribal_geojson_path)
                # Some tribes have multiple disconnected territories, resulting in duplicate rows
                # Group by tribe name and dissolve geometries to merge disconnected territories
                if 'tribe' in gdf.columns:
                    gdf = gdf.dissolve(by='tribe', as_index=False)
                logger.info(f"Loaded {len(gdf)} unique tribal jurisdiction geometries")
                return gdf
            else:
                logger.warning(f"Tribal GeoJSON file not found: {self.tribal_geojson_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading tribal geometries: {e}")
            return None
    
    def _get_county_fips_code(self, county_name: str) -> Optional[str]:
        """Get FIPS code for a Wisconsin county."""
        # Wisconsin FIPS codes for counties
        wi_fips = {
            'Adams': '55001', 'Ashland': '55003', 'Barron': '55005', 'Bayfield': '55007',
            'Brown': '55009', 'Buffalo': '55011', 'Burnett': '55013', 'Calumet': '55015',
            'Chippewa': '55017', 'Clark': '55019', 'Columbia': '55021', 'Crawford': '55023',
            'Dane': '55025', 'Dodge': '55027', 'Door': '55029', 'Douglas': '55031',
            'Dunn': '55033', 'Eau Claire': '55035', 'Florence': '55037', 'Fond du Lac': '55039',
            'Forest': '55041', 'Grant': '55043', 'Green': '55045', 'Green Lake': '55047',
            'Iowa': '55049', 'Iron': '55051', 'Jackson': '55053', 'Jefferson': '55055',
            'Juneau': '55057', 'Kenosha': '55059', 'Kewaunee': '55061', 'La Crosse': '55063',
            'Lafayette': '55065', 'Langlade': '55067', 'Lincoln': '55069', 'Manitowoc': '55071',
            'Marathon': '55073', 'Marinette': '55075', 'Marquette': '55077', 'Menominee': '55078',
            'Milwaukee': '55079', 'Monroe': '55081', 'Oconto': '55083', 'Oneida': '55085',
            'Outagamie': '55087', 'Ozaukee': '55089', 'Pepin': '55091', 'Pierce': '55093',
            'Polk': '55095', 'Portage': '55097', 'Price': '55099', 'Racine': '55101',
            'Richland': '55103', 'Rock': '55105', 'Rusk': '55107', 'Sauk': '55111',
            'Sawyer': '55113', 'Shawano': '55115', 'Sheboygan': '55117', 'St. Croix': '55109',
            'Taylor': '55119', 'Trempealeau': '55121', 'Vernon': '55123', 'Vilas': '55125',
            'Walworth': '55127', 'Washburn': '55129', 'Washington': '55131', 'Waukesha': '55133',
            'Waupaca': '55135', 'Waushara': '55137', 'Winnebago': '55139', 'Wood': '55141'
        }
        return wi_fips.get(county_name)
    
    def _get_jurisdiction_centroid(self, county_name: str) -> Dict[str, float]:
        """Get approximate centroid coordinates for a jurisdiction."""
        # Approximate centroids for Wisconsin counties (lat, lon)
        centroids = {
            'Adams': {'lat': 43.9706, 'lon': -89.7709}, 'Ashland': {'lat': 46.4848, 'lon': -90.8838},
            'Barron': {'lat': 45.3763, 'lon': -91.8489}, 'Bayfield': {'lat': 46.7394, 'lon': -91.0298},
            'Brown': {'lat': 44.4663, 'lon': -88.0034}, 'Buffalo': {'lat': 44.2433, 'lon': -91.8404},
            'Burnett': {'lat': 45.8344, 'lon': -92.4687}, 'Calumet': {'lat': 44.2042, 'lon': -88.3192},
            'Chippewa': {'lat': 44.9377, 'lon': -91.3929}, 'Clark': {'lat': 44.7588, 'lon': -90.7354},
            'Columbia': {'lat': 43.4550, 'lon': -89.4309}, 'Crawford': {'lat': 43.3300, 'lon': -90.9709},
            'Dane': {'lat': 43.0642, 'lon': -89.4012}, 'Dodge': {'lat': 43.4450, 'lon': -88.7717},
            'Door': {'lat': 44.8858, 'lon': -87.2743}, 'Douglas': {'lat': 46.6544, 'lon': -91.9304},
            'Dunn': {'lat': 44.9377, 'lon': -91.9007}, 'Eau Claire': {'lat': 44.6358, 'lon': -91.2365},
            'Florence': {'lat': 45.9663, 'lon': -88.1881}, 'Fond du Lac': {'lat': 43.7730, 'lon': -88.4451},
            'Forest': {'lat': 45.6941, 'lon': -88.6318}, 'Grant': {'lat': 42.9289, 'lon': -90.8181},
            'Green': {'lat': 42.6358, 'lon': -89.6065}, 'Green Lake': {'lat': 43.8413, 'lon': -88.9642},
            'Iowa': {'lat': 43.0347, 'lon': -90.1184}, 'Iron': {'lat': 46.2677, 'lon': -90.1690},
            'Jackson': {'lat': 44.3441, 'lon': -90.8151}, 'Jefferson': {'lat': 43.0038, 'lon': -88.8076},
            'Juneau': {'lat': 43.9663, 'lon': -90.0396}, 'Kenosha': {'lat': 42.5969, 'lon': -87.8285},
            'Kewaunee': {'lat': 44.4566, 'lon': -87.5692}, 'La Crosse': {'lat': 43.8533, 'lon': -91.2396},
            'Lafayette': {'lat': 42.5586, 'lon': -90.1507}, 'Langlade': {'lat': 45.1691, 'lon': -89.0318},
            'Lincoln': {'lat': 45.4030, 'lon': -89.7348}, 'Manitowoc': {'lat': 44.1989, 'lon': -87.6887},
            'Marathon': {'lat': 44.9018, 'lon': -89.6315}, 'Marinette': {'lat': 45.4269, 'lon': -87.7303},
            'Marquette': {'lat': 43.7663, 'lon': -89.1801}, 'Menominee': {'lat': 44.8802, 'lon': -88.6318},
            'Milwaukee': {'lat': 43.0642, 'lon': -87.9073}, 'Monroe': {'lat': 44.0377, 'lon': -90.6396},
            'Oconto': {'lat': 45.0377, 'lon': -88.1318}, 'Oneida': {'lat': 45.7030, 'lon': -89.4348},
            'Outagamie': {'lat': 44.4808, 'lon': -88.6318}, 'Ozaukee': {'lat': 43.4097, 'lon': -87.8854},
            'Pepin': {'lat': 44.4377, 'lon': -92.1507}, 'Pierce': {'lat': 44.7377, 'lon': -92.6318},
            'Polk': {'lat': 45.4377, 'lon': -92.4318}, 'Portage': {'lat': 44.4663, 'lon': -89.4642},
            'Price': {'lat': 45.7030, 'lon': -90.4348}, 'Racine': {'lat': 42.7261, 'lon': -87.7890},
            'Richland': {'lat': 43.3663, 'lon': -90.3881}, 'Rock': {'lat': 42.6692, 'lon': -89.0776},
            'Rusk': {'lat': 45.5691, 'lon': -91.1318}, 'Sauk': {'lat': 43.5455, 'lon': -89.9709},
            'Sawyer': {'lat': 45.9691, 'lon': -91.1318}, 'Shawano': {'lat': 44.7808, 'lon': -88.6318},
            'Sheboygan': {'lat': 43.7548, 'lon': -87.7165}, 'St. Croix': {'lat': 45.1377, 'lon': -92.6318},
            'Taylor': {'lat': 45.2691, 'lon': -90.4348}, 'Trempealeau': {'lat': 44.1377, 'lon': -91.4396},
            'Vernon': {'lat': 43.6663, 'lon': -90.7881}, 'Vilas': {'lat': 46.0030, 'lon': -89.4348},
            'Walworth': {'lat': 42.6358, 'lon': -88.5776}, 'Washburn': {'lat': 45.9691, 'lon': -91.7318},
            'Washington': {'lat': 43.3847, 'lon': -88.2342}, 'Waukesha': {'lat': 43.0118, 'lon': -88.2318},
            'Waupaca': {'lat': 44.3808, 'lon': -89.0942}, 'Waushara': {'lat': 44.1286, 'lon': -89.2420},
            'Winnebago': {'lat': 44.0264, 'lon': -88.5451}, 'Wood': {'lat': 44.4377, 'lon': -90.0318}
        }
        return centroids.get(county_name, {'lat': 44.5, 'lon': -89.5})  # Default to Wisconsin center
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export jurisdiction risk data to CSV format.
        
        Args:
            data: List of jurisdiction risk data dictionaries
            filename: Optional custom filename
            
        Returns:
            Path to the created CSV file
        """
        if not filename:
            filename = f'cara_risk_scores_{self.timestamp}.csv'
        
        csv_path = self.exports_dir / filename
        
        if not data:
            logger.warning("No data to export to CSV")
            return str(csv_path)
        
        # Define field order for CSV
        fieldnames = [
            'jurisdiction_id', 'jurisdiction', 'county', 'fips_code',
            'total_risk_score', 'residual_risk',
            'exposure', 'vulnerability', 'resilience', 'health_impact_factor',
            'natural_hazards_risk', 'health_risk', 'active_shooter_risk',
            'extreme_heat_risk', 'air_quality_risk', 'cybersecurity_risk', 'utilities_risk',
            'flood_risk', 'tornado_risk', 'winter_storm_risk', 'thunderstorm_risk',
            'lat', 'lon', 'calculation_timestamp', 'framework_version', 'data_source'
        ]
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Successfully exported {len(data)} records to CSV: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def export_to_geojson(self, data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export jurisdiction risk data to GeoJSON format with geometries.
        
        Uses deterministic mapping table for reliable polygon matching,
        with fuzzy string matching as fallback only.
        
        Args:
            data: List of jurisdiction risk data dictionaries
            filename: Optional custom filename
            
        Returns:
            Path to the created GeoJSON file
        """
        if not filename:
            filename = f'cara_risk_scores_{self.timestamp}.geojson'
        
        geojson_path = self.exports_dir / filename
        
        if not data:
            logger.warning("No data to export to GeoJSON")
            return str(geojson_path)
        
        # Import boundary mapping for deterministic matching
        from utils.boundary_mapping import (
            get_boundary_objectid, 
            get_tribal_boundary_name, 
            is_tribal_jurisdiction
        )
        
        # Load both county/city and tribal geometries
        county_geometries_gdf = self._load_jurisdiction_geometries()
        tribal_geometries_gdf = self._load_tribal_geometries()
        
        features = []
        matched_county = 0
        matched_tribal = 0
        matched_by_mapping = 0
        matched_by_fuzzy = 0
        unmatched = 0
        
        for record in data:
            try:
                # Create properties (exclude lat/lon from properties since they'll be in geometry)
                properties = {k: v for k, v in record.items() if k not in ['lat', 'lon']}
                
                jurisdiction_id = str(record.get('jurisdiction_id', ''))
                jurisdiction_name = record.get('jurisdiction', '')
                
                # Try to find matching geometry
                geometry = None
                match_method = None
                
                # Check if this is a tribal jurisdiction
                if is_tribal_jurisdiction(jurisdiction_id):
                    # Use mapping table for tribal boundaries
                    if tribal_geometries_gdf is not None:
                        tribal_name = get_tribal_boundary_name(jurisdiction_id)
                        
                        if tribal_name:
                            # Try exact match using mapping table
                            if 'tribe' in tribal_geometries_gdf.columns:
                                matching_rows = tribal_geometries_gdf[
                                    tribal_geometries_gdf['tribe'].str.upper() == tribal_name.upper()
                                ]
                                
                                # Try partial match if exact fails
                                if matching_rows.empty:
                                    matching_rows = tribal_geometries_gdf[
                                        tribal_geometries_gdf['tribe'].apply(
                                            lambda x: tribal_name.upper() in x.upper() if pd.notna(x) else False
                                        )
                                    ]
                                
                                if not matching_rows.empty:
                                    geom = matching_rows.iloc[0].geometry
                                    if geom and geom.is_valid:
                                        geometry = geom.__geo_interface__
                                        matched_tribal += 1
                                        matched_by_mapping += 1
                                        match_method = 'tribal_mapping'
                                        logger.debug(f"Matched tribal '{jurisdiction_name}' via mapping to '{tribal_name}'")
                        
                        # Fallback to fuzzy matching if mapping failed
                        if geometry is None and 'tribe' in tribal_geometries_gdf.columns:
                            matching_rows = tribal_geometries_gdf[
                                tribal_geometries_gdf['tribe'].apply(
                                    lambda x: (jurisdiction_name.upper() in x.upper() or x.upper() in jurisdiction_name.upper()) if pd.notna(x) else False
                                )
                            ]
                            if not matching_rows.empty:
                                geom = matching_rows.iloc[0].geometry
                                if geom and geom.is_valid:
                                    geometry = geom.__geo_interface__
                                    matched_tribal += 1
                                    matched_by_fuzzy += 1
                                    match_method = 'tribal_fuzzy'
                else:
                    # Use mapping table for county/city boundaries
                    if county_geometries_gdf is not None and 'OBJECTID' in county_geometries_gdf.columns:
                        boundary_id = get_boundary_objectid(jurisdiction_id)
                        
                        if boundary_id is not None:
                            # Match using OBJECTID from mapping table
                            matching_rows = county_geometries_gdf[
                                county_geometries_gdf['OBJECTID'] == boundary_id
                            ]
                            
                            if not matching_rows.empty:
                                geom = matching_rows.iloc[0].geometry
                                if geom and geom.is_valid:
                                    geometry = geom.__geo_interface__
                                    matched_county += 1
                                    matched_by_mapping += 1
                                    match_method = 'objectid_mapping'
                                    logger.debug(f"Matched '{jurisdiction_name}' via mapping to OBJECTID {boundary_id}")
                        
                        # Fallback to fuzzy name matching if mapping failed
                        if geometry is None and 'AGENCY' in county_geometries_gdf.columns:
                            # Try exact match first
                            matching_rows = county_geometries_gdf[
                                county_geometries_gdf['AGENCY'].str.upper() == jurisdiction_name.upper()
                            ]
                            
                            # Try fuzzy match if exact fails
                            if matching_rows.empty:
                                matching_rows = county_geometries_gdf[
                                    county_geometries_gdf['AGENCY'].apply(
                                        lambda x: (x.upper() in jurisdiction_name.upper() or jurisdiction_name.upper() in x.upper()) if pd.notna(x) else False
                                    )
                                ]
                            
                            if not matching_rows.empty:
                                geom = matching_rows.iloc[0].geometry
                                if geom and geom.is_valid:
                                    geometry = geom.__geo_interface__
                                    matched_county += 1
                                    matched_by_fuzzy += 1
                                    match_method = 'name_fuzzy'
                                    logger.debug(f"Matched '{jurisdiction_name}' via fuzzy name matching")
                
                # If no geometry found, create point from centroid
                if geometry is None:
                    geometry = {
                        "type": "Point",
                        "coordinates": [record.get('lon', -89.5), record.get('lat', 44.5)]
                    }
                    unmatched += 1
                    logger.warning(f"No boundary match for {jurisdiction_name} ({jurisdiction_id}), using point geometry")
                
                feature = {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": geometry
                }
                
                features.append(feature)
                
            except Exception as e:
                logger.warning(f"Error creating feature for {record.get('jurisdiction', 'unknown')}: {e}")
                continue
        
        logger.info(f"Geometry matching results: {matched_county} county/city, {matched_tribal} tribal, {unmatched} unmatched")
        logger.info(f"Match methods: {matched_by_mapping} via mapping table, {matched_by_fuzzy} via fuzzy matching")
        
        # Create GeoJSON structure (no CRS for ArcGIS Pro compatibility)
        # Modern GeoJSON standard assumes WGS84 (EPSG:4326) by default
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }
        
        try:
            with open(geojson_path, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully exported {len(features)} features to GeoJSON: {geojson_path}")
            return str(geojson_path)
            
        except Exception as e:
            logger.error(f"Error exporting to GeoJSON: {e}")
            raise