"""
API endpoints pour le monitoring et gestion du cache.

Fournit des endpoints pour visualiser les performances du cache,
les statistiques et les métriques d'optimisation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional, List
import logging

from wakedock.infrastructure.cache.service import CacheService
from wakedock.api.dependencies import get_cache_service_dep
from wakedock.api.auth.dependencies import get_current_user
from wakedock.database.models import UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Cache Health Check")
async def cache_health(cache_service: CacheService = Depends(get_cache_service_dep)):
    """
    Vérification de l'état de santé du cache.
    """
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503, 
            detail="Cache service not initialized"
        )
    
    health = await cache_service.health_check()
    
    if not health.get("healthy", False):
        raise HTTPException(
            status_code=503,
            detail=f"Cache unhealthy: {health.get('error', 'Unknown error')}"
        )
    
    return health


@router.get("/stats", summary="Cache Statistics")
async def cache_stats(
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Statistiques complètes du cache.
    
    Retourne:
    - Métriques globales (hit rate, response time, etc.)
    - Breakdown par type de cache
    - Analyse des tendances
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        stats = await cache_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error retrieving cache stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache statistics"
        )


@router.get("/metrics", summary="Cache Metrics Export")
async def cache_metrics(
    format: str = Query("prometheus", pattern="^(prometheus|json)$"),
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
):
    """
    Export des métriques du cache en format Prometheus ou JSON.
    
    Args:
        format: Format d'export (prometheus ou json)
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        metrics = await cache_service.export_metrics(format)
        
        if format == "prometheus":
            return PlainTextResponse(
                content=metrics,
                media_type="text/plain; version=0.0.4"
            )
        else:
            return {"metrics": metrics}
            
    except Exception as e:
        logger.error(f"Error exporting cache metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to export cache metrics"
        )


@router.post("/invalidate", summary="Invalidate Cache")
async def invalidate_cache(
    pattern: Optional[str] = None,
    namespace: Optional[str] = None,
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
):
    """
    Invalidation du cache par pattern ou namespace.
    
    Args:
        pattern: Pattern de clés à invalider (ex: "user:*")
        namespace: Namespace à invalider (ex: "users", "services")
    
    Note: Nécessite les droits administrateur.
    """
    # Vérification droits admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for cache invalidation"
        )
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    if not pattern and not namespace:
        raise HTTPException(
            status_code=400,
            detail="Either pattern or namespace must be specified"
        )
    
    try:
        await cache_service.invalidate(pattern=pattern, namespace=namespace)
        
        return {
            "success": True,
            "message": f"Cache invalidated for {'pattern: ' + pattern if pattern else 'namespace: ' + namespace}",
            "invalidated_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache"
        )


