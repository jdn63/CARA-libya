"""
API helper utilities for managing API connectivity and errors

This module provides utilities to handle API timeouts, errors,
and connectivity issues when interacting with external APIs.
"""
import logging
import time
from functools import wraps
from typing import TypeVar, Callable, Dict, Tuple, Optional, Any, Union

logger = logging.getLogger(__name__)

# Type variables for generic decorator
T = TypeVar('T')

def with_api_error_handling(max_retries: int = 1, retry_delay: float = 1.0):
    """
    Decorator to handle API errors and retry requests
    
    Args:
        max_retries: Maximum number of retry attempts (default: 1)
        retry_delay: Delay between retries in seconds (default: 1.0)
        
    Returns:
        Decorator function to handle API errors
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Tuple[bool, Union[T, str]]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Tuple[bool, Union[T, str]]:
            retry_count = 0
            last_error = None
            
            while retry_count <= max_retries:
                try:
                    # Attempt to call the function
                    result = func(*args, **kwargs)
                    return True, result
                except (ValueError, KeyError, TypeError, ConnectionError) as e:
                    # Log specific error types for better debugging
                    error_type = type(e).__name__
                    logger.error(f"API error ({error_type}) in {func.__name__}: {str(e)}")
                    last_error = f"{error_type}: {str(e)}"
                    
                    # Increment retry count
                    retry_count += 1
                    
                    # If we've reached max retries, break
                    if retry_count > max_retries:
                        break
                    
                    # Wait before retrying
                    logger.info(f"Retrying {func.__name__} in {retry_delay} seconds (attempt {retry_count}/{max_retries})")
                    time.sleep(retry_delay)
            
            # Return error if all retries failed
            return False, last_error or "Unknown error occurred"
        
        return wrapper
    
    return decorator


def check_api_keys(required_keys: Dict[str, str]) -> Tuple[bool, Dict[str, bool], Optional[str]]:
    """
    Check if required API keys are available in environment variables
    
    Args:
        required_keys: Dictionary mapping key names to descriptions, e.g. {'CENSUS_API_KEY': 'Census Bureau API'}
        
    Returns:
        Tuple of (all_keys_available, individual_key_status, error_message)
    """
    import os
    
    individual_status = {}
    missing_keys = []
    
    # Check each key
    for key, description in required_keys.items():
        if not os.environ.get(key):
            individual_status[key] = False
            missing_keys.append(f"{description} ({key})")
        else:
            individual_status[key] = True
    
    # All keys are available if we have no missing keys
    all_available = len(missing_keys) == 0
    
    # Create error message if keys are missing
    error_message = None
    if not all_available:
        error_message = f"Missing API keys: {', '.join(missing_keys)}"
        logger.error(error_message)
    
    return all_available, individual_status, error_message


def format_api_error(api_name: str, error: str) -> str:
    """
    Format an API error message for user-friendly display
    
    Args:
        api_name: Name of the API that encountered an error
        error: Error message
        
    Returns:
        Formatted error message
    """
    return f"Error accessing {api_name}: {error}. Please check connectivity and try again later."


def extract_api_response_data(response_data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely extract nested data from an API response
    
    Args:
        response_data: API response data dictionary
        *keys: Sequence of keys to traverse through the nested dictionary
        default: Default value to return if path not found
        
    Returns:
        Extracted data or default value
    """
    current = response_data
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError, IndexError):
        return default
