"""FEMA Risk Assessment Planning Tool (RAPT) API Connector"""
import os
import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FEMARAPTConnector:
    """Connector for FEMA RAPT API"""
    
    def __init__(self):
        self.base_url = "https://rapt.fema.gov/api/v1"  # Example URL, replace with actual FEMA RAPT API endpoint
        self.api_key = os.environ.get("FEMA_RAPT_API_KEY")
        
    def get_correctional_facilities(self, state_code: str = "WI") -> Dict[str, Dict]:
        """
        Fetch correctional facilities data from FEMA RAPT API
        Returns data in the format:
        {
            'county_name': {
                'facilities': [
                    {
                        'type': 'state_prison|county_jail|juvenile|treatment',
                        'name': 'Facility Name'
                    }
                ],
                'weights': {
                    'state_prison': 1.0,
                    'county_jail': 0.8,
                    'juvenile': 0.6,
                    'treatment': 0.4
                }
            }
        }
        """
        try:
            if not self.api_key:
                logger.error("FEMA RAPT API key not found")
                return self._get_fallback_data()
                
            # Define facility type weights
            facility_weights = {
                'state_prison': 1.0,
                'county_jail': 0.8,
                'juvenile': 0.6,
                'treatment': 0.4
            }
            
            # Make API request
            response = requests.get(
                f"{self.base_url}/facilities/correctional",
                params={
                    'state': state_code,
                    'api_key': self.api_key
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"FEMA RAPT API request failed: {response.status_code}")
                return self._get_fallback_data()
                
            # Process API response
            facilities_data = response.json()
            
            # Transform API data into our required format
            processed_data = {}
            for facility in facilities_data.get('facilities', []):
                county = facility.get('county', '')
                if not county:
                    continue
                    
                if county not in processed_data:
                    processed_data[county] = {
                        'facilities': [],
                        'weights': facility_weights
                    }
                
                processed_data[county]['facilities'].append({
                    'type': self._determine_facility_type(facility),
                    'name': facility.get('name', 'Unknown Facility')
                })
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching correctional facilities data: {str(e)}")
            return self._get_fallback_data()
    
    def _determine_facility_type(self, facility: Dict) -> str:
        """Determine facility type based on FEMA classification"""
        facility_type = facility.get('type', '').lower()
        
        if 'state' in facility_type and 'prison' in facility_type:
            return 'state_prison'
        elif 'jail' in facility_type or 'detention' in facility_type:
            return 'county_jail'
        elif 'juvenile' in facility_type:
            return 'juvenile'
        elif 'treatment' in facility_type or 'rehabilitation' in facility_type:
            return 'treatment'
        else:
            return 'county_jail'  # Default to county jail if type is unclear
    
    def _get_fallback_data(self) -> Dict[str, Dict]:
        """Return fallback data when API is unavailable"""
        logger.warning("Using fallback correctional facilities data")
        
        # Define facility type weights
        facility_weights = {
            'state_prison': 1.0,
            'county_jail': 0.8,
            'juvenile': 0.6,
            'treatment': 0.4
        }
        
        # Return our existing representative data
        return {
            'Milwaukee': {
                'facilities': [
                    {'type': 'state_prison', 'name': 'Milwaukee Secure Detention Facility'},
                    {'type': 'county_jail', 'name': 'Milwaukee County Jail'},
                    {'type': 'county_jail', 'name': 'House of Correction'},
                    {'type': 'juvenile', 'name': 'Vel R. Phillips Juvenile Justice Center'},
                    {'type': 'treatment', 'name': 'Milwaukee Women\'s Correctional Center'}
                ],
                'weights': facility_weights
            },
            # ... [previous fallback data for other counties] ...
        }