@router.get("/performance", summary="Cache Performance Analysis")
async def cache_performance(
    hours: int = Query(24, ge=1, le=168),  # 1 heure à 1 semaine
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyse de performance du cache sur une période donnée.
    
    Args:
        hours: Nombre d'heures d'historique à analyser (1-168)
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Récupérer stats actuelles
        current_stats = await cache_service.get_stats()
        
        # Analyse de tendance si monitoring disponible
        trend_analysis = current_stats.get("trends", {})
        
        return {
            "period_hours": hours,
            "current_performance": {
                "hit_rate": current_stats["global"].get("hit_rate", 0),
                "total_requests": current_stats["global"].get("total_requests", 0),
                "cache_size_mb": current_stats["global"].get("redis_memory_used", "0MB")
            },
            "breakdown_by_type": current_stats.get("breakdown", {}),
            "trends": trend_analysis,
            "status": "active" if cache_service.is_initialized() else "inactive"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing cache performance: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze cache performance"
        )


@router.get("/config", summary="Cache Configuration")
async def cache_config(
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Configuration actuelle du cache.
    
    Retourne les stratégies de cache par type de données
    et les seuils configurés.
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Récupérer configuration depuis cache manager
        cache_configs = cache_service.cache_manager.cache.CACHE_CONFIGS
        namespaces = cache_service.cache_manager.namespaces
        
        # Formater pour API
        config_data = {}
        for cache_type, config in cache_configs.items():
            config_data[cache_type] = {
                "ttl_seconds": config.ttl,
                "strategy": config.strategy.value,
                "max_size_kb": config.max_size,
                "refresh_threshold": config.refresh_threshold,
                "compression_enabled": config.compress,
                "serializer": config.serializer
            }
        
        return {
            "cache_types": config_data,
            "namespaces": namespaces,
            "total_types": len(cache_configs),
            "service_status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving cache config: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache configuration"
        )


@router.get("/keys", summary="Cache Keys Sample")
async def cache_keys_sample(
    pattern: str = Query("*", description="Pattern pour filtrer les clés"),
    limit: int = Query(100, ge=1, le=1000),
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Échantillon des clés de cache pour debugging.
    
    Args:
        pattern: Pattern Redis pour filtrer les clés (ex: "user:*")
        limit: Nombre maximum de clés à retourner
        
    Note: Nécessite les droits administrateur.
    """
    # Vérification droits admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for cache inspection"
        )
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        redis_client = cache_service.redis_client
        
        # Récupérer clés avec pattern
        keys = await redis_client.keys(pattern)
        
        # Limiter résultats
        sample_keys = keys[:limit]
        
        # Récupérer TTL pour quelques clés
        key_details = []
        for key in sample_keys[:10]:  # Détails pour 10 premières clés seulement
            try:
                ttl = await redis_client.ttl(key.decode() if isinstance(key, bytes) else key)
                size = await redis_client.memory_usage(key.decode() if isinstance(key, bytes) else key)
                
                key_details.append({
                    "key": key.decode() if isinstance(key, bytes) else key,
                    "ttl_seconds": ttl,
                    "size_bytes": size or 0
                })
            except Exception:
                # Ignorer erreurs pour clés individuelles
                pass
        
        return {
            "pattern": pattern,
            "total_matches": len(keys),
            "sample_size": len(sample_keys),
            "keys": [k.decode() if isinstance(k, bytes) else k for k in sample_keys],
            "key_details": key_details
        }
        
    except Exception as e:
        logger.error(f"Error sampling cache keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to sample cache keys"
        )


@router.get("/analytics/dashboard", summary="Cache Analytics Dashboard")
async def cache_analytics_dashboard(
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Tableau de bord analytics du cache avec métriques avancées.
    
    Retourne un dashboard complet avec:
    - Métriques de performance en temps réel
    - Tendances et alertes
    - Recommandations d'optimisation
    - Données pour visualisation
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Vérifier si analytics est disponible
        if not hasattr(cache_service, 'cache_analytics') or not cache_service.cache_analytics:
            # Fallback to basic stats
            stats = await cache_service.get_stats()
            return {
                "analytics_available": False,
                "basic_stats": stats,
                "message": "Advanced analytics not available - showing basic cache statistics"
            }
        
        # Récupérer dashboard analytics complet
        dashboard_data = await cache_service.cache_analytics.get_performance_dashboard()
        
        return {
            "analytics_available": True,
            **dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error retrieving cache analytics dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache analytics dashboard"
        )


@router.get("/optimization/stats", summary="Cache Optimization Statistics")
async def cache_optimization_stats(
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Statistiques d'optimisation du cache.
    
    Retourne les métriques d'optimisation intelligente:
    - Efficacité du prefetching prédictif
    - Ajustements TTL dynamiques
    - Partitionnement des workloads
    - Configuration actuelle
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Vérifier si optimizer est disponible
        if not hasattr(cache_service, 'performance_optimizer') or not cache_service.performance_optimizer:
            return {
                "optimization_available": False,
                "message": "Cache performance optimizer not available"
            }
        
        # Récupérer stats d'optimisation
        optimization_stats = await cache_service.performance_optimizer.get_optimization_stats()
        
        return {
            "optimization_available": True,
            **optimization_stats
        }
        
    except Exception as e:
        logger.error(f"Error retrieving optimization stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache optimization statistics"
        )


@router.post("/optimization/tune", summary="Tune Cache Optimization")
async def tune_cache_optimization(
    config_updates: Dict[str, Any],
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
):
    """
    Ajuster la configuration d'optimisation du cache.
    
    Args:
        config_updates: Mises à jour de configuration
    
    Note: Nécessite les droits administrateur.
    """
    # Vérification droits admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for cache optimization tuning"
        )
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Vérifier si optimizer est disponible
        if not hasattr(cache_service, 'performance_optimizer') or not cache_service.performance_optimizer:
            raise HTTPException(
                status_code=503,
                detail="Cache performance optimizer not available"
            )
        
        # Appliquer les mises à jour
        await cache_service.performance_optimizer.tune_configuration(config_updates)
        
        return {
            "success": True,
            "message": "Cache optimization configuration updated",
            "updated_config": config_updates,
            "updated_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Error tuning cache optimization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update cache optimization configuration"
        )


@router.get("/analytics/report", summary="Export Cache Analytics Report")
async def export_analytics_report(
    format: str = Query("json", pattern="^(json|text)$"),
    hours: int = Query(24, ge=1, le=168),
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
):
    """
    Export détaillé des analytics de cache.
    
    Args:
        format: Format d'export (json ou text)
        hours: Période d'analyse en heures (1-168)
    """
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Vérifier si analytics est disponible
        if not hasattr(cache_service, 'cache_analytics') or not cache_service.cache_analytics:
            raise HTTPException(
                status_code=503,
                detail="Cache analytics not available"
            )
        
        # Générer rapport
        report = await cache_service.cache_analytics.export_analytics_report(format, hours)
        
        if format == "text":
            return PlainTextResponse(
                content=report,
                media_type="text/plain"
            )
        else:
            return {"report": report}
            
    except Exception as e:
        logger.error(f"Error exporting analytics report: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to export cache analytics report"
        )


@router.post("/analytics/alerts/{alert_id}/resolve", summary="Resolve Cache Alert")
async def resolve_cache_alert(
    alert_id: str,
    cache_service: CacheService = Depends(get_cache_service_dep),
    current_user = Depends(get_current_user)
):
    """
    Résoudre une alerte de cache.
    
    Args:
        alert_id: ID de l'alerte à résoudre
    
    Note: Nécessite les droits administrateur.
    """
    # Vérification droits admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for alert resolution"
        )
    
    if not cache_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Cache service not initialized"
        )
    
    try:
        # Vérifier si analytics est disponible
        if not hasattr(cache_service, 'cache_analytics') or not cache_service.cache_analytics:
            raise HTTPException(
                status_code=503,
                detail="Cache analytics not available"
            )
        
        # Résoudre l'alerte
        await cache_service.cache_analytics.resolve_alert(alert_id)
        
        return {
            "success": True,
            "message": f"Alert {alert_id} resolved",
            "resolved_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Error resolving cache alert: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to resolve cache alert"
        )