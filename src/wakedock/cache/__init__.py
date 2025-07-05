"""
Caching system for WakeDock.
Provides in-memory and Redis-backed caching capabilities.
"""

from .backends import MemoryCache, RedisCache, CacheBackend
from .manager import CacheManager, get_cache_manager

__all__ = ["MemoryCache", "RedisCache", "CacheBackend", "CacheManager", "get_cache_manager"]

# Lazy access to cache_manager for backward compatibility
def __getattr__(name):
    if name == "cache_manager":
        return get_cache_manager()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")