"""
Gun Violence Archive (GVA) Data Processor

This module processes data from the Gun Violence Archive (gunviolencearchive.org/reports)
to enhance the active shooter risk assessment with real-world incident data.

The GVA provides comprehensive data on gun violence incidents that can be 
downloaded as CSV files from their website.
"""

import os
import json
import logging
import csv
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import io

try:
    import pandas as pd
except ImportError:
    pd = None

# Import Wisconsin city-to-county mapping
from utils.wisconsin_mapping import get_county_for_city

# Set up logging
logger = logging.getLogger(__name__)

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs('data/gva_reports', exist_ok=True)
    logger.info("Ensured data/gva_reports directory exists")

def get_incident_data_for_location(location: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Get gun violence incident data for a specific location
    
    Args:
        location: Location name (county or state)
        
    Returns:
        Tuple of (incidents, stats)
        - incidents: List of incident dictionaries with details
        - stats: Dictionary with summary statistics
    """
    ensure_data_directory()
    
    # Check if we're looking for state-level data
    is_state = location.lower() == 'wisconsin'
    
    # Normalize county name (remove "County" suffix if present)
    if not is_state:
        location = location.replace(' County', '').strip()
    
    # Load incidents from all available files
    all_incidents = []
    
    try:
        for filename in os.listdir('data/gva_reports'):
            if not filename.endswith('.json'):
                continue
                
            try:
                with open(f'data/gva_reports/{filename}', 'r') as f:
                    data = json.load(f)
                    
                for incident in data.get('incidents', []):
                    # First check if this is a Wisconsin incident
                    if incident.get('state') != 'Wisconsin':
                        continue
                        
                    # For state-level data, include all Wisconsin incidents
                    if is_state:
                        all_incidents.append(incident)
                        continue
                    
                    # Check if county is directly specified
                    if incident.get('county') and location.lower() in incident.get('county').lower():
                        all_incidents.append(incident)
                        continue
                    
                    # If we have a city but no county, derive county from city
                    if incident.get('city') and not incident.get('county'):
                        city_name = incident.get('city')
                        derived_county = get_county_for_city(city_name)
                        
                        # Add derived county to incident data for future use
                        if derived_county:
                            incident['derived_county'] = derived_county
                            
                            # If derived county matches our target location, include incident
                            if location.lower() == derived_county.lower():
                                logger.info(f"Matched incident in {city_name} to {derived_county} County")
                                all_incidents.append(incident)
                                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error scanning data directory: {str(e)}")
    
    # Calculate statistics
    stats = {
        'total_incidents': len(all_incidents),
        'incidents_by_year': {},
        'fatalities': sum(incident.get('killed', 0) for incident in all_incidents),
        'injuries': sum(incident.get('injured', 0) for incident in all_incidents),
        'data_sources': ['Gun Violence Archive']
    }
    
    # Group by year
    for incident in all_incidents:
        if 'date' in incident:
            try:
                year = incident['date'].split('-')[0] if '-' in incident['date'] else incident['date'][:4]
                if year in stats['incidents_by_year']:
                    stats['incidents_by_year'][year] += 1
                else:
                    stats['incidents_by_year'][year] = 1
            except (ValueError, KeyError, IndexError, TypeError) as e:
                logger.warning(f"Error parsing date from incident: {e}")
                pass
    
    return all_incidents, stats

def get_incident_density_score(location: str) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate an incident density score based on GVA data
    
    Args:
        location: County name or 'Wisconsin'
        
    Returns:
        Tuple of (score, metrics_dict)
        - score: Normalized score between 0.0 and 1.0
        - metrics_dict: Dictionary with metrics used for calculation
    """
    import math
    
    # Get incident data
    incidents, stats = get_incident_data_for_location(location)
    
    if not incidents:
        logger.warning(f"No GVA incident data found for {location}")
        return 0.0, {
            "incidents_10yr": 0,
            "incidents_per_100k": 0.0,
            "data_sources": ["Gun Violence Archive - No Data"],
            "trend": "insufficient data"
        }
    
    # Get 10-year count
    incidents_10yr = len(incidents)
    
    # Approximate population (would be better to get from Census)
    # Using rough estimates for Wisconsin counties
    if location.lower() == 'wisconsin':
        population = 5800000  # State population approximation
    elif location.lower() == 'milwaukee':
        population = 945000
    elif location.lower() == 'dane':
        population = 550000
    elif location.lower() == 'waukesha':
        population = 405000
    elif location.lower() == 'brown':
        population = 270000
    else:
        # Default to average Wisconsin county
        population = 80000
    
    # Calculate per 100k rate
    per_100k_rate = (incidents_10yr / population) * 100000
    
    # Calculate trend from yearly data
    yearly_data = stats.get('incidents_by_year', {})
    years = sorted(yearly_data.keys())
    
    if len(years) >= 3:
        first_half = sum(yearly_data.get(year, 0) for year in years[:len(years)//2])
        second_half = sum(yearly_data.get(year, 0) for year in years[len(years)//2:])
        
        if second_half > first_half * 1.2:
            trend = "increasing"
        elif second_half < first_half * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient data"
    
    # Calculate score using sigmoid-like function to normalize between 0 and 1
    # Score of 0.5 around 12 incidents per 100k, 0.8 around 25 per 100k
    score = min(1.0, math.tanh(per_100k_rate / 20))
    
    return score, {
        "incidents_10yr": incidents_10yr,
        "incidents_per_100k": round(per_100k_rate, 1),
        "data_sources": ["Gun Violence Archive"],
        "trend": trend,
        "fatalities": stats.get('fatalities', 0),
        "injuries": stats.get('injuries', 0)
    }

def process_gva_file(file_path_or_object) -> str:
    """
    Process a GVA CSV file and store it in the data directory
    
    Args:
        file_path_or_object: Path to the CSV file or file-like object
        
    Returns:
        Path to the processed JSON file
    """
    ensure_data_directory()
    
    try:
        # Check if we have a path or file-like object
        if isinstance(file_path_or_object, str):
            filename = os.path.basename(file_path_or_object)
            file_obj = open(file_path_or_object, 'r')
        else:
            # Assume it's a file-like object (e.g., from request.files)
            filename = file_path_or_object.filename
            file_obj = file_path_or_object.stream
        
        # Try to extract year from filename
        year = None
        for y in range(2014, 2025):
            if str(y) in filename:
                year = str(y)
                break
        
        # Process incidents
        processed_incidents = []
        
        # Using standard CSV module since we might not have pandas
        csv_reader = csv.DictReader(file_obj)
        
        for incident in csv_reader:
            # Clean up the data
            processed_incident = {}
            
            # Map specific columns for the Gun Violence Archive data
            field_mappings = {
                'Incident ID': 'incident_id',
                'Incident Date': 'date',
                'State': 'state',
                'City Or County': 'city_or_county',
                'Address': 'address',
                'Victims Killed': 'killed',
                'Victims Injured': 'injured',
                'Operations': 'operations'
            }
            
            # Process fields based on mappings
            for original_field, mapped_field in field_mappings.items():
                if original_field in incident:
                    processed_incident[mapped_field] = incident[original_field]
            
            # Determine if it's a city or county
            if 'city_or_county' in processed_incident:
                location = processed_incident['city_or_county']
                if ' County' in location:
                    processed_incident['county'] = location
                else:
                    processed_incident['city'] = location
                    
                    # If it's a city in Wisconsin, try to determine the county
                    if processed_incident.get('state') == 'Wisconsin' and 'county' not in processed_incident:
                        county = get_county_for_city(location)
                        if county:
                            processed_incident['derived_county'] = county
                            logger.info(f"Derived county for {location}, WI: {county}")
            
            # Convert numeric fields
            for num_field in ['killed', 'injured']:
                if num_field in processed_incident:
                    try:
                        processed_incident[num_field] = int(processed_incident[num_field])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting {num_field} to int: {e}")
                        processed_incident[num_field] = 0
            
            # Additional metadata specifically for the incident
            if 'incident_id' in processed_incident:
                processed_incident['id'] = processed_incident['incident_id']
            
            # Only add incidents with valid data
            if processed_incident:
                processed_incidents.append(processed_incident)
        
        # Create output structure
        output_data = {
            'year': year,
            'source': 'Gun Violence Archive',
            'processed_date': datetime.now().isoformat(),
            'incidents': processed_incidents,
            'total_incidents': len(processed_incidents)
        }
        
        # Determine output filename
        output_filename = f"gva_data_{year or 'unknown'}.json"
        output_path = f"data/gva_reports/{output_filename}"
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        logger.info(f"Processed {len(processed_incidents)} incidents from GVA data")
        return output_filename
        
    except Exception as e:
        logger.error(f"Error processing GVA file: {str(e)}")
        raise