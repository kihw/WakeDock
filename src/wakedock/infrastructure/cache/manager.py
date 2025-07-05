"""
Gestionnaire de cache centralisé pour WakeDock.

Coordonne les différentes instances de cache et fournit une interface
unifiée pour les opérations de cache dans l'application.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .intelligent import IntelligentCache, CacheStrategy, CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class CacheOperation:
    """Opération de cache en batch"""
    operation: str  # get, set, delete
    key: str
    value: Any = None
    cache_type: str = "default"
    fetcher: Optional[Callable] = None


class CacheManager:
    """Gestionnaire centralisé des caches"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache = IntelligentCache(redis_client)
        
        # Métriques globales
        self._global_stats = {
            'total_operations': 0,
            'batch_operations': 0,
            'cache_warmup_count': 0,
            'last_cleanup': None
        }
        
        # Configuration des namespaces de cache
        self.namespaces = {
            'users': 'user_permissions',
            'services': 'service_status', 
            'metrics': 'system_metrics',
            'logs': 'service_logs',
            'dashboard': 'dashboard_overview',
            'system': 'system_config'
        }
    
    # === Interface simplifiée pour l'application ===
    
    async def get_user_data(self, user_id: str) -> Optional[Dict]:
        """Récupération données utilisateur avec cache"""
        key = self.cache.get_cache_key("users", user_id)
        
        async def fetch_user():
            # Simulation fetch depuis DB
            return {"id": user_id, "permissions": ["read", "write"]}
        
        return await self.cache.get_with_strategy(
            key, fetch_user, "user_permissions"
        )
    
    async def get_service_status(self, service_id: str) -> Optional[Dict]:
        """Status service avec cache temps réel"""
        key = self.cache.get_cache_key("services", service_id, status=True)
        
        async def fetch_status():
            # Simulation Docker API call
            return {
                "id": service_id,
                "status": "running",
                "cpu": 45.2,
                "memory": 128.5,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await self.cache.get_with_strategy(
            key, fetch_status, "service_status"
        )
    
    async def get_system_metrics(self, timeframe: str = "5m") -> Optional[Dict]:
        """Métriques système avec cache court"""
        key = self.cache.get_cache_key("metrics", "system", timeframe=timeframe)
        
        async def fetch_metrics():
            return {
                "cpu_usage": 25.4,
                "memory_usage": 67.8,
                "disk_usage": 45.2,
                "network_io": {"in": 1024, "out": 2048},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await self.cache.get_with_strategy(
            key, fetch_metrics, "system_metrics"
        )
    
    async def get_dashboard_overview(self, user_id: str) -> Optional[Dict]:
        """Vue d'ensemble dashboard avec cache refresh-ahead"""
        key = self.cache.get_cache_key("dashboard", user_id)
        
        async def fetch_overview():
            # Agrégation de données coûteuse
            services = await self.get_services_summary()
            metrics = await self.get_system_metrics()
            
            return {
                "services": services,
                "system": metrics,
                "alerts": [],
                "recent_events": [],
                "generated_at": datetime.utcnow().isoformat()
            }
        
        return await self.cache.get_with_strategy(
            key, fetch_overview, "dashboard_overview"
        )
    
    async def get_service_logs(
        self, 
        service_id: str, 
        limit: int = 100, 
        level: str = "all"
    ) -> Optional[List[Dict]]:
        """Logs service avec compression"""
        key = self.cache.get_cache_key(
            "logs", service_id, limit=limit, level=level
        )
        
        async def fetch_logs():
            # Simulation fetch logs depuis DB/Docker
            return [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "info",
                    "message": f"Service {service_id} log entry {i}",
                    "source": "container"
                }
                for i in range(limit)
            ]
        
        return await self.cache.get_with_strategy(
            key, fetch_logs, "service_logs"
        )
    
    # === Opérations batch ===
    
    async def batch_get(self, operations: List[CacheOperation]) -> Dict[str, Any]:
        """Récupération en batch pour performance"""
        self._global_stats['batch_operations'] += 1
        
        results = {}
        
        # Grouper par type de cache pour optimisation
        by_cache_type = {}
        for op in operations:
            if op.operation == "get":
                cache_type = op.cache_type
                if cache_type not in by_cache_type:
                    by_cache_type[cache_type] = []
                by_cache_type[cache_type].append(op)
        
        # Exécuter en parallèle par type
        tasks = []
        for cache_type, ops in by_cache_type.items():
            task = self._batch_get_by_type(ops, cache_type)
            tasks.append(task)
        
        batch_results = await asyncio.gather(*tasks)
        
        # Merger résultats
        for result_dict in batch_results:
            results.update(result_dict)
        
        return results
    
    async def _batch_get_by_type(
        self, 
        operations: List[CacheOperation], 
        cache_type: str
    ) -> Dict[str, Any]:
        """Batch get optimisé par type de cache"""
        
        # Récupération pipeline Redis pour performance
        pipe = self.redis.pipeline()
        keys = [op.key for op in operations]
        
        # Pipeline pour vérifier existence
        for key in keys:
            pipe.exists(key)
        
        exists_results = await pipe.execute()
        pipe = self.redis.pipeline()
        
        # Pipeline pour récupération
        for key in keys:
            pipe.get(key)
        
        cached_results = await pipe.execute()
        
        results = {}
        fetch_tasks = []
        
        # Traiter résultats
        for i, op in enumerate(operations):
            if exists_results[i] and cached_results[i]:
                # Cache hit
                try:
                    config = self.cache.CACHE_CONFIGS.get(cache_type)
                    if config:
                        data = await self.cache._get_from_cache(op.key, config)
                        results[op.key] = data
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached data for {op.key}: {e}")
                    # Fallback to fetcher si disponible
                    if op.fetcher:
                        fetch_tasks.append((op.key, op.fetcher, cache_type))
            else:
                # Cache miss - programmer fetch
                if op.fetcher:
                    fetch_tasks.append((op.key, op.fetcher, cache_type))
        
        # Exécuter fetchers en parallèle avec limite concurrence
        if fetch_tasks:
            semaphore = asyncio.Semaphore(10)  # Max 10 fetches simultanés
            
            async def bounded_fetch(key: str, fetcher: Callable, cache_type: str):
                async with semaphore:
                    try:
                        data = await fetcher()
                        # Mise en cache async
                        await self.cache.set_with_strategy(key, data, cache_type)
                        return key, data
                    except Exception as e:
                        logger.error(f"Fetch failed for {key}: {e}")
                        return key, None
            
            fetch_results = await asyncio.gather(
                *[bounded_fetch(key, fetcher, ct) for key, fetcher, ct in fetch_tasks],
                return_exceptions=True
            )
            
            # Merger fetch results
            for result in fetch_results:
                if isinstance(result, tuple):
                    key, data = result
                    results[key] = data
        
        return results
    
    # === Cache warming ===
    
    async def warm_cache(self, patterns: List[str]):
        """Préchauffage du cache pour patterns courants"""
        self._global_stats['cache_warmup_count'] += 1
        
        warming_tasks = []
        
        for pattern in patterns:
            if pattern == "dashboard_data":
                # Préchauffer données dashboard critiques
                task = self._warm_dashboard_data()
                warming_tasks.append(task)
            
            elif pattern == "system_metrics":
                # Préchauffer métriques système
                task = self._warm_system_metrics()
                warming_tasks.append(task)
            
            elif pattern == "user_permissions":
                # Préchauffer permissions utilisateurs actifs
                task = self._warm_user_permissions()
                warming_tasks.append(task)
        
        if warming_tasks:
            await asyncio.gather(*warming_tasks, return_exceptions=True)
            logger.info(f"Cache warming completed for {len(patterns)} patterns")
    
    async def _warm_dashboard_data(self):
        """Préchauffage données dashboard"""
        # Identifier utilisateurs actifs récents
        active_users = ["admin", "user1", "user2"]  # À récupérer depuis DB
        
        tasks = [
            self.get_dashboard_overview(user_id) 
            for user_id in active_users
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _warm_system_metrics(self):
        """Préchauffage métriques système"""
        timeframes = ["5m", "1h", "24h"]
        
        tasks = [
            self.get_system_metrics(tf) 
            for tf in timeframes
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _warm_user_permissions(self):
        """Préchauffage permissions utilisateurs"""
        # À implémenter selon logique métier
        pass
    
    # === Gestion et maintenance ===
    
    async def invalidate_namespace(self, namespace: str):
        """Invalidation par namespace"""
        cache_type = self.namespaces.get(namespace)
        if cache_type:
            await self.cache.invalidate(cache_type=cache_type)
            logger.info(f"Invalidated cache namespace: {namespace}")
    
    async def cleanup_expired(self):
        """Nettoyage cache expiré et tâches background"""
        self._global_stats['last_cleanup'] = datetime.utcnow()
        
        # Nettoyage tâches background
        await self.cache.cleanup_background_tasks()
        
        # Stats Redis pour monitoring
        redis_info = await self.redis.info('memory')
        used_memory = redis_info.get('used_memory', 0)
        
        if used_memory > 200 * 1024 * 1024:  # Si > 200MB
            logger.info("Redis memory usage high, consider cleanup")
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Statistiques globales du cache"""
        cache_stats = await self.cache.get_stats()
        
        return {
            **cache_stats,
            **self._global_stats,
            'namespaces_count': len(self.namespaces),
            'configs_count': len(self.cache.CACHE_CONFIGS)
        }
    
    # === Helpers ===
    
    async def get_services_summary(self) -> Dict:
        """Résumé services pour dashboard"""
        # Simulation - à remplacer par vraie logique
        return {
            "total": 5,
            "running": 3,
            "stopped": 1,
            "error": 1
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check du cache"""
        try:
            # Test Redis connectivité
            await self.redis.ping()
            
            # Test opération cache
            test_key = "health_check_test"
            await self.redis.setex(test_key, 10, "test")
            result = await self.redis.get(test_key)
            await self.redis.delete(test_key)
            
            if result != b"test":
                raise Exception("Cache read/write test failed")
            
            stats = await self.get_global_stats()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "cache_operational": True,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False,
                "cache_operational": False
            }