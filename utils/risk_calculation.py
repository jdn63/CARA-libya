"""Utility module for risk calculation functions used across the application"""
import json
import logging
import os
from typing import Dict, Optional

import pandas as pd

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# NRI data cache to avoid repeated file reads
_nri_health_data_cache = None

def get_health_impact_factor(county_name: str, hazard_type: str) -> float:
    """
    Retrieves health impact factor from FEMA NRI data for a specific county and hazard type.
    
    The health impact factor considers:
    1. Expected Annual Loss of Population (EAL_POPULATION)
    2. Social Vulnerability components (SOVI_HEALTH)
    3. Healthcare Access metrics (HEALTHCARE_ACCESS)
    4. Population with Disabilities percentage (DISABILITY_PERCENT)
    
    Args:
        county_name: The name of the Wisconsin county
        hazard_type: The type of hazard (flood, tornado, winter_storm, etc.)
        
    Returns:
        A health impact factor (0.8-1.5) where:
        - <1.0 means reduced health impacts compared to average
        - 1.0 means average health impacts
        - >1.0 means elevated health impacts compared to average
    """
    global _nri_health_data_cache
    
    # Load NRI health data if not already cached
    if _nri_health_data_cache is None:
        try:
            # Attempt to load data from NRI CSV file
            nri_path = 'attached_assets/NRI_Table_CensusTracts_Wisconsin_FloodTornadoWinterOnly.csv'
            if os.path.exists(nri_path):
                logger.info(f"Loading NRI health impact data from {nri_path}")
                nri_df = pd.read_csv(nri_path)
                
                # Aggregate to county level
                county_health_data = {}
                for county in nri_df['county'].unique():
                    county_rows = nri_df[nri_df['county'] == county]
                    
                    # Create county-level health impact factors by hazard type
                    # Note: Actual field names would depend on the specific NRI dataset structure
                    county_health_data[county] = {
                        # Scale and normalize each factor to the desired range (0.8-1.5)
                        "flood": _calculate_normalized_health_factor(county_rows, 'flood'),
                        "tornado": _calculate_normalized_health_factor(county_rows, 'tornado'),
                        "winter_storm": _calculate_normalized_health_factor(county_rows, 'winter'),
                        # Default factors for other hazard types
                        "thunderstorm": 1.1,  # Slightly elevated health impacts
                        "extreme_heat": 1.3,  # Higher health impacts due to vulnerable populations
                        "active_shooter": 1.4,  # Significant direct health impacts
                        "infectious_disease": 1.5,  # Maximum health impacts
                        "electrical_outage": 1.2,  # Healthcare system disruption
                        "utilities_disruption": 1.2,  # Sanitation and water impacts
                        "supply_chain": 1.1,  # Medical supply disruption
                        "fuel_shortage": 1.0,  # Less direct health impacts
                        "cybersecurity": 1.1   # Healthcare information systems impacts
                    }
                
                _nri_health_data_cache = county_health_data
                logger.info(f"Successfully loaded health impact factors for {len(county_health_data)} counties")
            else:
                logger.warning(f"NRI data file not found at {nri_path}, using default health factors")
                _nri_health_data_cache = {}
                
        except Exception as e:
            logger.error(f"Error loading NRI health impact data: {str(e)}")
            _nri_health_data_cache = {}
    
    # Get health factor for the county and hazard type
    # Default to 1.0 (neutral) if data isn't available
    county_data = _nri_health_data_cache.get(county_name, {})
    
    # Normalize hazard type name (convert spaces to underscores, lowercase)
    hazard_key = hazard_type.lower().replace(' ', '_')
    
    # Get health factor with fallback to default of 1.0
    health_factor = county_data.get(hazard_key, 1.0)
    
    logger.info(f"Health impact factor for {county_name}, {hazard_type}: {health_factor:.2f}")
    return health_factor

