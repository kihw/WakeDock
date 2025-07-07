"""
Cache manager for WakeDock.
Provides high-level caching interface with multiple backends and decorators.
"""

import asyncio
import functools
import hashlib
import logging
from typing import Any, Callable, Dict, List, Optional, Union
import inspect
import json

from .backends import CacheBackend, MemoryCache, RedisCache

logger = logging.getLogger(__name__)


class CacheManager:
    """High-level cache manager with multiple backends."""
    
    def __init__(self, default_backend: Optional[CacheBackend] = None):
        self.backends: Dict[str, CacheBackend] = {}
        self.default_backend_name = "memory"
        self._default_backend = default_backend
        
        # Set up default backend lazily
        if default_backend:
            self.backends["default"] = default_backend
            self.default_backend_name = "default"
        # Memory backend will be created on first access
    
    def add_backend(self, name: str, backend: CacheBackend) -> None:
        """Add a cache backend."""
        self.backends[name] = backend
        logger.info(f"Added cache backend: {name}")
    
    def set_default_backend(self, name: str) -> None:
        """Set the default cache backend."""
        if name not in self.backends:
            raise ValueError(f"Backend {name} not found")
        self.default_backend_name = name
        logger.info(f"Set default cache backend to: {name}")
    
    def get_backend(self, name: Optional[str] = None) -> CacheBackend:
        """Get a cache backend by name."""
        backend_name = name or self.default_backend_name
        
        # Create memory backend lazily if needed
        if backend_name == "memory" and backend_name not in self.backends:
            self.backends["memory"] = MemoryCache()
        
        if backend_name not in self.backends:
            raise ValueError(f"Backend {backend_name} not found")
        return self.backends[backend_name]
    
    async def get(self, key: str, backend: Optional[str] = None) -> Optional[Any]:
        """Get value from cache."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        backend: Optional[str] = None
    ) -> bool:
        """Set value in cache."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.set(key, value, ttl)
    
    async def delete(self, key: str, backend: Optional[str] = None) -> bool:
        """Delete key from cache."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.delete(key)
    
    async def exists(self, key: str, backend: Optional[str] = None) -> bool:
        """Check if key exists in cache."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.exists(key)
    
    async def clear(self, backend: Optional[str] = None) -> bool:
        """Clear cache."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.clear()
    
    async def clear_all(self) -> None:
        """Clear all cache backends."""
        for backend in self.backends.values():
            await backend.clear()
    
    async def keys(self, pattern: str = "*", backend: Optional[str] = None) -> List[str]:
        """Get keys matching pattern."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.keys(pattern)
    
    async def size(self, backend: Optional[str] = None) -> int:
        """Get cache size."""
        cache_backend = self.get_backend(backend)
        return await cache_backend.size()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all backends."""
        stats = {}
        for name, backend in self.backends.items():
            if hasattr(backend, 'get_stats'):
                stats[name] = backend.get_stats()
            else:
                stats[name] = {"backend_type": type(backend).__name__}
        return stats
    
    async def cleanup(self) -> None:
        """Cleanup all cache backends."""
        for backend in self.backends.values():
            if hasattr(backend, 'cleanup'):
                await backend.cleanup()


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    # Create a deterministic key from arguments
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    backend: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        backend: Cache backend to use
        key_func: Custom function to generate cache keys
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__qualname__}"
                arg_key = generate_cache_key(*args, **kwargs)
                cache_key = f"{key_prefix}{func_name}:{arg_key}"
            
            # Try to get from cache
            try:
                cached_result = await cache_manager.get(cache_key, backend)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get error for key {cache_key}: {e}")
            
            # Execute function
            logger.debug(f"Cache miss for key: {cache_key}")
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Store in cache
            try:
                await cache_manager.set(cache_key, result, ttl, backend)
                logger.debug(f"Cached result for key: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set error for key {cache_key}: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                raise ValueError("Use async function with @cached decorator")
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__qualname__}"
                arg_key = generate_cache_key(*args, **kwargs)
                cache_key = f"{key_prefix}{func_name}:{arg_key}"
            
            # For sync functions, we need to run async cache operations
            # This is a simplified version - in practice, you might want to use a sync cache
            result = func(*args, **kwargs)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_key(*args, **kwargs):
    """
    Decorator to specify a custom cache key function.
    
    Usage:
        @cache_key(lambda self, user_id: f"user:{user_id}")
        @cached(ttl=300)
        async def get_user(self, user_id):
            ...
    """
    def decorator(func):
        if len(args) == 1 and callable(args[0]):
            # Used as @cache_key(key_function)
            func._cache_key_func = args[0]
        else:
            # Used as @cache_key() - extract from function signature
            func._cache_key_func = lambda *a, **kw: generate_cache_key(*a, **kw)
        return func
    return decorator


class CacheInvalidator:
    """Helper class to manage cache invalidation."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._invalidation_patterns: Dict[str, List[str]] = {}
    
    def register_pattern(self, event: str, pattern: str) -> None:
        """Register a cache pattern to invalidate on event."""
        if event not in self._invalidation_patterns:
            self._invalidation_patterns[event] = []
        self._invalidation_patterns[event].append(pattern)
    
    async def invalidate(self, event: str, **context) -> int:
        """Invalidate cache based on event."""
        if event not in self._invalidation_patterns:
            return 0
        
        total_invalidated = 0
        
        for pattern in self._invalidation_patterns[event]:
            # Format pattern with context
            try:
                formatted_pattern = pattern.format(**context)
            except KeyError:
                formatted_pattern = pattern
            
            # Get matching keys
            keys = await self.cache_manager.keys(formatted_pattern)
            
            # Delete keys
            for key in keys:
                await self.cache_manager.delete(key)
                total_invalidated += 1
        
        if total_invalidated > 0:
            logger.info(f"Invalidated {total_invalidated} cache entries for event: {event}")
        
        return total_invalidated


