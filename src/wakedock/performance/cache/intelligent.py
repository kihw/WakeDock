"""
Système de cache intelligent avec différentes stratégies
Optimise les performances des requêtes fréquentes
"""

import asyncio
import json
import pickle
from typing import Any, Callable, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum
import time
import logging
from datetime import datetime, timedelta
import hashlib

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Stratégies de cache disponibles"""
    WRITE_THROUGH = "write_through"      # Cache + DB simultané
    WRITE_BEHIND = "write_behind"        # Cache immédiat, DB async
    REFRESH_AHEAD = "refresh_ahead"      # Refresh proactif
    READ_THROUGH = "read_through"        # Cache miss = DB fetch


@dataclass
class CacheConfig:
    """Configuration cache par type de données"""
    ttl: int
    strategy: CacheStrategy
    refresh_threshold: float = 0.8  # Refresh quand TTL < 80%
    max_size: int = 1000
    serialize_json: bool = True


class IntelligentCache:
    """Cache intelligent avec stratégies avancées"""
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis = redis_client
        self.local_cache: Dict[str, Dict] = {}
        self.cache_configs: Dict[str, CacheConfig] = {}
        self.hit_stats = {"hits": 0, "misses": 0, "refreshes": 0}
        self.is_redis_available = redis_client is not None and REDIS_AVAILABLE
    
    async def configure_cache_type(self, cache_type: str, config: CacheConfig):
        """Configure un type de cache spécifique"""
        self.cache_configs[cache_type] = config
        logger.info(f"Configured cache type '{cache_type}' with strategy {config.strategy.value}")
    
    def _generate_key(self, cache_type: str, key: str) -> str:
        """Génère une clé de cache unique"""
        return f"wakedock:{cache_type}:{key}"
    
    def _serialize_value(self, value: Any, use_json: bool = True) -> bytes:
        """Sérialise une valeur pour le cache"""
        if use_json:
            try:
                return json.dumps(value, default=str).encode('utf-8')
            except (TypeError, ValueError):
                # Fallback to pickle pour objets complexes
                return pickle.dumps(value)
        return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes, use_json: bool = True) -> Any:
        """Désérialise une valeur du cache"""
        if use_json:
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fallback to pickle
                return pickle.loads(data)
        return pickle.loads(data)
    
    async def get(self, cache_type: str, key: str, default: Any = None) -> Any:
        """Récupère une valeur du cache"""
        full_key = self._generate_key(cache_type, key)
        config = self.cache_configs.get(cache_type)
        
        if not config:
            logger.warning(f"No cache config for type '{cache_type}'")
            return default
        
        # Essai Redis d'abord
        if self.redis:
            try:
                cached_data = await self.redis.get(full_key)
                if cached_data:
                    self.hit_stats["hits"] += 1
                    return self._deserialize_value(cached_data, config.serialize_json)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback cache local
        if full_key in self.local_cache:
            cache_entry = self.local_cache[full_key]
            if cache_entry["expires"] > time.time():
                self.hit_stats["hits"] += 1
                return cache_entry["value"]
            else:
                # Expired, remove
                del self.local_cache[full_key]
        
        self.hit_stats["misses"] += 1
        return default
    
    async def set(self, cache_type: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur dans le cache"""
        full_key = self._generate_key(cache_type, key)
        config = self.cache_configs.get(cache_type)
        
        if not config:
            logger.warning(f"No cache config for type '{cache_type}'")
            return False
        
        cache_ttl = ttl or config.ttl
        serialized_value = self._serialize_value(value, config.serialize_json)
        
        # Stockage Redis
        if self.redis:
            try:
                await self.redis.setex(full_key, cache_ttl, serialized_value)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Stockage local (backup/fallback)
        self.local_cache[full_key] = {
            "value": value,
            "expires": time.time() + cache_ttl,
            "created": time.time()
        }
        
        # Nettoyage du cache local si trop grand
        if len(self.local_cache) > config.max_size:
            await self._cleanup_local_cache()
        
        return True
    
    async def delete(self, cache_type: str, key: str) -> bool:
        """Supprime une valeur du cache"""
        full_key = self._generate_key(cache_type, key)
        
        # Suppression Redis
        if self.redis:
            try:
                await self.redis.delete(full_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Suppression locale
        if full_key in self.local_cache:
            del self.local_cache[full_key]
        
        return True
    
    async def cached_call(self, cache_type: str, key: str, func: Callable, *args, **kwargs) -> Any:
        """Exécute une fonction avec mise en cache automatique"""
        cached_value = await self.get(cache_type, key)
        
        if cached_value is not None:
            config = self.cache_configs.get(cache_type)
            
            # Vérification pour refresh ahead
            if config and config.strategy == CacheStrategy.REFRESH_AHEAD:
                await self._check_refresh_ahead(cache_type, key, func, *args, **kwargs)
            
            return cached_value
        
        # Cache miss - exécution de la fonction
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        
        # Mise en cache du résultat
        await self.set(cache_type, key, result)
        return result
    
    async def _check_refresh_ahead(self, cache_type: str, key: str, func: Callable, *args, **kwargs):
        """Vérifie si un refresh proactif est nécessaire"""
        full_key = self._generate_key(cache_type, key)
        config = self.cache_configs[cache_type]
        
        # Vérification TTL pour refresh proactif
        if self.redis:
            try:
                ttl_remaining = await self.redis.ttl(full_key)
                if ttl_remaining > 0 and ttl_remaining < (config.ttl * config.refresh_threshold):
                    # Refresh en arrière-plan
                    asyncio.create_task(self._background_refresh(cache_type, key, func, *args, **kwargs))
                    self.hit_stats["refreshes"] += 1
            except Exception as e:
                logger.error(f"TTL check error: {e}")
    
    async def _background_refresh(self, cache_type: str, key: str, func: Callable, *args, **kwargs):
        """Refresh en arrière-plan"""
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self.set(cache_type, key, result)
            logger.debug(f"Background refresh completed for {cache_type}:{key}")
            
        except Exception as e:
            logger.error(f"Background refresh failed for {cache_type}:{key}: {e}")
    
    async def _cleanup_local_cache(self):
        """Nettoie le cache local en supprimant les entrées expirées"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.local_cache.items()
            if entry["expires"] < current_time
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        total_requests = self.hit_stats["hits"] + self.hit_stats["misses"]
        hit_rate = (self.hit_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_rate": round(hit_rate, 2),
            "hits": self.hit_stats["hits"],
            "misses": self.hit_stats["misses"],
            "refreshes": self.hit_stats["refreshes"],
            "local_cache_size": len(self.local_cache),
            "configured_types": list(self.cache_configs.keys())
        }
    
    async def invalidate_pattern(self, pattern: str):
        """Invalide les clés correspondant à un pattern"""
        if self.redis:
            try:
                keys = await self.redis.keys(f"wakedock:{pattern}")
                if keys:
                    await self.redis.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} keys matching pattern '{pattern}'")
            except Exception as e:
                logger.error(f"Pattern invalidation error: {e}")
        
        # Nettoyage cache local
        matching_keys = [key for key in self.local_cache.keys() if pattern in key]
        for key in matching_keys:
            del self.local_cache[key]


class CacheManager:
    """Gestionnaire principal du cache avec configurations prédéfinies"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.cache = None
        self.redis_url = redis_url
        
    async def initialize(self):
        """Initialise le cache avec les configurations par défaut"""
        redis_client = None
        
        if self.redis_url and redis:
            try:
                redis_client = redis.from_url(self.redis_url)
                await redis_client.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, using local cache only: {e}")
                redis_client = None
        
        self.cache = IntelligentCache(redis_client)
        
        # Configurations par défaut
        await self._setup_default_configs()
        
    async def _setup_default_configs(self):
        """Configure les types de cache par défaut"""
        configs = {
            "services": CacheConfig(
                ttl=300,  # 5 minutes
                strategy=CacheStrategy.READ_THROUGH,
                refresh_threshold=0.8
            ),
            "metrics": CacheConfig(
                ttl=60,   # 1 minute
                strategy=CacheStrategy.REFRESH_AHEAD,
                refresh_threshold=0.7
            ),
            "dashboard": CacheConfig(
                ttl=30,   # 30 secondes
                strategy=CacheStrategy.READ_THROUGH,
                refresh_threshold=0.8
            ),
            "user_sessions": CacheConfig(
                ttl=1800,  # 30 minutes
                strategy=CacheStrategy.WRITE_THROUGH,
                serialize_json=True
            ),
            "system_config": CacheConfig(
                ttl=3600,  # 1 heure
                strategy=CacheStrategy.WRITE_THROUGH,
                serialize_json=True
            )
        }
        
        for cache_type, config in configs.items():
            await self.cache.configure_cache_type(cache_type, config)
    
    def get_cache(self) -> IntelligentCache:
        """Retourne l'instance de cache"""
        if not self.cache:
            raise RuntimeError("Cache not initialized. Call initialize() first.")
        return self.cache


# Instance globale
cache_manager = CacheManager()

async def get_cache() -> IntelligentCache:
    """Récupère l'instance de cache globale"""
    return cache_manager.get_cache()


# Décorateurs utilitaires
def cached(cache_type: str, key_func: Optional[Callable] = None, ttl: Optional[int] = None):
    """Décorateur pour mise en cache automatique"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = await get_cache()
            
            # Génération de la clé
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Clé basée sur les arguments
                key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            return await cache.cached_call(cache_type, cache_key, func, *args, **kwargs)
        
        return wrapper
    return decorator


# Fonction d'initialisation
async def init_cache(redis_url: Optional[str] = None):
    """Initialise le système de cache"""
    cache_manager.redis_url = redis_url
    await cache_manager.initialize()
    logger.info("Cache system initialized successfully")
