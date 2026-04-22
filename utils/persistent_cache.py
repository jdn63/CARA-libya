"""
Persistent cache module for long-term data caching

This module provides file-based long-term caching for infrequently changing datasets.
It's particularly useful for caching data from external sources that don't need
to be refreshed with every request, such as Census data or SVI data.
"""

import os
import json
import pickle
import logging
import hashlib
import glob
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Constants
CACHE_DIR = "./data/cache"  # Directory to store cache files
MAX_CACHE_FILE_AGE = 30  # Default maximum age in days for cache files

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_cache_key_hash(key: str) -> str:
    """
    Generate a hash for the cache key to use as a filename
    
    Args:
        key: The cache key
        
    Returns:
        Hashed key suitable for use as a filename
    """
    return hashlib.md5(key.encode()).hexdigest()

def get_from_persistent_cache(key: str, max_age_days: int = MAX_CACHE_FILE_AGE) -> Optional[Any]:
    """
    Get a value from the persistent cache
    
    Args:
        key: The cache key
        max_age_days: Maximum age in days for the cache to be considered valid
            (default: None, which uses MAX_CACHE_FILE_AGE)
            
    Returns:
        The cached value or None if not found or expired
    """
    # max_age_days has a default value, so no need to check for None
        
    # Hash the key to create a valid filename
    key_hash = _get_cache_key_hash(key)
    cache_path = os.path.join(CACHE_DIR, f"{key_hash}.cache")
    
    # Check if file exists
    if not os.path.exists(cache_path):
        return None
        
    # Check if file is too old
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
    if file_age > timedelta(days=max_age_days):
        logger.info(f"Cache file for key '{key}' is {file_age.days} days old (max: {max_age_days}), considering invalid")
        return None
        
    try:
        with open(cache_path, 'rb') as f:
            # Load metadata and value
            data = pickle.load(f)
            expiry_time = data.get('expiry')
            
            # Check if expired
            if expiry_time and datetime.now() > expiry_time:
                logger.info(f"Cache for key '{key}' has expired at {expiry_time}")
                return None
                
            return data.get('value')
    except Exception as e:
        logger.error(f"Error reading from cache for key '{key}': {str(e)}")
        return None

def set_in_persistent_cache(key: str, value: Any, expiry_days: int = MAX_CACHE_FILE_AGE) -> bool:
    """
    Set a value in the persistent cache
    
    Args:
        key: The cache key
        value: The value to cache
        expiry_days: Number of days before the cache expires
            
    Returns:
        True if successfully cached, False otherwise
    """
    try:
        # Hash the key to create a valid filename
        key_hash = _get_cache_key_hash(key)
        cache_path = os.path.join(CACHE_DIR, f"{key_hash}.cache")
        
        # Calculate expiry time
        expiry_time = datetime.now() + timedelta(days=expiry_days)
        
        # Store value with metadata
        data = {
            'key': key,
            'value': value,
            'created': datetime.now(),
            'expiry': expiry_time
        }
        
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
            
        logger.info(f"Cached data for key '{key}' with expiry in {expiry_days} days")
        return True
    except Exception as e:
        logger.error(f"Error writing to cache for key '{key}': {str(e)}")
        return False

def clear_cache_by_prefix(prefix: str) -> int:
    """
    Clear all cache entries with keys starting with the given prefix
    
    Args:
        prefix: The key prefix to match
            
    Returns:
        Number of entries cleared
    """
    count = 0
    try:
        # List all cache files
        cache_files = glob.glob(os.path.join(CACHE_DIR, "*.cache"))
        
        for cache_path in cache_files:
            try:
                # Load the data to check the original key
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    key = data.get('key', '')
                    
                    # If the key starts with the prefix, delete the file
                    if key.startswith(prefix):
                        os.remove(cache_path)
                        count += 1
            except Exception as e:
                logger.error(f"Error checking/removing cache file {cache_path}: {str(e)}")
                continue
                
        logger.info(f"Cleared {count} cache entries with prefix '{prefix}'")
        return count
    except Exception as e:
        logger.error(f"Error clearing cache with prefix '{prefix}': {str(e)}")
        return count

def clear_all_cache() -> int:
    """
    Clear all persistent cache entries
    
    Returns:
        Number of entries cleared
    """
    count = 0
    try:
        # List all cache files
        cache_files = glob.glob(os.path.join(CACHE_DIR, "*.cache"))
        
        for cache_path in cache_files:
            try:
                os.remove(cache_path)
                count += 1
            except Exception as e:
                logger.error(f"Error removing cache file {cache_path}: {str(e)}")
                continue
                
        logger.info(f"Cleared all {count} persistent cache entries")
        return count
    except Exception as e:
        logger.error(f"Error clearing all cache: {str(e)}")
        return count

class PersistentCache:
    """
    Class-based persistent cache for backward compatibility
    """
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str, max_age_days: int = MAX_CACHE_FILE_AGE) -> Optional[Any]:
        """Get a value from the persistent cache"""
        return get_from_persistent_cache(key, max_age_days)
    
    def set(self, key: str, value: Any, max_age_days: int = MAX_CACHE_FILE_AGE) -> bool:
        """Set a value in the persistent cache"""
        return set_in_persistent_cache(key, value, max_age_days)
    
    def clear(self, prefix: str = "") -> int:
        """Clear cache entries with the given prefix"""
        return clear_cache_by_prefix(prefix)

def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the persistent cache
    
    Returns:
        Dictionary with cache statistics
    """
    stats = {
        'total_entries': 0,
        'total_size_bytes': 0,
        'average_age_days': 0,
        'oldest_entry_days': 0,
        'newest_entry_days': 0,
        'categories': {}
    }
    
    try:
        # List all cache files
        cache_files = glob.glob(os.path.join(CACHE_DIR, "*.cache"))
        stats['total_entries'] = len(cache_files)
        
        if not cache_files:
            return stats
            
        # Calculate sizes and ages
        total_size = 0
        total_age_days = 0
        oldest_age = 0
        newest_age = float('inf')
        categories = {}
        
        now = datetime.now()
        
        for cache_path in cache_files:
            # Get file size
            size = os.path.getsize(cache_path)
            total_size += size
            
            # Get file age
            modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            age_days = (now - modified_time).days
            total_age_days += age_days
            
            oldest_age = max(oldest_age, age_days)
            newest_age = min(newest_age, age_days)
            
            # Load metadata to get category
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    key = data.get('key', '')
                    
                    # Extract category from key (assuming format like "category_subcategory_id")
                    category = key.split('_')[0] if '_' in key else 'unknown'
                    
                    if category not in categories:
                        categories[category] = {
                            'count': 0,
                            'size_bytes': 0
                        }
                        
                    categories[category]['count'] += 1
                    categories[category]['size_bytes'] += size
            except Exception:
                # Skip metadata analysis if file can't be read
                pass
                
        # Calculate averages
        stats['total_size_bytes'] = total_size
        stats['average_age_days'] = total_age_days / len(cache_files) if cache_files else 0
        stats['oldest_entry_days'] = oldest_age
        stats['newest_entry_days'] = newest_age if newest_age != float('inf') else 0
        stats['categories'] = categories
        
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return stats