# Global cache manager instance (lazy initialization)
_cache_manager: Optional[CacheManager] = None
_cache_invalidator: Optional[CacheInvalidator] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_cache_invalidator() -> CacheInvalidator:
    """Get the global cache invalidator instance."""
    global _cache_invalidator
    if _cache_invalidator is None:
        _cache_invalidator = CacheInvalidator(get_cache_manager())
    return _cache_invalidator


# Convenience functions
async def get_cached(key: str, backend: Optional[str] = None) -> Optional[Any]:
    """Get value from global cache manager."""
    return await get_cache_manager().get(key, backend)


async def set_cached(
    key: str,
    value: Any,
    ttl: Optional[int] = None,
    backend: Optional[str] = None
) -> bool:
    """Set value in global cache manager."""
    return await get_cache_manager().set(key, value, ttl, backend)


async def delete_cached(key: str, backend: Optional[str] = None) -> bool:
    """Delete key from global cache manager."""
    return await get_cache_manager().delete(key, backend)


async def clear_cache(backend: Optional[str] = None) -> bool:
    """Clear cache in global cache manager."""
    return await get_cache_manager().clear(backend)


# Cache configuration helpers
def setup_redis_cache(redis_url: str = "redis://localhost:6379/0") -> None:
    """Set up Redis cache backend."""
    redis_cache = RedisCache(redis_url)
    manager = get_cache_manager()
    manager.add_backend("redis", redis_cache)
    manager.set_default_backend("redis")
    logger.info("Redis cache configured as default backend")


def setup_memory_cache(max_size: int = 1000) -> None:
    """Set up memory cache backend."""
    memory_cache = MemoryCache(max_size=max_size)
    manager = get_cache_manager()
    manager.add_backend("memory", memory_cache)
    manager.set_default_backend("memory")
    logger.info("Memory cache configured as default backend")


# Global cache manager instance (lazy initialization)
_cache_manager: Optional[CacheManager] = None
_cache_invalidator: Optional[CacheInvalidator] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_cache_invalidator() -> CacheInvalidator:
    """Get the global cache invalidator instance."""
    global _cache_invalidator
    if _cache_invalidator is None:
        _cache_invalidator = CacheInvalidator(get_cache_manager())
    return _cache_invalidator


# For backward compatibility - these will be initialized on first access
cache_manager = None
cache_invalidator = None


# For backward compatibility - these will be initialized on first access
cache_manager = None
cache_invalidator = None


# Convenience functions
async def get_cached(key: str, backend: Optional[str] = None) -> Optional[Any]:
    """Get value from global cache manager."""
    return await get_cache_manager().get(key, backend)


async def set_cached(
    key: str,
    value: Any,
    ttl: Optional[int] = None,
    backend: Optional[str] = None
) -> bool:
    """Set value in global cache manager."""
    return await get_cache_manager().set(key, value, ttl, backend)


async def delete_cached(key: str, backend: Optional[str] = None) -> bool:
    """Delete key from global cache manager."""
    return await get_cache_manager().delete(key, backend)


async def clear_cache(backend: Optional[str] = None) -> bool:
    """Clear cache in global cache manager."""
    return await get_cache_manager().clear(backend)


# Cache configuration helpers
def setup_redis_cache(redis_url: str = "redis://localhost:6379/0") -> None:
    """Set up Redis cache backend."""
    redis_cache = RedisCache(redis_url)
    manager = get_cache_manager()
    manager.add_backend("redis", redis_cache)
    manager.set_default_backend("redis")
    logger.info("Redis cache configured as default backend")


def setup_memory_cache(max_size: int = 1000) -> None:
    """Set up memory cache backend."""
    memory_cache = MemoryCache(max_size=max_size)
    manager = get_cache_manager()
    manager.add_backend("memory", memory_cache)
    manager.set_default_backend("memory")
    logger.info("Memory cache configured as default backend")
