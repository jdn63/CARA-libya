"""
Persistent cache module for long-term data caching.

Uses JSON serialization (not pickle) and SHA-256 cache keys.
Suitable for caching dicts, lists, strings, and numbers from external sources.
"""

import os
import json
import logging
import hashlib
import glob
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_DIR = "./data/cache"
MAX_CACHE_FILE_AGE = 30

os.makedirs(CACHE_DIR, exist_ok=True)


class _DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"__datetime__": obj.isoformat()}
        return super().default(obj)


def _datetime_decoder(d):
    if "__datetime__" in d:
        return datetime.fromisoformat(d["__datetime__"])
    return d


def _get_cache_key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def get_from_persistent_cache(key: str, max_age_days: int = MAX_CACHE_FILE_AGE) -> Optional[Any]:
    key_hash = _get_cache_key_hash(key)
    cache_path = os.path.join(CACHE_DIR, f"{key_hash}.cache")

    if not os.path.exists(cache_path):
        return None

    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
    if file_age > timedelta(days=max_age_days):
        logger.info(f"Cache for '{key}' is {file_age.days} days old (max: {max_age_days})")
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f, object_hook=_datetime_decoder)

        expiry_time = data.get('expiry')
        if expiry_time and datetime.now() > expiry_time:
            logger.info(f"Cache for '{key}' expired at {expiry_time}")
            return None

        return data.get('value')
    except Exception as e:
        logger.error(f"Error reading cache for '{key}': {e}")
        return None


def set_in_persistent_cache(key: str, value: Any, expiry_days: int = MAX_CACHE_FILE_AGE) -> bool:
    try:
        key_hash = _get_cache_key_hash(key)
        cache_path = os.path.join(CACHE_DIR, f"{key_hash}.cache")

        data = {
            'key': key,
            'value': value,
            'created': datetime.now(),
            'expiry': datetime.now() + timedelta(days=expiry_days),
        }

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=_DatetimeEncoder)

        logger.info(f"Cached '{key}' for {expiry_days} days")
        return True
    except Exception as e:
        logger.error(f"Error writing cache for '{key}': {e}")
        return False


def clear_cache_by_prefix(prefix: str) -> int:
    count = 0
    try:
        for cache_path in glob.glob(os.path.join(CACHE_DIR, "*.cache")):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=_datetime_decoder)
                if data.get('key', '').startswith(prefix):
                    os.remove(cache_path)
                    count += 1
            except Exception as e:
                logger.error(f"Error checking cache file {cache_path}: {e}")
        logger.info(f"Cleared {count} cache entries with prefix '{prefix}'")
    except Exception as e:
        logger.error(f"Error clearing cache prefix '{prefix}': {e}")
    return count


def clear_all_cache() -> int:
    count = 0
    try:
        for cache_path in glob.glob(os.path.join(CACHE_DIR, "*.cache")):
            try:
                os.remove(cache_path)
                count += 1
            except Exception as e:
                logger.error(f"Error removing {cache_path}: {e}")
        logger.info(f"Cleared all {count} persistent cache entries")
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")
    return count


class PersistentCache:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get(self, key: str, max_age_days: int = MAX_CACHE_FILE_AGE) -> Optional[Any]:
        return get_from_persistent_cache(key, max_age_days)

    def set(self, key: str, value: Any, max_age_days: int = MAX_CACHE_FILE_AGE) -> bool:
        return set_in_persistent_cache(key, value, max_age_days)

    def clear(self, prefix: str = "") -> int:
        return clear_cache_by_prefix(prefix)


def get_cache_stats() -> Dict[str, Any]:
    stats: Dict[str, Any] = {
        'total_entries': 0,
        'total_size_bytes': 0,
        'average_age_days': 0,
        'oldest_entry_days': 0,
        'newest_entry_days': 0,
        'categories': {},
    }
    try:
        cache_files = glob.glob(os.path.join(CACHE_DIR, "*.cache"))
        stats['total_entries'] = len(cache_files)
        if not cache_files:
            return stats

        total_size = 0
        total_age = 0
        oldest = 0
        newest = float('inf')
        categories: Dict[str, Any] = {}
        now = datetime.now()

        for cache_path in cache_files:
            size = os.path.getsize(cache_path)
            total_size += size
            age = (now - datetime.fromtimestamp(os.path.getmtime(cache_path))).days
            total_age += age
            oldest = max(oldest, age)
            newest = min(newest, age)

            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=_datetime_decoder)
                key = data.get('key', '')
                cat = key.split('_')[0] if '_' in key else 'unknown'
                if cat not in categories:
                    categories[cat] = {'count': 0, 'size_bytes': 0}
                categories[cat]['count'] += 1
                categories[cat]['size_bytes'] += size
            except Exception:
                pass

        stats['total_size_bytes'] = total_size
        stats['average_age_days'] = total_age / len(cache_files)
        stats['oldest_entry_days'] = oldest
        stats['newest_entry_days'] = newest if newest != float('inf') else 0
        stats['categories'] = categories
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
    return stats
