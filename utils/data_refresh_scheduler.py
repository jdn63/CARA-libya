"""
Data Refresh Scheduler Module

This module implements a configurable scheduler for refreshing various data sources at appropriate intervals:
- Daily: Weather patterns and forecasts
- Weekly: Disease surveillance data from health departments
- Monthly: Seasonal forecasts and vaccination rates
- Quarterly: Social Vulnerability Index and crime statistics
- Annually: Census demographic data and climate projections
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional, Callable

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Path to scheduler configuration
SCHEDULER_CONFIG_PATH = "./data/config/scheduler_config.json"

# Global scheduler state
_scheduler_running = False
_scheduler_thread = None
_scheduler_status = {}
_scheduler_jobs = {}
_refresh_timestamps = {}
_refresh_in_progress = {}

def load_scheduler_config() -> Dict[str, Any]:
    """
    Load scheduler configuration from JSON file
    """
    # Ensure config directory exists
    os.makedirs(os.path.dirname(SCHEDULER_CONFIG_PATH), exist_ok=True)
    
    # Check if config file exists
    if not os.path.exists(SCHEDULER_CONFIG_PATH):
        # Create default config
        default_config = {
            "data_sources": {
                "weather_patterns": {
                    "description": "Current weather conditions and alerts",
                    "refresh_interval_hours": 24,  # Daily
                    "module": "utils.weather_alerts",
                    "function": "refresh_weather_data"
                },
                "disease_surveillance": {
                    "description": "Infectious disease activity data from health departments",
                    "refresh_interval_hours": 168,  # Weekly
                    "module": "utils.disease_surveillance",
                    "function": "refresh_disease_data"
                },
                "seasonal_forecasts": {
                    "description": "Seasonal weather forecasts",
                    "refresh_interval_hours": 720,  # Monthly (30 days)
                    "module": "utils.seasonal_forecasts",
                    "function": "refresh_seasonal_data"
                },
                "vaccination_rates": {
                    "description": "Vaccination coverage rates",
                    "refresh_interval_hours": 720,  # Monthly (30 days)
                    "module": "utils.vaccination_data",
                    "function": "refresh_vaccination_data"
                },
                "svi_data": {
                    "description": "Social Vulnerability Index data",
                    "refresh_interval_hours": 2160,  # Quarterly (90 days)
                    "module": "utils.svi_data",
                    "function": "refresh_svi_data"
                },
                "crime_statistics": {
                    "description": "Crime statistics from FBI UCR and local sources",
                    "refresh_interval_hours": 2160,  # Quarterly (90 days)
                    "module": "utils.crime_statistics",
                    "function": "refresh_crime_data"
                },
                "census_data": {
                    "description": "Census demographic data",
                    "refresh_interval_hours": 8760,  # Annually (365 days)
                    "module": "utils.census_data",
                    "function": "refresh_census_data"
                },
                "climate_projections": {
                    "description": "Climate change projections",
                    "refresh_interval_hours": 8760,  # Annually (365 days)
                    "module": "utils.climate_projections",
                    "function": "refresh_climate_data"
                },
                "herc_risk_cache": {
                    "description": "HERC region pre-computed risk data",
                    "refresh_interval_hours": 4,  # Every 4 hours
                    "module": "utils.herc_risk_aggregator",
                    "function": "precompute_all_herc_regions"
                },
                "openfema_declarations": {
                    "description": "Federal disaster declarations per county from OpenFEMA",
                    "refresh_interval_hours": 168,  # Weekly
                    "module": "utils.data_source_refresher",
                    "function": "refresh_all_openfema_declarations"
                },
                "openfema_nfip": {
                    "description": "NFIP flood insurance claims per county from OpenFEMA",
                    "refresh_interval_hours": 168,  # Weekly
                    "module": "utils.data_source_refresher",
                    "function": "refresh_all_openfema_nfip"
                },
                "openfema_hma": {
                    "description": "Hazard mitigation projects per county from OpenFEMA",
                    "refresh_interval_hours": 168,  # Weekly
                    "module": "utils.data_source_refresher",
                    "function": "refresh_all_openfema_hma"
                },
                "noaa_storm_events": {
                    "description": "Historical severe weather events from NOAA NCEI",
                    "refresh_interval_hours": 168,  # Weekly
                    "module": "utils.data_source_refresher",
                    "function": "refresh_all_noaa_storm_events"
                }
            }
        }
        
        # Save default config
        with open(SCHEDULER_CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        logger.info(f"Created default scheduler configuration at {SCHEDULER_CONFIG_PATH}")
        
        return default_config
    
    # Load existing config
    try:
        with open(SCHEDULER_CONFIG_PATH, 'r') as f:
            config = json.load(f)
            
        logger.info(f"Loaded scheduler configuration from {SCHEDULER_CONFIG_PATH}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading scheduler configuration: {str(e)}")
        return {"data_sources": {}}

def load_scheduler_status():
    """
    Load scheduler status from global variables or initialize with defaults
    """
    global _scheduler_status, _refresh_timestamps, _refresh_in_progress
    
    # Load configuration
    config = load_scheduler_config()
    
    # Initialize status for each data source
    for source_id, source_config in config.get("data_sources", {}).items():
        if source_id not in _scheduler_status:
            _scheduler_status[source_id] = {
                "last_refresh": None,
                "next_refresh": None,
                "status": "pending",
                "last_error": None,
                "refresh_count": 0,
                "error_count": 0
            }
            
        if source_id not in _refresh_timestamps:
            _refresh_timestamps[source_id] = None
            
        if source_id not in _refresh_in_progress:
            _refresh_in_progress[source_id] = False
            
    logger.info(f"Loaded scheduler status for {len(_scheduler_status)} data sources")

def get_scheduler_status() -> Dict[str, Any]:
    """
    Get the current status of the scheduler
    
    Returns:
        Dictionary with scheduler status
    """
    global _scheduler_running, _scheduler_status
    
    # Load configuration
    config = load_scheduler_config()
    
    # Build status response
    sources_status = []
    for source_id, source_config in config.get("data_sources", {}).items():
        status = _scheduler_status.get(source_id, {})
        
        sources_status.append({
            "id": source_id,
            "description": source_config.get("description", "Unknown data source"),
            "refresh_interval_hours": source_config.get("refresh_interval_hours", 24),
            "last_refresh": status.get("last_refresh"),
            "next_refresh": status.get("next_refresh"),
            "status": status.get("status", "pending"),
            "last_error": status.get("last_error"),
            "refresh_count": status.get("refresh_count", 0),
            "error_count": status.get("error_count", 0),
            "in_progress": _refresh_in_progress.get(source_id, False)
        })
    
    return {
        "running": _scheduler_running,
        "sources": sources_status
    }

def start_scheduler(run_in_background: bool = True) -> bool:
    """
    Start the data refresh scheduler
    
    Args:
        run_in_background: If True, run the scheduler in a background thread
        
    Returns:
        True if the scheduler was started, False if it was already running
    """
    global _scheduler_running, _scheduler_thread
    
    if _scheduler_running:
        logger.info("Scheduler is already running")
        return False
    
    # Load scheduler status
    load_scheduler_status()
    
    # Start the scheduler
    _scheduler_running = True
    
    if run_in_background:
        # Start in a background thread
        _scheduler_thread = threading.Thread(target=scheduler_loop)
        _scheduler_thread.daemon = True
        _scheduler_thread.start()
        logger.info("Started data refresh scheduler in background")
    else:
        # Start in the current thread
        scheduler_loop()
    
    return True

def stop_scheduler() -> bool:
    """
    Stop the data refresh scheduler
    
    Returns:
        True if the scheduler was stopped, False if it wasn't running
    """
    global _scheduler_running
    
    if not _scheduler_running:
        logger.info("Scheduler is not running")
        return False
    
    # Stop the scheduler
    _scheduler_running = False
    logger.info("Stopping data refresh scheduler")
    
    return True

def refresh_now(source: str) -> bool:
    """
    Trigger an immediate refresh of a data source
    
    Args:
        source: The name of the data source to refresh
        
    Returns:
        True if the refresh was started, False if the source wasn't found
    """
    # Load configuration
    config = load_scheduler_config()
    
    # Check if source exists
    if source not in config.get("data_sources", {}):
        logger.error(f"Data source '{source}' not found")
        return False
    
    # Refresh the data source
    success, message = refresh_data_source(source)
    
    if success:
        logger.info(f"Started refresh for {source}")
    else:
        logger.error(f"Error refreshing {source}: {message}")
    
    return success

def refresh_data_source(source: str) -> Tuple[bool, str]:
    """
    Refresh a data source
    
    Args:
        source: The name of the data source to refresh
        
    Returns:
        Tuple of (success, message)
    """
    global _scheduler_status, _refresh_timestamps, _refresh_in_progress
    
    # Load configuration
    config = load_scheduler_config()
    
    # Check if source exists
    if source not in config.get("data_sources", {}):
        return False, f"Data source '{source}' not found"
    
    # Check if already in progress
    if _refresh_in_progress.get(source, False):
        return False, f"Refresh already in progress for '{source}'"
    
    # Get source configuration
    source_config = config["data_sources"][source]
    
    # Mark refresh as in progress
    _refresh_in_progress[source] = True
    
    try:
        # Update status
        if source not in _scheduler_status:
            _scheduler_status[source] = {
                "last_refresh": None,
                "next_refresh": None,
                "status": "pending",
                "last_error": None,
                "refresh_count": 0,
                "error_count": 0
            }
        
        # Get module and function
        module_name = source_config.get("module")
        function_name = source_config.get("function")
        
        if not module_name or not function_name:
            _refresh_in_progress[source] = False
            _scheduler_status[source]["status"] = "error"
            _scheduler_status[source]["last_error"] = "Module or function name not specified"
            _scheduler_status[source]["error_count"] += 1
            return False, "Module or function name not specified"
        
        # Import the module dynamically
        try:
            # Special case for disease surveillance module
            if source == "disease_surveillance":
                from utils.disease_surveillance import clear_disease_cache
                clear_disease_cache()
                success = True
                
            # Special case for SVI data module
            elif source == "svi_data":
                from utils.svi_data import clear_svi_cache
                clear_svi_cache()
                success = True
                
            # Default case: try to import the specified module and function
            else:
                module = __import__(module_name, fromlist=[''])
                function = getattr(module, function_name)
                success = function()
                
            # Update status on success
            if success:
                now = datetime.now()
                refresh_interval = timedelta(hours=source_config.get("refresh_interval_hours", 24))
                next_refresh = now + refresh_interval
                
                _scheduler_status[source]["last_refresh"] = now.isoformat()
                _scheduler_status[source]["next_refresh"] = next_refresh.isoformat()
                _scheduler_status[source]["status"] = "success"
                _scheduler_status[source]["last_error"] = None
                _scheduler_status[source]["refresh_count"] += 1
                _refresh_timestamps[source] = now
                
                _refresh_in_progress[source] = False
                return True, "Refresh completed successfully"
            else:
                # Update status on failure
                _scheduler_status[source]["status"] = "error"
                _scheduler_status[source]["last_error"] = "Function returned False"
                _scheduler_status[source]["error_count"] += 1
                
                _refresh_in_progress[source] = False
                return False, "Function returned False"
                
        except Exception as e:
            # Update status on exception
            _scheduler_status[source]["status"] = "error"
            _scheduler_status[source]["last_error"] = str(e)
            _scheduler_status[source]["error_count"] += 1
            
            _refresh_in_progress[source] = False
            return False, str(e)
            
    except Exception as e:
        # Update status on outer exception
        if source in _scheduler_status:
            _scheduler_status[source]["status"] = "error"
            _scheduler_status[source]["last_error"] = str(e)
            _scheduler_status[source]["error_count"] += 1
        
        _refresh_in_progress[source] = False
        return False, str(e)

def scheduler_loop():
    """
    Main scheduler loop
    """
    global _scheduler_running, _scheduler_status, _refresh_timestamps
    
    logger.info("Starting scheduler loop")
    
    # Initialize status
    load_scheduler_status()
    
    while _scheduler_running:
        try:
            # Load configuration
            config = load_scheduler_config()
            
            # Get current time
            now = datetime.now()
            logger.info(f"Checking all data sources for refresh at {now.isoformat()}")
            
            # Check each data source
            for source_id, source_config in config.get("data_sources", {}).items():
                # Skip if refresh is already in progress
                if _refresh_in_progress.get(source_id, False):
                    continue
                
                # Get last refresh timestamp
                last_refresh = _refresh_timestamps.get(source_id)
                
                # Calculate next refresh time
                refresh_interval = timedelta(hours=source_config.get("refresh_interval_hours", 24))
                
                # Check if refresh is needed
                if last_refresh is None or now - last_refresh >= refresh_interval:
                    logger.info(f"Refreshing data source: {source_id}")
                    
                    # Refresh in a separate thread
                    thread = threading.Thread(
                        target=lambda: refresh_data_source(source_id)
                    )
                    thread.daemon = True
                    thread.start()
                    
            # Sleep for a while
            time.sleep(300)  # Check every 5 minutes
            
        except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
            error_type = type(e).__name__
            logger.error(f"Error in scheduler loop ({error_type}): {str(e)}")
            time.sleep(60)  # Wait a bit longer on error
        except Exception as e:
            # Catch-all for unexpected errors to prevent scheduler crash
            logger.critical(f"Unexpected error in scheduler loop: {type(e).__name__}: {str(e)}")
            time.sleep(300)  # Wait longer for unexpected errors
    
    logger.info("Scheduler loop stopped")

def initialize():
    """Initialize the data refresh scheduler module"""
    # Load configuration
    load_scheduler_config()
    
    # Load status
    load_scheduler_status()
    
    logger.info("Data refresh scheduler initialized")