"""
Service de cache pour l'intégration avec l'application WakeDock.

Fournit une interface simplifiée pour l'utilisation du cache intelligent
dans les différents composants de l'application.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
try:
    import redis
    from redis import Redis
except ImportError:
    redis = None
    Redis = None

from .manager import CacheManager
from .monitoring import CacheMonitor
from wakedock.config import get_settings
from wakedock.performance.cache.intelligent import IntelligentCache

logger = logging.getLogger(__name__)


class CacheService:
    """Service principal de cache pour WakeDock"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.cache_manager: Optional[CacheManager] = None
        self.cache_monitor: Optional[CacheMonitor] = None
        self._initialized = False
        self._startup_task = None
    
    async def initialize(self):
        """Initialisation du service de cache"""
        if self._initialized:
            return
        
        try:
            settings = get_settings()
            
            # Configuration Redis avec support URL
            redis_url = getattr(settings, 'redis_url', None) or os.getenv('REDIS_URL')
            
            if redis_url:
                # Utiliser URL si disponible (format: redis://:password@host:port/db)
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    health_check_interval=30
                )
            else:
                # Configuration traditionnelle
                redis_config = {
                    'host': settings.redis.host,
                    'port': settings.redis.port,
                    'db': settings.redis.db,
                    'decode_responses': False,
                    'max_connections': 20,
                    'retry_on_timeout': True,
                    'socket_keepalive': True,
                    'socket_keepalive_options': {},
                    'health_check_interval': 30
                }
                
                # Ajouter password si configuré
                if hasattr(settings.redis, 'password') and settings.redis.password:
                    redis_config['password'] = settings.redis.password
                
                # Créer client Redis
                self.redis_client = redis.Redis(**redis_config)
            
            # Test connectivité
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
            # Initialiser cache manager
            self.cache_manager = CacheManager(self.redis_client)
            
            # Initialiser intelligent cache
            self.intelligent_cache = IntelligentCache(self.redis_client)
            
            # Initialiser monitoring
            self.cache_monitor = CacheMonitor(self.cache_manager)
            await self.cache_monitor.start_monitoring(collection_interval=60)
            
            # Préchauffage cache en arrière-plan
            self._startup_task = asyncio.create_task(self._startup_cache_warmup())
            
            self._initialized = True
            logger.info("Cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Cache service initialization failed: {e}")
            raise
    
    async def _startup_cache_warmup(self):
        """Préchauffage du cache au démarrage"""
        try:
            # Attendre un peu que l'app soit prête
            await asyncio.sleep(5)
            
            # Préchauffer cache avec patterns courants
            await self.cache_manager.warm_cache([
                "system_metrics",
                "dashboard_data"
            ])
            
            logger.info("Cache warmup completed")
            
        except Exception as e:
            logger.warning(f"Cache warmup failed: {e}")
    
    async def shutdown(self):
        """Arrêt propre du service"""
        if not self._initialized:
            return
        
        try:
            # Arrêter monitoring
            if self.cache_monitor:
                await self.cache_monitor.stop_monitoring()
            
            # Attendre tâches background
            if self.cache_manager:
                await self.cache_manager.cleanup_expired()
            
            # Annuler tâche de warmup si active
            if self._startup_task and not self._startup_task.done():
                self._startup_task.cancel()
                try:
                    await self._startup_task
                except asyncio.CancelledError:
                    pass
            
            # Fermer connexion Redis
            if self.redis_client:
                await self.redis_client.aclose()
            
            self._initialized = False
            logger.info("Cache service shutdown completed")
            
        except Exception as e:
            logger.error(f"Cache service shutdown error: {e}")
    
    # === Interface simplifiée pour l'application ===
    
    async def get(self, key: str, fetcher=None, cache_type: str = "default"):
        """Récupération simple depuis le cache"""
        if not self._initialized:
            if fetcher:
                return await fetcher()
            return None
        
        return await self.cache_manager.cache.get_with_strategy(
            key, fetcher, cache_type
        )
    
    async def set(self, key: str, value: Any, cache_type: str = "default"):
        """Écriture simple au cache"""
        if not self._initialized:
            return
        
        await self.cache_manager.cache.set_with_strategy(
            key, value, cache_type
        )
    
    async def invalidate(self, pattern: str = None, namespace: str = None):
        """Invalidation de cache"""
        if not self._initialized:
            return
        
        if namespace:
            await self.cache_manager.invalidate_namespace(namespace)
        elif pattern:
            await self.cache_manager.cache.invalidate(pattern=pattern)
    
    async def get_with_intelligent_cache(self, key: str, fetcher=None, cache_type: str = "default"):
        """Récupération avec cache intelligent"""
        if not self._initialized:
            if fetcher:
                return await fetcher()
            return None
        
        return await self.intelligent_cache.get_with_strategy(
            key, fetcher, cache_type
        )
    
    async def set_with_intelligent_cache(self, key: str, value: Any, cache_type: str = "default"):
        """Écriture avec cache intelligent"""
        if not self._initialized:
            return
        
        await self.intelligent_cache.set_with_strategy(
            key, value, cache_type
        )
    
    # === Méthodes spécialisées ===
    
    async def get_user_data(self, user_id: str):
        """Données utilisateur avec cache"""
        if not self._initialized:
            return None
        
        return await self.cache_manager.get_user_data(user_id)
    
    async def get_service_status(self, service_id: str):
        """Status service avec cache"""
        if not self._initialized:
            return None
        
        return await self.cache_manager.get_service_status(service_id)
    
    async def get_system_metrics(self, timeframe: str = "5m"):
        """Métriques système avec cache"""
        if not self._initialized:
            return None
        
        return await self.cache_manager.get_system_metrics(timeframe)
    
    async def get_dashboard_overview(self, user_id: str):
        """Vue d'ensemble dashboard"""
        if not self._initialized:
            return None
        
        return await self.cache_manager.get_dashboard_overview(user_id)
    
    async def get_service_logs(self, service_id: str, limit: int = 100, level: str = "all"):
        """Logs service avec compression"""
        if not self._initialized:
            return None
        
        return await self.cache_manager.get_service_logs(service_id, limit, level)
    
    # === Monitoring et statistiques ===
    
    async def get_stats(self) -> Dict[str, Any]:
        """Statistiques complètes du cache"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        global_stats = await self.cache_manager.get_global_stats()
        cache_breakdown = await self.cache_monitor.get_cache_type_breakdown()
        trend_analysis = await self.cache_monitor.get_trend_analysis()
        
        return {
            "status": "active",
            "global": global_stats,
            "breakdown": cache_breakdown,
            "trends": trend_analysis
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check du service de cache"""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "healthy": False
            }
        
        return await self.cache_manager.health_check()
    
    async def export_metrics(self, format: str = "prometheus") -> str:
        """Export des métriques"""
        if not self._initialized:
            return ""
        
        return await self.cache_monitor.export_metrics(format)
    
    # === Utilités ===
    
    def is_initialized(self) -> bool:
        """Vérifier si le service est initialisé"""
        return self._initialized
    
    def get_cache_key(self, namespace: str, identifier: str, **kwargs) -> str:
        """Génération de clé de cache standardisée"""
        if not self._initialized:
            return f"{namespace}:{identifier}"
        
        return self.cache_manager.cache.get_cache_key(namespace, identifier, **kwargs)


# Instance globale du service de cache
cache_service = CacheService()


# Décorateurs utilitaires
def cached(cache_type: str = "default", key_generator=None):
    """Décorateur pour mise en cache automatique"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not cache_service.is_initialized():
                return await func(*args, **kwargs)
            
            # Générer clé
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__qualname__}"
                cache_key = cache_service.get_cache_key("func", func_name, args=str(args), kwargs=str(kwargs))
            
            # Fetcher
            async def fetcher():
                return await func(*args, **kwargs)
            
            return await cache_service.get(cache_key, fetcher, cache_type)
        
        return wrapper
    return decorator


# Functions d'aide pour l'intégration
async def init_cache_service():
    """Initialiser le service de cache"""
    await cache_service.initialize()


async def shutdown_cache_service():
    """Arrêter le service de cache"""
    await cache_service.shutdown()


def get_cache_service() -> CacheService:
    """Obtenir l'instance du service de cache"""
    return cache_service