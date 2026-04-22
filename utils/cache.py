"""
Cache utilities for managing in-memory caching

This module provides functions for managing in-memory caches
throughout the application. All operations are thread-safe.
"""
import logging
import time
import threading
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)

MAX_CACHE_SIZE = 1000
DEFAULT_TTL = 3600

_memory_cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
_cache_lock = threading.Lock()

def get_from_memory_cache(key: str) -> Optional[Any]:
    """
    Get a value from the in-memory cache

    Args:
        key: The cache key

    Returns:
        The cached value or None if not found or expired
    """
    with _cache_lock:
        if key not in _memory_cache:
            return None

        value, expiry_time = _memory_cache[key]

        if time.time() > expiry_time:
            del _memory_cache[key]
            return None

        _memory_cache.move_to_end(key)
        return value

def set_in_memory_cache(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """
    Set a value in the in-memory cache

    Args:
        key: The cache key
        value: The value to cache
        ttl: Time to live in seconds
    """
    expiry_time = time.time() + ttl

    with _cache_lock:
        while len(_memory_cache) >= MAX_CACHE_SIZE:
            oldest_key = next(iter(_memory_cache))
            del _memory_cache[oldest_key]
            logger.debug(f"Evicted cache entry: {oldest_key}")

        _memory_cache[key] = (value, expiry_time)

def clear_memory_cache() -> int:
    """
    Clear all in-memory cache entries

    Returns:
        Number of entries cleared
    """
    with _cache_lock:
        count = len(_memory_cache)
        _memory_cache.clear()
    logger.info(f"Cleared {count} entries from in-memory cache")
    return count

def cleanup_expired_cache() -> int:
    """
    Remove expired entries from cache

    Returns:
        Number of expired entries removed
    """
    current_time = time.time()

    with _cache_lock:
        expired_keys = [
            key for key, (_, expiry_time) in _memory_cache.items()
            if current_time > expiry_time
        ]
        for key in expired_keys:
            del _memory_cache[key]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    return len(expired_keys)

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics

    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()

    with _cache_lock:
        total = len(_memory_cache)
        expired_count = sum(
            1 for _, expiry_time in _memory_cache.values()
            if current_time > expiry_time
        )

    return {
        'total_entries': total,
        'expired_entries': expired_count,
        'max_size': MAX_CACHE_SIZE,
        'utilization': total / MAX_CACHE_SIZE
    }

def remove_from_memory_cache(key: str) -> bool:
    """
    Remove a specific key from the in-memory cache

    Args:
        key: The cache key to remove

    Returns:
        True if the key was found and removed, False otherwise
    """
    with _cache_lock:
        if key in _memory_cache:
            del _memory_cache[key]
            return True
    return False
