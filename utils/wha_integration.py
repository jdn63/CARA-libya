"""Module for integrating Wisconsin Hospital Association (WHA) data"""
import logging
import os
import requests
import json
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def get_hospital_capacity_data(region_id: str) -> Optional[Dict]:
    """
    Fetch real-time hospital capacity data from WHA's public data portal
    
    Args:
        region_id: HERC region ID
        
    Returns:
        Dictionary containing hospital capacity data or None if not available
    """
    try:
        api_url = os.environ.get('WHA_API_URL')
        api_key = os.environ.get('WHA_API_KEY')

        if not api_url or not api_key:
            logger.debug("WHA API credentials not configured")
            return None

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            f"{api_url}/regions/{region_id}/capacity",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch WHA data: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error fetching WHA data: {str(e)}")
        return None
