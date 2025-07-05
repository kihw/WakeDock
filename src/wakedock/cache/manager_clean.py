# This is a temp file - will replace the broken manager.py

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