"""
Optimisations de performance pour l'API FastAPI
Includes middleware, caching, and response optimization
"""

import asyncio
import time
import gzip
from typing import Callable, Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.compression import CompressionMiddleware
from starlette.middleware.gzip import GZipMiddleware
import logging
import json
from datetime import datetime, timedelta

from ..cache.intelligent import get_cache, cached

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware pour monitoring et optimisation des performances"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.request_times: Dict[str, list] = {}
        self.slow_requests: list = []
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring"""
        start_time = time.time()
        
        # Headers pour performance
        request.state.start_time = start_time
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
        
        # Calcul du temps de traitement
        process_time = time.time() - start_time
        
        # Logging des requêtes lentes
        if process_time > 1.0:  # Plus de 1 seconde
            slow_request = {
                "method": request.method,
                "url": str(request.url),
                "duration": process_time,
                "timestamp": datetime.now().isoformat(),
                "user_agent": request.headers.get("user-agent", "unknown")
            }
            self.slow_requests.append(slow_request)
            logger.warning(f"Slow request: {request.method} {request.url.path} - {process_time:.3f}s")
        
        # Stockage des temps pour statistiques
        endpoint = f"{request.method}:{request.url.path}"
        if endpoint not in self.request_times:
            self.request_times[endpoint] = []
        
        self.request_times[endpoint].append(process_time)
        
        # Limit history to last 1000 requests per endpoint
        if len(self.request_times[endpoint]) > 1000:
            self.request_times[endpoint] = self.request_times[endpoint][-1000:]
        
        # Headers de performance dans la réponse
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Timestamp"] = str(int(start_time))
        
        return response
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        stats = {}
        
        for endpoint, times in self.request_times.items():
            if times:
                sorted_times = sorted(times)
                stats[endpoint] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "p50": sorted_times[len(times)//2],
                    "p95": sorted_times[int(len(times)*0.95)] if len(times) > 20 else sorted_times[-1],
                    "p99": sorted_times[int(len(times)*0.99)] if len(times) > 100 else sorted_times[-1],
                    "max": max(times),
                    "min": min(times)
                }
        
        return {
            "endpoints": stats,
            "slow_requests_count": len(self.slow_requests),
            "recent_slow_requests": self.slow_requests[-10:] if self.slow_requests else []
        }


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware pour mise en cache automatique des réponses"""
    
    def __init__(self, app: FastAPI, cache_patterns: Dict[str, int] = None):
        super().__init__(app)
        self.cache_patterns = cache_patterns or {
            "/api/v1/services": 30,      # 30 secondes
            "/api/v1/dashboard": 15,     # 15 secondes  
            "/api/v1/metrics": 60,       # 1 minute
            "/api/v1/system": 120        # 2 minutes
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Cache GET requests matching patterns"""
        
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if URL matches cache patterns
        cache_ttl = self._get_cache_ttl(str(request.url.path))
        if not cache_ttl:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        try:
            cache = await get_cache()
            
            # Try to get from cache
            cached_response = await cache.get("api_responses", cache_key)
            if cached_response:
                return JSONResponse(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers={**cached_response["headers"], "X-Cache": "HIT"}
                )
            
            # Cache miss - call endpoint
            response = await call_next(request)
            
            # Cache successful responses
            if response.status_code == 200:
                # Read response content
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                try:
                    content = json.loads(response_body.decode())
                    cached_data = {
                        "content": content,
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    }
                    
                    await cache.set("api_responses", cache_key, cached_data, ttl=cache_ttl)
                    
                    # Return new response with cache headers
                    return JSONResponse(
                        content=content,
                        status_code=response.status_code,
                        headers={**dict(response.headers), "X-Cache": "MISS"}
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Can't cache non-JSON responses
                    pass
            
            return response
            
        except Exception as e:
            logger.error(f"Cache middleware error: {e}")
            return await call_next(request)
    
    def _get_cache_ttl(self, path: str) -> Optional[int]:
        """Retourne le TTL de cache pour un chemin donné"""
        for pattern, ttl in self.cache_patterns.items():
            if path.startswith(pattern):
                return ttl
        return None
    
    def _generate_cache_key(self, request: Request) -> str:
        """Génère une clé de cache unique pour la requête"""
        key_parts = [
            request.method,
            str(request.url.path),
            str(request.url.query),
            request.headers.get("authorization", "anonymous")[:50]  # Truncate auth
        ]
        return ":".join(key_parts)


class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware pour optimisation des réponses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Optimize response based on client capabilities"""
        
        response = await call_next(request)
        
        # Add performance headers
        response.headers["Cache-Control"] = "public, max-age=30"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        
        # Compression hints
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" in accept_encoding and not response.headers.get("content-encoding"):
            response.headers["Vary"] = "Accept-Encoding"
        
        return response


class ConnectionPoolingMiddleware(BaseHTTPMiddleware):
    """Middleware pour gestion optimisée des connexions"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.active_connections = 0
        self.max_connections = 1000
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Manage connection pooling"""
        
        if self.active_connections >= self.max_connections:
            return JSONResponse(
                status_code=503,
                content={"error": "Server too busy, please try again later"}
            )
        
        self.active_connections += 1
        try:
            response = await call_next(request)
            return response
        finally:
            self.active_connections -= 1


def setup_performance_middleware(app: FastAPI):
    """Configure tous les middlewares de performance"""
    
    # Compression middleware
    app.add_middleware(
        CompressionMiddleware,
        minimum_size=1000  # Compress responses > 1KB
    )
    
    # Custom middlewares (order matters!)
    app.add_middleware(ConnectionPoolingMiddleware)
    app.add_middleware(ResponseOptimizationMiddleware)
    app.add_middleware(CacheMiddleware)
    app.add_middleware(PerformanceMiddleware)
    
    logger.info("Performance middleware configured successfully")


# Décorateurs pour endpoints optimisés
def optimized_endpoint(cache_ttl: int = 0):
    """Décorateur pour endpoints optimisés"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > 0.5:  # Log slow endpoints
                    logger.warning(f"Slow endpoint {func.__name__}: {duration:.3f}s")
                
                return result
                
            except Exception as e:
                logger.error(f"Endpoint {func.__name__} failed: {e}")
                raise
        
        return wrapper
    return decorator


# API utilities pour monitoring
class PerformanceAPI:
    """API endpoints pour monitoring des performances"""
    
    def __init__(self, performance_middleware: PerformanceMiddleware):
        self.perf_middleware = performance_middleware
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Endpoint pour statistiques de performance"""
        api_stats = self.perf_middleware.get_performance_stats()
        
        # Ajouter stats de cache si disponible
        try:
            cache = await get_cache()
            cache_stats = cache.get_stats()
        except Exception:
            cache_stats = {"error": "Cache not available"}
        
        return {
            "api": api_stats,
            "cache": cache_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def clear_performance_cache(self) -> Dict[str, str]:
        """Clear performance cache"""
        try:
            cache = await get_cache()
            await cache.invalidate_pattern("api_responses:*")
            return {"message": "Performance cache cleared successfully"}
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {"error": str(e)}


# Background tasks pour optimisation
async def performance_cleanup_task():
    """Tâche de nettoyage périodique"""
    while True:
        try:
            # Cleanup cache periodically
            cache = await get_cache()
            await cache._cleanup_local_cache()
            
            logger.debug("Performance cleanup completed")
            
        except Exception as e:
            logger.error(f"Performance cleanup failed: {e}")
        
        # Wait 5 minutes before next cleanup
        await asyncio.sleep(300)


def start_performance_tasks():
    """Démarre les tâches de performance en arrière-plan"""
    asyncio.create_task(performance_cleanup_task())
    logger.info("Performance background tasks started")
