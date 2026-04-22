"""
Census data validation utilities

This module provides functions to validate and verify Census API data
to ensure it meets quality standards and can be reliably used in
risk calculations.
"""
import logging
import math
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


def validate_census_variable(data: Dict[str, Any], var_name: str, default_value: Any = 0) -> Any:
    """
    Validate a single Census variable and apply appropriate fallbacks if needed
    
    Args:
        data: Dictionary containing Census API data
        var_name: Name of the Census variable to validate
        default_value: Default value to use if validation fails
        
    Returns:
        Validated variable value or default value
    """
    # Check if variable exists
    if var_name not in data:
        logger.warning(f"Census variable {var_name} not found in data")
        return default_value
    
    value = data[var_name]
    
    # Handle None values
    if value is None:
        logger.warning(f"Census variable {var_name} is None")
        return default_value
    
    # Handle negative values for counts (should never be negative)
    if isinstance(value, (int, float)) and value < 0 and var_name.endswith('E'):
        logger.warning(f"Census variable {var_name} has negative value: {value}, using default")
        return default_value
    
    return value


def validate_census_ratio(data: Dict[str, Any], 
                          numerator_var: str, 
                          denominator_var: str, 
                          default_ratio: float = 0.0) -> float:
    """
    Validate and calculate a ratio from two Census variables
    
    Args:
        data: Dictionary containing Census API data
        numerator_var: Name of the numerator Census variable
        denominator_var: Name of the denominator Census variable
        default_ratio: Default ratio to use if validation fails
        
    Returns:
        Validated ratio or default ratio
    """
    # Get validated values
    numerator = validate_census_variable(data, numerator_var, 0)
    denominator = validate_census_variable(data, denominator_var, 1)  # Use 1 to avoid division by zero
    
    # Verify denominator isn't zero
    if denominator == 0:
        logger.warning(f"Census variable {denominator_var} is zero, cannot calculate ratio")
        return default_ratio
    
    # Calculate ratio
    ratio = numerator / denominator
    
    # Check if ratio makes sense (between 0 and 1 for most demographic ratios)
    if ratio < 0 or ratio > 1:
        logger.warning(f"Census ratio {numerator_var}/{denominator_var} = {ratio} is outside expected range [0,1]")
        # We'll still return it, but log the warning
    
    return ratio


def validate_county_data_completeness(data: Dict[str, Any], required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that county data has all required variables and meets quality standards
    
    Args:
        data: Dictionary containing Census API data for a county
        required_vars: List of required Census variables
        
    Returns:
        Tuple of (is_complete, missing_vars)
    """
    missing_vars = []
    
    # Check for missing variables
    for var in required_vars:
        if var not in data or data[var] is None:
            missing_vars.append(var)
    
    # Calculate completeness percentage
    completeness = 1.0 - (len(missing_vars) / len(required_vars))
    logger.info(f"County data completeness: {completeness:.2f} ({len(required_vars) - len(missing_vars)}/{len(required_vars)} variables)")
    
    # Data is considered complete if it has at least 90% of required variables
    is_complete = completeness >= 0.9
    
    if not is_complete:
        logger.warning(f"County data missing too many required variables: {missing_vars}")
    
    return is_complete, missing_vars


def aggregate_tract_to_county(tract_data: List[Dict[str, Any]], required_vars: List[str]) -> Optional[Dict[str, Any]]:
    """
    Aggregate Census tract-level data to county level when county-level is unavailable
    
    Args:
        tract_data: List of dictionaries containing Census API data for tracts
        required_vars: List of required Census variables
        
    Returns:
        Aggregated county data or None if aggregation fails
    """
    if not tract_data:
        logger.error("No tract data provided for aggregation")
        return None
    
    aggregated = {}
    
    try:
        # Initialize aggregated data
        for var in required_vars:
            if var.endswith('E'):  # Estimate variables should be summed
                aggregated[var] = sum(validate_census_variable(tract, var, 0) for tract in tract_data)
            elif var.endswith('M'):  # Margin of error uses root sum of squares
                # For MOE, use the RSS (root sum of squares)
                aggregated[var] = (sum(validate_census_variable(tract, var, 0)**2 for tract in tract_data))**0.5
            elif var in tract_data[0]:  # Other variables just take from first tract
                aggregated[var] = tract_data[0][var]
        
        logger.info(f"Successfully aggregated {len(tract_data)} tracts to county level")
        return aggregated
        
    except Exception as e:
        logger.error(f"Error aggregating tract data to county level: {str(e)}")
        return None


def validate_census_response(data: Any) -> Tuple[bool, Dict[str, Any], str]:
    """
    Validate Census API response data
    
    Args:
        data: Data returned from Census API
        
    Returns:
        Tuple of (is_valid, data, error_message)
    """
    error_message = ""
    
    # Check if data is None
    if data is None:
        error_message = "Census API returned no data"
        logger.error(error_message)
        return False, {}, error_message
    
    # Check if data is a list with at least one item
    if not isinstance(data, list) or len(data) == 0:
        error_message = f"Census API returned invalid data format: {type(data)}"
        logger.error(error_message)
        return False, {}, error_message
    
    # Get the first item (for county data)
    county_data = data[0]
    
    # Check if it's a dictionary
    if not isinstance(county_data, dict):
        error_message = f"Census API returned non-dictionary data: {type(county_data)}"
        logger.error(error_message)
        return False, {}, error_message
    
    # Check if it has any keys
    if len(county_data.keys()) == 0:
        error_message = "Census API returned empty dictionary"
        logger.error(error_message)
        return False, {}, error_message
    
    # Data looks valid
    return True, county_data, ""


def validate_percentage_calculation(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely calculate a percentage, handling edge cases
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if calculation fails
        
    Returns:
        Calculated percentage (0-1 range) or default value
    """
    # Handle None values
    if numerator is None or denominator is None:
        return default
    
    # Handle non-numeric values
    try:
        num = float(numerator)
        denom = float(denominator)
    except (ValueError, TypeError):
        return default
    
    # Handle zero denominator
    if denom == 0:
        return default
    
    # Calculate percentage
    percentage = num / denom
    
    # Check for NaN or infinity
    if math.isnan(percentage) or math.isinf(percentage):
        return default
    
    # Ensure result is between 0 and 1
    return max(0.0, min(1.0, percentage))
