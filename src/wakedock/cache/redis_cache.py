"""
Redis Cache Implementation for WakeDock
High-performance caching layer with smart invalidation
"""

import json
import pickle
import hashlib
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis

logger = logging.getLogger(__name__)
from redis.asyncio import Redis

class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TTL_ONLY = "ttl_only"           # Simple TTL expiration
    WRITE_THROUGH = "write_through"  # Update cache on write
    WRITE_BEHIND = "write_behind"    # Async cache update
    READ_THROUGH = "read_through"    # Cache on read miss

@dataclass
class CacheConfig:
    """Cache configuration"""
    default_ttl: int = 300          # 5 minutes
    max_connections: int = 50
    retry_on_timeout: bool = True
    retry_attempts: int = 3
    retry_delay: float = 0.1
    compression_threshold: int = 1024  # Compress values > 1KB
    key_prefix: str = "wakedock"

class CacheKey:
    """Smart cache key generation"""
    
    @staticmethod
    def service_list(user_id: Optional[int] = None, status: Optional[str] = None) -> str:
        parts = ["services"]
        if user_id:
            parts.append(f"user:{user_id}")
        if status:
            parts.append(f"status:{status}")
        return ":".join(parts)
    
    @staticmethod
    def service_detail(service_id: str) -> str:
        return f"service:{service_id}"
    
    @staticmethod
    def service_metrics(service_id: str, timeframe: str = "1h") -> str:
        return f"metrics:{service_id}:{timeframe}"
    
    @staticmethod
    def service_logs(service_id: str, level: Optional[str] = None, limit: int = 100) -> str:
        parts = ["logs", service_id, str(limit)]
        if level:
            parts.append(f"level:{level}")
        return ":".join(parts)
    
    @staticmethod
    def dashboard_summary(user_id: Optional[int] = None) -> str:
        if user_id:
            return f"dashboard:summary:user:{user_id}"
        return "dashboard:summary:global"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"user:profile:{user_id}"
    
    @staticmethod
    def system_stats() -> str:
        return "system:stats"
    
    @staticmethod
    def alerts_summary(user_id: Optional[int] = None) -> str:
        if user_id:
            return f"alerts:summary:user:{user_id}"
        return "alerts:summary:global"

class RedisCache:
    """High-performance Redis cache with smart features"""
    
    def __init__(self, redis_url: str, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis: Optional[Redis] = None
        self.redis_url = redis_url
        self._connection_pool = None
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'bytes_saved': 0
        }
    
    async def connect(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Handle binary data
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            logger.info(f"Redis cache connected: {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value with optional compression"""
        # Try JSON first for simple types
        try:
            json_str = json.dumps(value, default=str)
            json_bytes = json_str.encode('utf-8')
            
            # Use compression for large values
            if len(json_bytes) > self.config.compression_threshold:
                import gzip
                compressed = gzip.compress(json_bytes)
                # Only use compression if it saves space
                if len(compressed) < len(json_bytes):
                    self.stats['bytes_saved'] += len(json_bytes) - len(compressed)
                    return b'gzip:' + compressed
            
            return b'json:' + json_bytes
            
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            pickled = pickle.dumps(value)
            return b'pickle:' + pickled
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value with decompression"""
        if data.startswith(b'json:'):
            return json.loads(data[5:].decode('utf-8'))
        elif data.startswith(b'gzip:'):
            import gzip
            decompressed = gzip.decompress(data[5:])
            return json.loads(decompressed.decode('utf-8'))
        elif data.startswith(b'pickle:'):
            return pickle.loads(data[7:])
        else:
            # Legacy format
            return json.loads(data.decode('utf-8'))
    
    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix"""
        return f"{self.config.key_prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        
        try:
            full_key = self._make_key(key)
            data = await self.redis.get(full_key)
            
            if data is None:
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            return self._deserialize_value(data)
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.redis:
            return False
        
        try:
            full_key = self._make_key(key)
            serialized = self._serialize_value(value)
            ttl = ttl or self.config.default_ttl
            
            await self.redis.setex(full_key, ttl, serialized)
            self.stats['sets'] += 1
            return True
            
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis:
            return False
        
        try:
            full_key = self._make_key(key)
            result = await self.redis.delete(full_key)
            self.stats['deletes'] += 1
            return bool(result)
            
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            self.stats['errors'] += 1
            return False
    
    async def get_or_set(
        self, 
        key: str, 
        factory: Callable[[], Any], 
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or execute factory and cache result"""
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Execute factory function
        try:
            if asyncio.iscoroutinefunction(factory):
                result = await factory()
            else:
                result = factory()
            
            # Cache the result
            await self.set(key, result, ttl)
            return result
            
        except Exception as e:
            print(f"Factory function error for key {key}: {e}")
            raise
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = await self.redis.keys(full_pattern)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                self.stats['deletes'] += len(keys)
                return deleted
            
            return 0
            
        except Exception as e:
            print(f"Cache invalidate pattern error for {pattern}: {e}")
            self.stats['errors'] += 1
            return 0
    
    async def invalidate_service(self, service_id: str) -> int:
        """Invalidate all cache entries for a service"""
        patterns = [
            f"service:{service_id}*",
            f"metrics:{service_id}*", 
            f"logs:{service_id}*",
            "services*",  # Invalidate service lists
            "dashboard:summary*"  # Invalidate dashboard
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.invalidate_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    
    async def invalidate_user(self, user_id: int) -> int:
        """Invalidate all cache entries for a user"""
        patterns = [
            f"*user:{user_id}*",
            f"user:profile:{user_id}",
            "dashboard:summary*"  # User-specific dashboards
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.invalidate_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    
    async def warm_cache(self, keys_and_factories: Dict[str, Callable]) -> Dict[str, bool]:
        """Warm cache with multiple key-value pairs"""
        results = {}
        
        for key, factory in keys_and_factories.items():
            try:
                # Check if already cached
                if await self.get(key) is None:
                    # Execute factory and cache
                    if asyncio.iscoroutinefunction(factory):
                        value = await factory()
                    else:
                        value = factory()
                    
                    results[key] = await self.set(key, value)
                else:
                    results[key] = True  # Already cached
                    
            except Exception as e:
                print(f"Cache warm error for key {key}: {e}")
                results[key] = False
        
        return results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_operations = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_operations * 100) if total_operations > 0 else 0
        
        redis_info = {}
        if self.redis:
            try:
                info = await self.redis.info()
                redis_info = {
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except Exception:
                pass
        
        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'total_operations': total_operations,
            'redis_info': redis_info
        }
    
    async def reset_stats(self) -> None:
        """Reset cache statistics"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'bytes_saved': 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        if not self.redis:
            return {'status': 'disconnected', 'error': 'No Redis connection'}
        
        try:
            start_time = datetime.now()
            await self.redis.ping()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'connection': 'active'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection': 'failed'
            }

# Global cache instance
cache = RedisCache("redis://localhost:6379/0")

# Convenience functions
async def get_cache() -> RedisCache:
    """Get the global cache instance"""
    if not cache.redis:
        await cache.connect()
    return cache

async def cached(
    key: str,
    factory: Callable,
    ttl: Optional[int] = None
) -> Any:
    """Decorator-style caching function"""
    cache_instance = await get_cache()
    return await cache_instance.get_or_set(key, factory, ttl)
