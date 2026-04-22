"""
Standardized API Response Utilities

This module provides consistent JSON response formats for all API endpoints.
Ensures uniform error handling and success responses across the application.
"""

from flask import jsonify
from typing import Any, Dict, Optional


def api_success(data: Any = None, message: str = "Success"):
    """
    Create a standardized API success response.
    
    Args:
        data: The data payload to return (optional)
        message: Success message (default: "Success")
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
        
    return jsonify(response), 200


def api_error(error: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
    """
    Create a standardized API error response.
    
    Args:
        error: Descriptive error message
        status_code: HTTP status code (default: 400)
        details: Optional additional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "success": False,
        "error": error
    }
    
    if details:
        response["details"] = details
        
    return jsonify(response), status_code


def api_not_found(resource: str = "Resource"):
    """
    Create a standardized 404 not found response.
    
    Args:
        resource: The type of resource that wasn't found
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_error(f"{resource} not found", 404)


def api_server_error(error: str = "An internal server error occurred"):
    """
    Create a standardized 500 server error response.
    
    Args:
        error: Error message
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_error(error, 500)


def api_unauthorized(error: str = "Authentication required"):
    """
    Create a standardized 401 unauthorized response.
    
    Args:
        error: Error message
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_error(error, 401)


def api_forbidden(error: str = "Access forbidden"):
    """
    Create a standardized 403 forbidden response.
    
    Args:
        error: Error message
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_error(error, 403)


def api_rate_limited(error: str = "Rate limit exceeded"):
    """
    Create a standardized 429 rate limit response.
    
    Args:
        error: Error message
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return api_error(error, 429)