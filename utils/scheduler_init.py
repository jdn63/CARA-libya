"""
Scheduler Initialization Module

This module handles initialization of the data refresh scheduler.
It is designed to be imported by the main application and provides
controlled startup and status reporting for the scheduler system.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Initialization state
_init_thread = None
_init_complete = False
_init_error = None

def _delayed_scheduler_start(delay_seconds: int = 10):
    """
    Start the data refresh scheduler after a delay
    
    This function is meant to be called in a background thread to prevent
    blocking the application startup while the scheduler initializes.
    
    Args:
        delay_seconds: Number of seconds to wait before starting the scheduler
    """
    global _init_complete, _init_error
    
    try:
        logger.info(f"Waiting {delay_seconds} seconds before starting data refresh scheduler")
        time.sleep(delay_seconds)
        
        logger.info("Initializing data refresh scheduler")
        
        # Import the scheduler module
        from utils.data_refresh_scheduler import initialize, start_scheduler, get_scheduler_status
        
        # Initialize the scheduler
        initialize()
        
        # Start the scheduler in a background thread
        start_scheduler(run_in_background=True)
        
        # Get scheduler status
        status = get_scheduler_status()
        logger.info(f"Successfully started data refresh scheduler")
        logger.info(f"Scheduler status: running={status.get('running', False)}")
        logger.info(f"Monitoring {len(status.get('sources', []))} data sources")
        
        _init_complete = True
        _init_error = None
        
    except Exception as e:
        logger.error(f"Error initializing data refresh scheduler: {str(e)}")
        _init_complete = True
        _init_error = str(e)

def start_scheduler_with_delay(delay_seconds: int = 10):
    """
    Start the data refresh scheduler in a background thread after a delay
    
    Args:
        delay_seconds: Number of seconds to wait before starting the scheduler
        
    Returns:
        True if initialization started, False if already in progress
    """
    global _init_thread, _init_complete
    
    if _init_thread is not None and _init_thread.is_alive():
        logger.info("Scheduler initialization already in progress")
        return False
    
    if _init_complete:
        logger.info("Scheduler initialization already complete")
        return False
    
    # Start in a background thread
    _init_thread = threading.Thread(target=_delayed_scheduler_start, args=(delay_seconds,))
    _init_thread.daemon = True
    _init_thread.start()
    
    return True

def get_init_status() -> Dict[str, Any]:
    """
    Get the status of the scheduler initialization
    
    Returns:
        Dictionary with initialization status
    """
    global _init_thread, _init_complete, _init_error
    
    if _init_thread is None:
        return {
            "status": "not_started",
            "error": None,
            "complete": False
        }
    
    if _init_complete:
        if _init_error is None:
            return {
                "status": "complete",
                "error": None,
                "complete": True
            }
        else:
            return {
                "status": "error",
                "error": _init_error,
                "complete": True
            }
    
    return {
        "status": "in_progress",
        "error": None,
        "complete": False
    }

def is_scheduler_running() -> bool:
    """
    Check if the scheduler is running
    
    Returns:
        True if the scheduler is running, False otherwise
    """
    try:
        from utils.data_refresh_scheduler import get_scheduler_status
        status = get_scheduler_status()
        return status.get('running', False)
    except Exception as e:
        logger.warning(f"Could not check scheduler status: {e}")
        return False