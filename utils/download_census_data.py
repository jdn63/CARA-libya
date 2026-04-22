#!/usr/bin/env python3
"""
Download Wisconsin County Census Data for Strategic Planning

This script downloads county-specific demographic data from the Census Bureau API
and formats it for use in the CARA strategic planning tool.
"""

import requests
import pandas as pd
import logging
import os

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

def download_wisconsin_census_data(api_key=None):
    """
    Download Wisconsin county census data and save to local files
    
    Args:
        api_key: Census API key (optional - can work without for basic data)
    """
    
    if not api_key:
        logger.warning("No API key provided - using alternative data sources")
        return download_alternative_sources()
    
    try:
        # Wisconsin state code
        wisconsin_fips = "55"
        
        # Download mobile home data (Table B25024)
        logger.info("Downloading mobile home data...")
        mobile_url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME,B25024_010E,B25024_001E&for=county:*&in=state:{wisconsin_fips}&key={api_key}"
        
        mobile_response = requests.get(mobile_url, timeout=30)
        if mobile_response.status_code == 200:
            mobile_data = mobile_response.json()
            logger.info(f"Downloaded mobile home data for {len(mobile_data)-1} counties")
        else:
            logger.error(f"Mobile home data request failed: {mobile_response.status_code}")
            return False
        
        # Download population aged 65+ data (Table DP05)
        logger.info("Downloading population 65+ data...")
        elderly_url = f"https://api.census.gov/data/2022/acs/acs5/profile?get=NAME,DP05_0024PE,DP05_0001E&for=county:*&in=state:{wisconsin_fips}&key={api_key}"
        
        elderly_response = requests.get(elderly_url, timeout=30)
        if elderly_response.status_code == 200:
            elderly_data = elderly_response.json()
            logger.info(f"Downloaded population 65+ data for {len(elderly_data)-1} counties")
        else:
            logger.error(f"Population 65+ data request failed: {elderly_response.status_code}")
            return False
        
        # Process mobile home data
        mobile_df = pd.DataFrame(mobile_data[1:], columns=mobile_data[0])
        mobile_df['county_name'] = mobile_df['NAME'].str.replace(' County, Wisconsin', '')
        mobile_df['mobile_homes'] = pd.to_numeric(mobile_df['B25024_010E'], errors='coerce')
        mobile_df['total_housing_units'] = pd.to_numeric(mobile_df['B25024_001E'], errors='coerce')
        mobile_df['mobile_home_percentage'] = (mobile_df['mobile_homes'] / mobile_df['total_housing_units'] * 100).round(2)
        
        # Process population aged 65+ data  
        elderly_df = pd.DataFrame(elderly_data[1:], columns=elderly_data[0])
        elderly_df['county_name'] = elderly_df['NAME'].str.replace(' County, Wisconsin', '')
        elderly_df['total_population'] = pd.to_numeric(elderly_df['DP05_0001E'], errors='coerce')
        elderly_df['elderly_percentage'] = pd.to_numeric(elderly_df['DP05_0024PE'], errors='coerce')
        elderly_df['population_65_plus'] = (elderly_df['total_population'] * elderly_df['elderly_percentage'] / 100).round(0).astype(int)
        
        # Save to CSV files
        os.makedirs('data/census', exist_ok=True)
        
        # Housing data
        housing_cols = ['county_name', 'total_housing_units', 'mobile_homes', 'mobile_home_percentage']
        mobile_df[housing_cols].to_csv('data/census/wisconsin_housing_data_downloaded.csv', index=False)
        logger.info("Saved housing data to data/census/wisconsin_housing_data_downloaded.csv")
        
        # Demographics data
        demo_cols = ['county_name', 'total_population', 'population_65_plus', 'elderly_percentage']
        elderly_df[demo_cols].to_csv('data/census/wisconsin_demographics_downloaded.csv', index=False)
        logger.info("Saved demographics data to data/census/wisconsin_demographics_downloaded.csv")
        
        logger.info("✅ Census data download completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading Census data: {str(e)}")
        return False

def download_alternative_sources():
    """
    Download data from alternative sources when Census API is not available
    """
    logger.info("Using Wisconsin DHS and other state sources...")
    
    # This would implement alternative download methods
    # For now, let's just inform the user about manual options
    
    print("""
    Alternative Data Sources for Wisconsin Counties:
    
    1. Wisconsin DHS Demographics:
       https://www.dhs.wisconsin.gov/aging/demographics.htm
       
    2. Wisconsin DOA Census Data:
       https://doa.wi.gov/Pages/LocalGovtsGrants/US_Census_Bureau_News_and_Products_for_Wisconsin.aspx
       
    3. Census Reporter (user-friendly):
       https://censusreporter.org/profiles/04000US55-wisconsin/
       
    4. Direct Census Data Portal:
       https://data.census.gov/
       - Search for "Wisconsin counties"
       - Select Table B25024 (housing) and DP05 (demographics)
       - Download as CSV
    """)
    
    return False

def get_census_api_key():
    """
    Help user get a Census API key
    """
    print("""
    To get a free Census API key:
    
    1. Visit: https://api.census.gov/data/key_signup.html
    2. Provide your name and email
    3. You'll receive the key via email instantly
    4. It's completely free and no restrictions for research use
    
    Then run this script with your key:
    python utils/download_census_data.py YOUR_API_KEY
    """)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        success = download_wisconsin_census_data(api_key)
        if not success:
            download_alternative_sources()
    else:
        print("Wisconsin Census Data Downloader")
        print("=" * 40)
        print()
        api_key = input("Enter your Census API key (or press Enter to see alternatives): ").strip()
        
        if api_key:
            success = download_wisconsin_census_data(api_key)
            if not success:
                download_alternative_sources()
        else:
            get_census_api_key()
            download_alternative_sources()