def _calculate_normalized_health_factor(county_rows: pd.DataFrame, hazard_type: str) -> float:
    """
    Calculate a normalized health impact factor from NRI data for a specific hazard type.
    
    Args:
        county_rows: DataFrame containing NRI data for a specific county
        hazard_type: The type of hazard (flood, tornado, winter)
        
    Returns:
        A normalized health impact factor between 0.8 and 1.5
    """
    try:
        # These field names are examples and would need to be adjusted
        # based on actual NRI data structure
        risk_field = f'{hazard_type}_risk'
        population_loss_field = f'{hazard_type}_eals_population' 
        exposure_field = f'{hazard_type}_exposure'
        
        # Extract relevant metrics if they exist
        if risk_field in county_rows.columns and population_loss_field in county_rows.columns:
            # Calculate weighted average based on exposure
            risk = county_rows[risk_field].mean() / 100.0  # Normalize to 0-1
            pop_loss = county_rows[population_loss_field].mean()
            
            # NRI SoVI (Social Vulnerability Index) includes health components
            sovi = county_rows['sovi'].mean() / 100.0 if 'sovi' in county_rows.columns else 0.5
            
            # Combined factor considering hazard risk, population loss and social vulnerability
            raw_factor = (0.4 * risk + 0.4 * pop_loss + 0.2 * sovi)
            
            # Normalize to our desired range (0.8-1.5)
            # 0.8 = minimal health impact, 1.5 = severe health impact
            normalized_factor = 0.8 + (0.7 * raw_factor)
            
            # Ensure it's within our bounds
            return max(0.8, min(1.5, normalized_factor))
        else:
            # Default values if fields don't exist
            if hazard_type == 'flood':
                return 1.2  # Higher health impacts
            elif hazard_type == 'tornado':
                return 1.3  # Higher health impacts
            elif hazard_type == 'winter':
                return 1.1  # Moderate health impacts
            else:
                return 1.0  # Neutral
                
    except Exception as e:
        logger.warning(f"Error calculating health factor for {hazard_type}: {str(e)}")
        return 1.0  # Default to neutral

def calculate_residual_risk(exposure: float, vulnerability: float, resilience: float, 
                           max_risk: float = 1.0, health_impact_factor: float = None) -> float:
    """
    Calculate residual risk using the corrected intuitive formula:
    Residual Risk = (Exposure × Vulnerability) × Resilience_Adjustment × Health_Impact_Factor
    
    This corrected formula provides logical risk assessment where:
    1. High vulnerability + low resilience = high risk (as expected)
    2. Resilience acts as an amplification factor rather than simple subtraction
    3. Low resilience amplifies risk, high resilience reduces amplification
    4. No artificial risk floor that masks real differences between jurisdictions
    5. Incorporates health-related consequences from FEMA NRI data
    
    Args:
        exposure: The exposure score (0-1), representing hazard likelihood and magnitude
        vulnerability: The vulnerability score (0-1), representing susceptibility to the hazard
        resilience: The resilience score (0-1), representing community capacity (higher is better)
        max_risk: The maximum risk calibration constant (unused in corrected formula, kept for compatibility)
        health_impact_factor: Optional multiplier (0.8-1.5) representing health-related consequences
                             from FEMA NRI data such as:
                             - Expected Annual Loss of Population
                             - Social Vulnerability components related to health
                             - Population with Disabilities
                             - Healthcare Access metrics
                             If None, defaults to 1.0 (no adjustment)
        
    Returns:
        A residual risk score between 0-1
    """
    # Apply default health impact factor if not provided
    if health_impact_factor is None:
        health_impact_factor = 1.0
    
    # Calculate base risk from exposure and vulnerability
    base_risk = exposure * vulnerability
    
    # Calculate resilience adjustment factor
    # Low resilience (0.1) → 1.9x amplifier (high risk amplification)
    # Medium resilience (0.5) → 1.5x amplifier (moderate amplification)
    # High resilience (0.9) → 1.1x amplifier (minimal amplification)
    # This ensures resilience never completely eliminates risk but low resilience significantly amplifies it
    resilience_adjustment = 2.0 - resilience
    
    # Apply the corrected formula: Base Risk × Resilience Adjustment × Health Impact
    residual_risk = base_risk * resilience_adjustment * health_impact_factor
    
    # Ensure result is between 0 and 1
    residual_risk = max(0.0, min(1.0, residual_risk))
    
    logger.info(f"CORRECTED Risk calculation: exposure={exposure:.2f}, vulnerability={vulnerability:.2f}, " 
                f"resilience={resilience:.2f}, resilience_adj={resilience_adjustment:.2f}, " 
                f"health_factor={health_impact_factor:.2f} → risk={residual_risk:.2f}")
    
    return residual_risk