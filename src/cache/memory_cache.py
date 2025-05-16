"""
In-memory cache implementation.
"""

import hashlib
import json
import sys
import threading
import time
from typing import Any, Dict, Optional, Tuple


class MemoryCache:
    """
    A simple in-memory cache implementation.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize the cache with a default time-to-live (TTL) for cached items.

        Args:
            default_ttl (int): Default TTL in seconds for cached items.
        """
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats: Dict[str, Dict[str, int]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key (str): The key to retrieve from the cache.
        """

        with self._lock:
            if key not in self._cache:
                # Track miss
                if key not in self._stats:
                    self._stats[key] = {"hits": 0, "misses": 0}
                self._stats[key]["misses"] += 1
                return None

            value, expiry = self._cache[key]
            if expiry < time.time():
                # Track miss due to expiry
                if key not in self._stats:
                    self._stats[key] = {"hits": 0, "misses": 0}
                self._stats[key]["misses"] += 1
                del self._cache[key]
                return None

            # Track hit
            if key not in self._stats:
                self._stats[key] = {"hits": 0, "misses": 0}
            self._stats[key]["hits"] += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set a value in the cache with an optional TTL.

        Args:
            key (str): The key to set in the cache.
            value (Any): The value to store in the cache.
            ttl (Optional[int]): Time-to-live in seconds for the cached item.
                                 If None, uses the default TTL.
        """
        with self._lock:
            expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
            self._cache[key] = (value, expiry)

    def delete(self, key: str):
        """
        Delete a value from the cache.

        Args:
            key (str): The key to delete from the cache.

        Returns:
            True if the key was deleted, False if it was not found.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return False
            return True

    def clear(self):
        """
        Clear the entire cache.
        """
        with self._lock:
            self._cache.clear()
            # We don't clear statistics when clearing the cache
            # so that overall stats are maintained between cache clears

    def clean_expired(self):
        """
        Remove expired items from the cache.

        Returns:
            Number of expired items removed.
        """
        now = time.time()
        removed = 0
        with self._lock:
            expired_keys = [
                key for key, (_, expiry) in self._cache.items() if expiry < now
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics including hits and misses for each key.
        """
        with self._lock:
            total = len(self._cache)
            now = time.time()
            expired = sum(1 for _, expiry in self._cache.values() if expiry < now)

            # Calculate overall hits and misses
            total_hits = sum(stats["hits"] for stats in self._stats.values())
            total_misses = sum(stats["misses"] for stats in self._stats.values())

            # Prepare detailed stats by key
            key_stats = {}
            for key, stats in self._stats.items():
                hits = stats["hits"]
                misses = stats["misses"]
                total_requests = hits + misses
                hit_rate = hits / total_requests if total_requests > 0 else 0

                key_stats[key] = {
                    "hits": hits,
                    "misses": misses,
                    "total_requests": total_requests,
                    "hit_rate": hit_rate,
                }

            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "memory_usage": self._estimate_size(),
                "total_hits": total_hits,
                "total_misses": total_misses,
                "hit_rate": (
                    total_hits / (total_hits + total_misses)
                    if (total_hits + total_misses) > 0
                    else 0
                ),
                "keys": key_stats,
            }

    def _estimate_size(self) -> int:
        """
        Estimate the size of the cache in bytes.

        Returns:
            Estimated size in bytes.
        """
        total_size = sys.getsizeof(self._cache)

        for key, (value, expiry) in self._cache.items():
            total_size += (
                sys.getsizeof(key) + sys.getsizeof(value) + sys.getsizeof(expiry)
            )

        return total_size

    @staticmethod
    def get_cache_key(method: str, params: Dict[str, Any] = None):
        """
        Generate a cache key for the query parameters of a method.

        Args:
            method (str): The method for the cache key.
            params (Dict[str,Any]: The dictionary with the params of the method to create de the cache key.

        Returns:
            str: The generated cache key.
        """

        params_str = json.dumps(params, sort_keys=True)
        return f"{method}:{hashlib.md5(params_str.encode()).hexdigest()}"
