"""
API Key Management and External Service Health Monitoring

This module provides centralized API key validation, retry logic for API failures,
and health check endpoints for external services used in the CARA application.
"""

import os
import logging
import time
import threading
import requests
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Centralized API key management and validation"""
    
    def __init__(self):
        self.api_keys = {
            'CENSUS_API_KEY': os.environ.get('CENSUS_API_KEY'),
            'OPENWEATHERMAP_API_KEY': os.environ.get('OPENWEATHERMAP_API_KEY'),
            'FBI_CRIME_DATA_API_KEY': os.environ.get('FBI_CRIME_DATA_API_KEY'),
            'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
            'AIRNOW_API_KEY': os.environ.get('AIRNOW_API_KEY'),
        }
        self.validation_cache = {}
        self._lock = threading.Lock()
        self.cache_duration = 3600
        
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        return self.api_keys.get(service)
    
    def is_key_available(self, service: str) -> bool:
        """Check if API key is available for a service"""
        key = self.get_api_key(service)
        return key is not None and key.strip() != ""
    
    def validate_key(self, service: str, force_refresh: bool = False) -> Tuple[bool, str]:
        """
        Validate an API key by making a test request
        
        Args:
            service: Service name (e.g., 'CENSUS_API_KEY')
            force_refresh: Force validation even if cached
            
        Returns:
            Tuple of (is_valid, status_message)
        """
        cache_key = f"{service}_validation"
        with self._lock:
            if not force_refresh and cache_key in self.validation_cache:
                cached_time, cached_result = self.validation_cache[cache_key]
                if time.time() - cached_time < self.cache_duration:
                    return cached_result
        
        if not self.is_key_available(service):
            result = (False, "API key not configured")
            with self._lock:
                self.validation_cache[cache_key] = (time.time(), result)
            return result
        
        api_key = self.get_api_key(service)
        if not api_key:
            result = (False, "API key is empty or None")
            with self._lock:
                self.validation_cache[cache_key] = (time.time(), result)
            return result
        
        try:
            if service == 'CENSUS_API_KEY':
                result = self._validate_census_key(api_key)
            elif service == 'OPENWEATHERMAP_API_KEY':
                result = self._validate_openweather_key(api_key)
            elif service == 'FBI_CRIME_DATA_API_KEY':
                result = self._validate_fbi_key(api_key)
            elif service == 'OPENAI_API_KEY':
                result = self._validate_openai_key(api_key)
            elif service == 'AIRNOW_API_KEY':
                result = self._validate_airnow_key(api_key)
            else:
                result = (False, f"Unknown service: {service}")
                
            with self._lock:
                self.validation_cache[cache_key] = (time.time(), result)
            return result
            
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            error_type = type(e).__name__
            logger.error(f"Error validating {service} ({error_type}): {e}")
            result = (False, f"Validation error ({error_type}): {str(e)}")
            with self._lock:
                self.validation_cache[cache_key] = (time.time(), result)
            return result
    
    def _validate_census_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate Census Bureau API key"""
        try:
            url = f"https://api.census.gov/data/2022/acs/acs5?get=NAME&for=state:55&key={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return (True, "Census API key valid")
            elif response.status_code == 400:
                return (False, "Invalid Census API key")
            else:
                return (False, f"Census API returned status {response.status_code}")
                
        except requests.RequestException as e:
            return (False, f"Census API connection error: {str(e)}")
    
    def _validate_openweather_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate OpenWeatherMap API key"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q=Madison,WI,US&appid={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return (True, "OpenWeatherMap API key valid")
            elif response.status_code == 401:
                return (False, "Invalid OpenWeatherMap API key")
            else:
                return (False, f"OpenWeatherMap API returned status {response.status_code}")
                
        except requests.RequestException as e:
            return (False, f"OpenWeatherMap API connection error: {str(e)}")
    
    def _validate_fbi_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate FBI Crime Data API key"""
        try:
            # FBI API endpoint for testing
            url = f"https://api.fbi.gov/wanted/v1/list?page=1"
            headers = {'X-API-KEY': api_key}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return (True, "FBI Crime Data API key valid")
            elif response.status_code == 401:
                return (False, "Invalid FBI Crime Data API key")
            else:
                return (False, f"FBI API returned status {response.status_code}")
                
        except requests.RequestException as e:
            return (False, f"FBI API connection error: {str(e)}")
    
    def _validate_openai_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate OpenAI API key"""
        try:
            url = "https://api.openai.com/v1/models"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return (True, "OpenAI API key valid")
            elif response.status_code == 401:
                return (False, "Invalid OpenAI API key")
            else:
                return (False, f"OpenAI API returned status {response.status_code}")
                
        except requests.RequestException as e:
            return (False, f"OpenAI API connection error: {str(e)}")
    
    def _validate_airnow_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate AirNow API key"""
        try:
            # Test with Madison, WI coordinates
            url = "https://www.airnowapi.org/aq/observation/latLong/current/"
            params = {
                'format': 'application/json',
                'latitude': 43.0731,
                'longitude': -89.4012,
                'distance': 25,
                'API_KEY': api_key
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return (True, "AirNow API key valid")
            elif response.status_code == 401:
                return (False, "Invalid AirNow API key")
            elif response.status_code == 403:
                return (False, "AirNow API key access denied")
            else:
                return (False, f"AirNow API returned status {response.status_code}")
                
        except requests.RequestException as e:
            return (False, f"AirNow API connection error: {str(e)}")
    
    def get_all_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get validation status for all configured services"""
        status = {}
        for service in self.api_keys.keys():
            is_valid, message = self.validate_key(service)
            status[service] = {
                'configured': self.is_key_available(service),
                'valid': is_valid,
                'status': message,
                'last_checked': datetime.utcnow().isoformat()
            }
        return status


class APIRetryManager:
    """Automatic retry logic for API failures"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        
    def retry_api_call(self, func, *args, **kwargs):
        """
        Retry an API call with exponential backoff
        
        Args:
            func: Function to retry
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Function result or raises the last exception
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"API call failed after {self.max_retries} retries: {e}")
                    raise e
                
                delay = self.base_delay * (self.backoff_factor ** attempt)
                logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                time.sleep(delay)
        
        if last_exception:
            raise last_exception
        raise Exception("Unknown error in retry logic")


def api_key_required(service: str):
    """
    Decorator to ensure API key is available before making API calls
    
    Args:
        service: Service name (e.g., 'CENSUS_API_KEY')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_manager = APIKeyManager()
            if not api_manager.is_key_available(service):
                logger.error(f"API key not available for {service}")
                raise ValueError(f"API key not configured for {service}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_retry(max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator to add retry logic to API calls
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        backoff_factor: Exponential backoff factor
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = APIRetryManager(max_retries, base_delay, backoff_factor)
            return retry_manager.retry_api_call(func, *args, **kwargs)
        return wrapper
    return decorator


# Global instances
api_key_manager = APIKeyManager()
retry_manager = APIRetryManager()