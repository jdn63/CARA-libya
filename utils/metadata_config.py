"""
Configuration settings for metadata handling throughout the application.
This file serves as a single source of truth for metadata field definitions.
"""

# Fields that should be excluded from risk calculations and displays
# These fields contain metadata rather than actual risk values
EXCLUDED_RISK_FIELDS = [
    'tribal_status',
    'tribal_counties',
    'tribal_primary_county'
]

def is_metadata_field(field_name):
    """
    Check if a field name is a metadata field that should be excluded from risk calculations.
    
    Args:
        field_name (str): The name of the field to check
        
    Returns:
        bool: True if the field is a metadata field, False otherwise
    """
    return field_name in EXCLUDED_RISK_FIELDS