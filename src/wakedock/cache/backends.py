"""
Cache backend implementations for WakeDock.
Supports memory-based and Redis-based caching.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
# Removed unused import: import weakref
# Removed pickle import for security - using JSON-only serialization

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get cache size (number of keys)."""
        pass


class CacheEntry:
    """Cache entry with expiration support."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl else None
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def ttl_remaining(self) -> Optional[int]:
        """Get remaining TTL in seconds."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0, int(remaining))


class MemoryCache(CacheBackend):
    """In-memory cache backend with TTL support."""
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 60):
        self._cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._lock = None  # Initialize lazily
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
        self._initialized = False
    
    async def initialize(self):
        """Initialize async components."""
        if not self._initialized:
            self._lock = asyncio.Lock()
            self._start_cleanup_task()
            self._initialized = True
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        except RuntimeError:
            # No event loop running, skip task creation
            pass
    
    async def _cleanup_loop(self):
        """Background loop to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired entries."""
        if not self._initialized:
            return
        async with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        if len(self._cache) >= self.max_size:
            # Evict 10% of entries (oldest first)
            evict_count = max(1, self.max_size // 10)
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].created_at
            )
            
            for key, _ in sorted_entries[:evict_count]:
                del self._cache[key]
                self._stats["evictions"] += 1
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            await self._evict_if_needed()
            self._cache[key] = CacheEntry(value, ttl)
            self._stats["sets"] += 1
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return True
            elif entry and entry.is_expired():
                del self._cache[key]
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            self._cache.clear()
            return True
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        import fnmatch
        
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            await self._cleanup_expired()
            all_keys = list(self._cache.keys())
            
            if pattern == "*":
                return all_keys
            
            return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
    
    async def size(self) -> int:
        """Get cache size."""
        if not self._initialized:
            await self.initialize()
        async with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "max_size": self.max_size
        }
    
    async def cleanup(self):
        """Cleanup cache resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.clear()


class RedisCache(CacheBackend):
    """Redis-based cache backend."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "wakedock:"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def _get_redis(self):
        """Get Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
                logger.info("Connected to Redis cache")
            except ImportError:
                logger.error("redis package not installed. Install with: pip install redis")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    def _strip_prefix(self, key: str) -> str:
        """Remove prefix from key."""
        if key.startswith(self.prefix):
            return key[len(self.prefix):]
        return key
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            redis = await self._get_redis()
            value = await redis.get(self._make_key(key))
            
            if value is None:
                self._stats["misses"] += 1
                return None
            
            # Deserialize as JSON only (secure deserialization)
            try:
                result = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Fallback to plain string value if not valid JSON
                logger.warning(f"Cache value is not valid JSON, returning as string: {key}")
                result = value
            
            self._stats["hits"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            self._stats["errors"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        try:
            redis = await self._get_redis()
            
            # Serialize as JSON only (secure serialization)
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to serialize cache value as JSON: {e}, converting to string")
                serialized = json.dumps(str(value))
            
            await redis.set(self._make_key(key), serialized, ex=ttl)
            self._stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
            self._stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            redis = await self._get_redis()
            result = await redis.delete(self._make_key(key))
            
            if result > 0:
                self._stats["deletes"] += 1
                return True
            return False
            
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            self._stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            redis = await self._get_redis()
            result = await redis.exists(self._make_key(key))
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis cache exists error: {e}")
            self._stats["errors"] += 1
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries with prefix."""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(f"{self.prefix}*")
            
            if keys:
                await redis.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")
            self._stats["errors"] += 1
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        try:
            redis = await self._get_redis()
            redis_pattern = f"{self.prefix}{pattern}"
            keys = await redis.keys(redis_pattern)
            
            # Strip prefix from keys
            return [self._strip_prefix(key) for key in keys]
            
        except Exception as e:
            logger.error(f"Redis cache keys error: {e}")
            self._stats["errors"] += 1
            return []
    
    async def size(self) -> int:
        """Get cache size."""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(f"{self.prefix}*")
            return len(keys)
            
        except Exception as e:
            logger.error(f"Redis cache size error: {e}")
            self._stats["errors"] += 1
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "backend": "redis",
            "redis_url": self.redis_url
        }
    
    async def cleanup(self):
        """Cleanup Redis resources."""
        if self._redis:
            await self._redis.close()
            self._redis = None
