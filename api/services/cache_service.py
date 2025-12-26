"""Cache service for TTL-based caching of Intervals.icu API data.

Provides a 6-hour TTL cache to reduce API calls to Intervals.icu.
Cache can be invalidated manually after workout sync or via refresh parameter.
"""

import logging
from typing import Any, Optional, Callable
from datetime import datetime
from cachetools import TTLCache
from functools import wraps

logger = logging.getLogger(__name__)

# Default TTL: 6 hours in seconds
DEFAULT_TTL = 6 * 60 * 60  # 21,600 seconds

# Cache key prefixes
CACHE_KEYS = {
    "fitness": "fitness",
    "activities": "activities",
    "profile": "profile",
    "calendar": "calendar",
}

# User-specific caches: user_id -> TTLCache
_user_caches: dict[str, TTLCache] = {}


def get_user_cache(
    user_id: str, maxsize: int = 100, ttl: int = DEFAULT_TTL
) -> TTLCache:
    """Get or create a TTL cache for a specific user.

    Args:
        user_id: The user's unique identifier.
        maxsize: Maximum number of items in the cache.
        ttl: Time-to-live in seconds (default: 6 hours).

    Returns:
        TTLCache instance for the user.
    """
    if user_id not in _user_caches:
        _user_caches[user_id] = TTLCache(maxsize=maxsize, ttl=ttl)
        logger.debug(f"Created new cache for user {user_id[:8]}...")
    return _user_caches[user_id]


def get_cached(user_id: str, cache_key: str) -> Optional[Any]:
    """Get a cached value for a user.

    Args:
        user_id: The user's unique identifier.
        cache_key: The cache key to retrieve.

    Returns:
        Cached value or None if not found/expired.
    """
    cache = get_user_cache(user_id)
    value = cache.get(cache_key)
    if value is not None:
        logger.debug(f"Cache HIT for user {user_id[:8]}... key={cache_key}")
    return value


def set_cached(user_id: str, cache_key: str, value: Any) -> None:
    """Set a cached value for a user.

    Args:
        user_id: The user's unique identifier.
        cache_key: The cache key to store.
        value: The value to cache.
    """
    cache = get_user_cache(user_id)
    cache[cache_key] = value
    logger.debug(f"Cache SET for user {user_id[:8]}... key={cache_key}")


def clear_user_cache(user_id: str, keys: Optional[list[str]] = None) -> None:
    """Clear cache for a specific user.

    Args:
        user_id: The user's unique identifier.
        keys: Optional list of specific keys to clear. If None, clears all.
    """
    if user_id not in _user_caches:
        return

    cache = _user_caches[user_id]

    if keys:
        for key in keys:
            if key in cache:
                del cache[key]
                logger.info(f"Cache cleared for user {user_id[:8]}... key={key}")
    else:
        cache.clear()
        logger.info(f"Cache fully cleared for user {user_id[:8]}...")


def clear_all_caches() -> None:
    """Clear all user caches (for admin/debugging purposes)."""
    global _user_caches
    _user_caches = {}
    logger.info("All user caches cleared")


def get_cache_stats(user_id: str) -> dict:
    """Get cache statistics for a user.

    Args:
        user_id: The user's unique identifier.

    Returns:
        Dictionary with cache statistics.
    """
    if user_id not in _user_caches:
        return {"exists": False, "size": 0, "keys": []}

    cache = _user_caches[user_id]
    return {
        "exists": True,
        "size": len(cache),
        "maxsize": cache.maxsize,
        "ttl": cache.ttl,
        "keys": list(cache.keys()),
    }
