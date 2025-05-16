"""
Cache system for the Autosubmit Models API.
"""

from src.cache.memory_cache import MemoryCache

Cache = MemoryCache

__all__ = ["Cache"]
