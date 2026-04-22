#!/usr/bin/env python3
"""
Local Census Data Loader for Strategic Planning

This module replaces Census API calls with local file-based data loading
to provide reliable, county-specific demographic data for Wisconsin jurisdictions.
Perfect for strategic planning scenarios where consistent baseline data is needed.
"""

import os
import pandas as pd
import logging
from typing import Dict, Optional, Any
from utils.persistent_cache import get_from_persistent_cache, set_in_persistent_cache

logger = logging.getLogger(__name__)

class WisconsinCensusDataLoader:
    """
    Loads Wisconsin county-level Census data from local CSV files
    """
    
    def __init__(self):
        self.data_dir = 'data/census'
        self.housing_file = 'wisconsin_housing_data.csv'
        self.demographics_file = 'wisconsin_demographics.csv'
        self.cache_ttl = 90  # 90 days cache for strategic planning data
        
        # Load data on initialization
        self._housing_data = None
        self._demographics_data = None
        self._load_data()
    
    def _load_data(self):
        """Load CSV data files into memory"""
        try:
            # Load housing data
            housing_path = os.path.join(self.data_dir, self.housing_file)
            if os.path.exists(housing_path):
                self._housing_data = pd.read_csv(housing_path)
                logger.info(f"Loaded housing data for {len(self._housing_data)} Wisconsin counties")
            else:
                logger.warning(f"Housing data file not found: {housing_path}")
                self._housing_data = pd.DataFrame()
            
            # Load demographics data  
            demographics_path = os.path.join(self.data_dir, self.demographics_file)
            if os.path.exists(demographics_path):
                self._demographics_data = pd.read_csv(demographics_path)
                logger.info(f"Loaded demographics data for {len(self._demographics_data)} Wisconsin counties")
            else:
                logger.warning(f"Demographics data file not found: {demographics_path}")
                self._demographics_data = pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error loading Census data files: {str(e)}")
            self._housing_data = pd.DataFrame()
            self._demographics_data = pd.DataFrame()
    
    def get_mobile_home_percentage(self, county_name: str) -> Optional[float]:
        """
        Get mobile home percentage for a Wisconsin county from local data
        
        Args:
            county_name: Name of Wisconsin county (without 'County' suffix)
            
        Returns:
            Mobile home percentage or None if not found
        """
        cache_key = f"local_mobile_homes_{county_name}"
        cached_data = get_from_persistent_cache(cache_key, self.cache_ttl)
        if cached_data:
            return cached_data
        
        try:
            # Clean county name for matching
            clean_county = county_name.strip().replace(' County', '')
            
            # Handle tribal jurisdictions
            if self._is_tribal_jurisdiction(clean_county):
                clean_county = self._get_tribal_proxy_county(clean_county)
            
            # Look up in housing data
            if self._housing_data is not None and not self._housing_data.empty:
                county_row = self._housing_data[self._housing_data['county_name'].str.contains(clean_county, case=False, na=False)]
                
                if not county_row.empty:
                    mobile_home_pct = float(county_row.iloc[0]['mobile_home_percentage'])
                    set_in_persistent_cache(cache_key, mobile_home_pct)
                    logger.info(f"Local data: {clean_county} has {mobile_home_pct}% mobile homes")
                    return mobile_home_pct
            
            # Fallback to Wisconsin average
            logger.warning(f"No local mobile home data found for {clean_county}, using state average")
            return 5.2
            
        except Exception as e:
            logger.error(f"Error retrieving mobile home data for {county_name}: {str(e)}")
            return 5.2
    
    def get_elderly_population_percentage(self, county_name: str) -> Optional[float]:
        """
        Get population aged 65+ percentage for a Wisconsin county from local data
        
        Args:
            county_name: Name of Wisconsin county (without 'County' suffix)
            
        Returns:
            Elderly population percentage or None if not found
        """
        cache_key = f"local_elderly_pop_{county_name}"
        cached_data = get_from_persistent_cache(cache_key, self.cache_ttl)
        if cached_data:
            return cached_data
        
        try:
            # Clean county name for matching
            clean_county = county_name.strip().replace(' County', '')
            
            # Handle tribal jurisdictions
            if self._is_tribal_jurisdiction(clean_county):
                clean_county = self._get_tribal_proxy_county(clean_county)
            
            # Look up in demographics data
            if self._demographics_data is not None and not self._demographics_data.empty:
                county_row = self._demographics_data[self._demographics_data['county_name'].str.contains(clean_county, case=False, na=False)]
                
                if not county_row.empty:
                    elderly_pct = float(county_row.iloc[0]['elderly_percentage'])
                    set_in_persistent_cache(cache_key, elderly_pct)
                    logger.info(f"Local data: {clean_county} has {elderly_pct}% elderly population")
                    return elderly_pct
            
            # Fallback to Wisconsin average
            logger.warning(f"No local population 65+ data found for {clean_county}, using state average")
            return 18.7
            
        except Exception as e:
            logger.error(f"Error retrieving population 65+ data for {county_name}: {str(e)}")
            return 18.7
    
    def get_county_population(self, county_name: str) -> Optional[int]:
        """
        Get total population for a Wisconsin county from local data
        
        Args:
            county_name: Name of Wisconsin county (without 'County' suffix)
            
        Returns:
            Total population or None if not found
        """
        cache_key = f"local_population_{county_name}"
        cached_data = get_from_persistent_cache(cache_key, self.cache_ttl)
        if cached_data:
            return cached_data
        
        try:
            # Clean county name for matching
            clean_county = county_name.strip().replace(' County', '')
            
            # Handle tribal jurisdictions
            if self._is_tribal_jurisdiction(clean_county):
                clean_county = self._get_tribal_proxy_county(clean_county)
            
            # Look up in demographics data
            if self._demographics_data is not None and not self._demographics_data.empty:
                county_row = self._demographics_data[self._demographics_data['county_name'].str.contains(clean_county, case=False, na=False)]
                
                if not county_row.empty:
                    population = int(county_row.iloc[0]['total_population'])
                    set_in_persistent_cache(cache_key, population)
                    logger.info(f"Local data: {clean_county} has population of {population:,}")
                    return population
            
            # Fallback to Wisconsin average county size
            logger.warning(f"No local population data found for {clean_county}, using estimated average")
            return 80000  # Approximate average Wisconsin county population
            
        except Exception as e:
            logger.error(f"Error retrieving population data for {county_name}: {str(e)}")
            return 80000
    
    def _is_tribal_jurisdiction(self, county_name: str) -> bool:
        """Check if this is a tribal jurisdiction"""
        tribal_keywords = ['Ho-Chunk', 'HoChunk', 'Menominee', 'Oneida', 'Lac du Flambeau', 
                          'Bad River', 'Red Cliff', 'Potawatomi', 'St. Croix', 'Sokaogon', 
                          'Lac Courte Oreilles']
        return any(keyword in county_name for keyword in tribal_keywords)
    
    def _get_tribal_proxy_county(self, county_name: str) -> str:
        """Get proxy county for tribal jurisdiction demographics"""
        tribal_county_mapping = {
            'HoChunk': 'Jackson',
            'Ho-Chunk': 'Jackson',
            'Menominee': 'Menominee',
            'Oneida': 'Brown',
            'Lac du Flambeau': 'Vilas',
            'Bad River': 'Ashland',
            'Red Cliff': 'Bayfield',
            'Potawatomi': 'Forest',
            'St. Croix': 'Burnett',
            'Sokaogon': 'Forest',
            'Lac Courte Oreilles': 'Sawyer'
        }
        
        for tribal_name, mapped_county in tribal_county_mapping.items():
            if tribal_name in county_name:
                logger.info(f"Using {mapped_county} County as proxy for {county_name} tribal jurisdiction")
                return mapped_county
        
        return county_name
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data for validation"""
        return {
            'housing_data_counties': len(self._housing_data) if self._housing_data is not None else 0,
            'demographics_data_counties': len(self._demographics_data) if self._demographics_data is not None else 0,
            'data_directory': self.data_dir,
            'cache_ttl_days': self.cache_ttl
        }

# Global instance for easy access
wisconsin_census = WisconsinCensusDataLoader()