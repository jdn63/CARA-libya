"""Correctional Facilities Data Integration"""
import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CorrectionalFacilitiesConnector:
    """Connector for correctional facilities data from OpenFEMA and WI DOC"""
    
    def __init__(self):
        self.openfema_base_url = "https://www.fema.gov/api/open/v1"
        self.wi_doc_base_url = "https://doc.wi.gov/api/facilities"  # Example URL
        
    def get_correctional_facilities(self, state_code: str = "WI") -> Dict[str, Dict]:
        """
        Fetch correctional facilities data from multiple sources
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
            # Define facility type weights
            facility_weights = {
                'state_prison': 1.0,
                'county_jail': 0.8,
                'juvenile': 0.6,
                'treatment': 0.4
            }
            
            # Fetch data from OpenFEMA API
            facilities_data = {}
            
            try:
                # OpenFEMA API request for public facilities
                response = requests.get(
                    f"{self.openfema_base_url}/publicAssistanceFundedProjectsDetails",
                    params={
                        'state': state_code,
                        'damageCategory': 'E',  # Public buildings
                        'declarationType': 'DR',  # Major disaster declarations
                        '$filter': "facilityType eq 'CORRECTIONAL'",
                        '$select': 'countyName,projectTitle,damageCategory,facilityType',
                        '$top': 1000
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    fema_data = response.json()
                    for facility in fema_data.get('PublicAssistanceFundedProjectsDetails', []):
                        county = facility.get('countyName', '').replace(' County', '')
                        if not county:
                            continue
                            
                        if county not in facilities_data:
                            facilities_data[county] = {
                                'facilities': [],
                                'weights': facility_weights
                            }
                        
                        # Extract facility type from project title
                        facility_name = facility.get('projectTitle', '')
                        facility_type = self._determine_facility_type(facility_name)
                        
                        if any(f['name'] == facility_name for f in facilities_data[county]['facilities']):
                            continue  # Skip duplicates
                            
                        facilities_data[county]['facilities'].append({
                            'type': facility_type,
                            'name': facility_name
                        })
                
            except Exception as e:
                logger.error(f"Error fetching OpenFEMA data: {str(e)}")
            
            # Fetch Wisconsin DOC facility data
            try:
                response = requests.get(
                    "https://doc.wi.gov/Pages/DataResearch/PrisonFacilities.aspx",
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Parse the DOC webpage content
                    # This would need to be adjusted based on actual DOC data structure
                    # For now, using our existing data as fallback
                    pass
                    
            except Exception as e:
                logger.error(f"Error fetching WI DOC data: {str(e)}")
            
            # If no data was fetched, use fallback data
            if not facilities_data:
                logger.warning("Using fallback correctional facilities data")
                return self._get_fallback_data()
                
            return facilities_data
            
        except Exception as e:
            logger.error(f"Error fetching correctional facilities data: {str(e)}")
            return self._get_fallback_data()
    
    def _determine_facility_type(self, facility_name: str) -> str:
        """Determine facility type based on name and description"""
        facility_name = facility_name.lower()
        
        if any(term in facility_name for term in ['state prison', 'correctional institution', 'maximum security']):
            return 'state_prison'
        elif any(term in facility_name for term in ['jail', 'detention center', 'holding']):
            return 'county_jail'
        elif any(term in facility_name for term in ['juvenile', 'youth', 'child']):
            return 'juvenile'
        elif any(term in facility_name for term in ['treatment', 'rehabilitation', 'minimum security']):
            return 'treatment'
        else:
            return 'county_jail'  # Default to county jail if type is unclear
    
    def _get_fallback_data(self) -> Dict[str, Dict]:
        """Return empty data when APIs are unavailable"""
        logger.warning("Correctional facilities API data unavailable - no fallback data used")
        return {}
