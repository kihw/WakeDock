"""
Cache Redis intelligent avec stratégies adaptatives.

Implémente différentes stratégies de cache pour optimiser les performances
selon le type de données et les patterns d'accès.
"""

import asyncio
import json
import gzip
import time
import logging
from typing import Any, Callable, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum

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
    max_size: Optional[int] = None
    refresh_threshold: float = 0.8  # Refresh à 80% du TTL
    compress: bool = False
    serializer: str = "json"  # json, pickle, msgpack


class IntelligentCache:
    """Cache Redis avec stratégies intelligentes"""
    
    CACHE_CONFIGS = {
        # Données quasi-statiques
        "user_permissions": CacheConfig(
            ttl=3600, strategy=CacheStrategy.REFRESH_AHEAD
        ),
        "system_config": CacheConfig(
            ttl=1800, strategy=CacheStrategy.WRITE_THROUGH
        ),
        
        # Données temps réel
        "system_metrics": CacheConfig(
            ttl=30, strategy=CacheStrategy.WRITE_BEHIND
        ),
        "service_status": CacheConfig(
            ttl=60, strategy=CacheStrategy.READ_THROUGH
        ),
        
        # Données calculées coûteuses
        "dashboard_overview": CacheConfig(
            ttl=300, strategy=CacheStrategy.REFRESH_AHEAD,
            refresh_threshold=0.7
        ),
        
        # Logs et historiques (compression)
        "service_logs": CacheConfig(
            ttl=900, strategy=CacheStrategy.READ_THROUGH,
            compress=True, max_size=1000
        ),
        
        # Métriques agrégées
        "metrics_aggregated": CacheConfig(
            ttl=600, strategy=CacheStrategy.REFRESH_AHEAD,
            compress=True, refresh_threshold=0.6
        ),
        
        # Sessions utilisateur
        "user_sessions": CacheConfig(
            ttl=7200, strategy=CacheStrategy.WRITE_THROUGH
        )
    }
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.background_tasks = set()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'refresh_ahead_count': 0,
            'compression_ratio': 0.0
        }
    
    async def get_with_strategy(
        self, 
        key: str, 
        fetcher: Optional[Callable] = None, 
        cache_type: str = "default"
    ) -> Any:
        """Récupération avec stratégie intelligente"""
        
        config = self.CACHE_CONFIGS.get(cache_type, 
            CacheConfig(ttl=300, strategy=CacheStrategy.READ_THROUGH))
        
        # Tenter récupération cache
        cached_data = await self._get_from_cache(key, config)
        
        if cached_data is not None:
            self._stats['hits'] += 1
            
            # Cache hit - vérifier si refresh nécessaire
            if config.strategy == CacheStrategy.REFRESH_AHEAD and fetcher:
                await self._check_refresh_ahead(key, config, fetcher)
            return cached_data
        
        # Cache miss
        self._stats['misses'] += 1
        
        if not fetcher:
            return None
        
        # Stratégie selon type
        if config.strategy == CacheStrategy.READ_THROUGH:
            return await self._read_through(key, config, fetcher)
        else:
            # Fallback standard
            data = await fetcher()
            await self._set_to_cache(key, data, config)
            return data
    
    async def set_with_strategy(
        self, 
        key: str, 
        data: Any, 
        cache_type: str = "default",
        db_updater: Optional[Callable] = None
    ):
        """Écriture avec stratégie"""
        
        config = self.CACHE_CONFIGS.get(cache_type)
        if not config:
            return
        
        if config.strategy == CacheStrategy.WRITE_THROUGH:
            # Cache + DB simultané
            await asyncio.gather(
                self._set_to_cache(key, data, config),
                db_updater() if db_updater else asyncio.sleep(0)
            )
        
        elif config.strategy == CacheStrategy.WRITE_BEHIND:
            # Cache immédiat, DB en arrière-plan
            await self._set_to_cache(key, data, config)
            if db_updater:
                task = asyncio.create_task(db_updater())
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)
        
        else:
            # Stratégies par défaut
            await self._set_to_cache(key, data, config)
    
    async def invalidate(self, pattern: str = None, cache_type: str = None):
        """Invalidation intelligente du cache"""
        
        if pattern:
            # Invalidation par pattern
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
        
        elif cache_type:
            # Invalidation par type
            prefix = f"{cache_type}:*"
            keys = await self.redis.keys(prefix)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys for cache type: {cache_type}")
    
    async def _check_refresh_ahead(
        self, 
        key: str, 
        config: CacheConfig, 
        fetcher: Callable
    ):
        """Vérification refresh proactif"""
        
        ttl_remaining = await self.redis.ttl(key)
        if ttl_remaining > 0:
            ttl_ratio = ttl_remaining / config.ttl
            
            # Si proche expiration, refresh en arrière-plan
            if ttl_ratio < config.refresh_threshold:
                task = asyncio.create_task(
                    self._background_refresh(key, config, fetcher)
                )
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)
                self._stats['refresh_ahead_count'] += 1
    
    async def _background_refresh(
        self, 
        key: str, 
        config: CacheConfig, 
        fetcher: Callable
    ):
        """Refresh en arrière-plan"""
        try:
            fresh_data = await fetcher()
            await self._set_to_cache(key, fresh_data, config)
            logger.debug(f"Background refresh completed for {key}")
        except Exception as e:
            logger.error(f"Background refresh failed for {key}: {e}")
    
    async def _read_through(
        self, 
        key: str, 
        config: CacheConfig, 
        fetcher: Callable
    ) -> Any:
        """Stratégie read-through avec protection contre cache stampede"""
        
        # Lock pour éviter cache stampede
        lock_key = f"lock:{key}"
        
        # Tenter acquisition lock
        acquired = await self.redis.set(lock_key, "1", nx=True, ex=30)
        
        if acquired:
            try:
                # Double-check cache pendant qu'on a le lock
                cached_data = await self._get_from_cache(key, config)
                if cached_data is not None:
                    return cached_data
                
                # Fetch et mise en cache
                data = await fetcher()
                await self._set_to_cache(key, data, config)
                return data
                
            finally:
                await self.redis.delete(lock_key)
        else:
            # Attendre que l'autre thread termine
            for _ in range(50):  # Max 5 secondes
                await asyncio.sleep(0.1)
                cached_data = await self._get_from_cache(key, config)
                if cached_data is not None:
                    return cached_data
            
            # Fallback si timeout
            return await fetcher()
    
    async def _get_from_cache(self, key: str, config: CacheConfig) -> Any:
        """Récupération optimisée du cache"""
        
        raw_data = await self.redis.get(key)
        if not raw_data:
            return None
        
        try:
            if config.compress:
                # Décompression
                raw_data = gzip.decompress(raw_data)
            
            if config.serializer == "json":
                return json.loads(raw_data)
            elif config.serializer == "pickle":
                import pickle
                return pickle.loads(raw_data)
            else:
                return json.loads(raw_data)
                
        except Exception as e:
            logger.warning(f"Failed to deserialize cached data for {key}: {e}")
            # Invalider cache corrompu
            await self.redis.delete(key)
            return None
    
    async def _set_to_cache(self, key: str, data: Any, config: CacheConfig):
        """Écriture optimisée au cache"""
        
        try:
            # Sérialisation
            if config.serializer == "json":
                serialized = json.dumps(data, default=str).encode()
            elif config.serializer == "pickle":
                import pickle
                serialized = pickle.dumps(data)
            else:
                serialized = json.dumps(data, default=str).encode()
            
            original_size = len(serialized)
            
            # Compression si configurée
            if config.compress:
                serialized = gzip.compress(serialized, compresslevel=6)
                compressed_size = len(serialized)
                self._stats['compression_ratio'] = (
                    (original_size - compressed_size) / original_size * 100
                )
            
            # Vérification taille max
            if config.max_size and len(serialized) > config.max_size * 1024:
                logger.warning(f"Data too large for cache key {key}: {len(serialized)} bytes")
                return
            
            # Écriture avec TTL
            await self.redis.setex(key, config.ttl, serialized)
            
        except Exception as e:
            logger.error(f"Failed to cache data for {key}: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Statistiques Redis
        redis_info = await self.redis.info('memory')
        
        return {
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'refresh_ahead_count': self._stats['refresh_ahead_count'],
            'compression_ratio': round(self._stats['compression_ratio'], 2),
            'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
            'redis_memory_peak': redis_info.get('used_memory_peak_human', 'N/A'),
            'background_tasks_count': len(self.background_tasks)
        }
    
    async def cleanup_background_tasks(self):
        """Nettoyage des tâches en arrière-plan"""
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            self.background_tasks.clear()
    
    def get_cache_key(self, namespace: str, identifier: str, **kwargs) -> str:
        """Génération de clés de cache standardisées"""
        base_key = f"{namespace}:{identifier}"
        
        if kwargs:
            # Ajouter paramètres pour cache plus granulaire
            params = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            base_key = f"{base_key}:{params}"
        
        return base_key


class CacheDecorator:
    """Décorateur pour mise en cache automatique"""
    
    def __init__(self, cache: IntelligentCache, cache_type: str = "default", key_generator: Optional[Callable] = None):
        self.cache = cache
        self.cache_type = cache_type
        self.key_generator = key_generator or self._default_key_generator
    
    def __call__(self, func: Callable):
        async def wrapper(*args, **kwargs):
            # Générer clé cache
            cache_key = self.key_generator(func, args, kwargs)
            
            # Créer fetcher pour la fonction
            async def fetcher():
                return await func(*args, **kwargs)
            
            # Utiliser cache intelligent
            return await self.cache.get_with_strategy(
                cache_key, 
                fetcher, 
                self.cache_type
            )
        
        return wrapper
    
    def _default_key_generator(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Générateur de clé par défaut"""
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        # Créer signature des arguments
        arg_parts = []
        if args:
            arg_parts.extend(str(arg) for arg in args)
        if kwargs:
            arg_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        signature = ":".join(arg_parts) if arg_parts else "no_args"
        return f"func:{func_name}:{signature}"


# Factory pour création cache avec configuration
def create_intelligent_cache(redis_client, custom_configs: Optional[Dict] = None) -> IntelligentCache:
    """Factory pour création cache intelligent"""
    
    cache = IntelligentCache(redis_client)
    
    # Merger configurations custom
    if custom_configs:
        cache.CACHE_CONFIGS.update(custom_configs)
    
    return cache