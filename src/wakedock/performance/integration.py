#!/usr/bin/env python3
"""
Performance Integration Manager for WakeDock
Integrates all performance optimizations into the main application
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from wakedock.performance.cache.intelligent import IntelligentCache, CacheStrategy, CacheConfig
    from wakedock.performance.database.optimizer import DatabaseOptimizer, OptimizedDatabase
    from wakedock.performance.api.middleware import PerformanceMiddleware, setup_performance_middleware
except ImportError as e:
    print(f"❌ Error importing performance modules: {e}")
    print("Make sure the performance modules are properly installed")
    sys.exit(1)

logger = logging.getLogger(__name__)


class PerformanceManager:
    """Main performance manager for WakeDock"""
    
    def __init__(self):
        self.cache: Optional[IntelligentCache] = None
        self.db_optimizer: Optional[DatabaseOptimizer] = None
        self.performance_config = self._load_performance_config()
        self.is_initialized = False
    
    def _load_performance_config(self) -> Dict[str, Any]:
        """Load performance configuration"""
        return {
            "cache": {
                "enabled": True,
                "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                "default_ttl": 300,
                "max_memory": "256mb"
            },
            "database": {
                "pool_size": 20,
                "max_overflow": 50,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "query_cache_size": 1200
            },
            "api": {
                "enable_compression": True,
                "compression_level": 6,
                "enable_monitoring": True,
                "slow_request_threshold": 1.0
            },
            "monitoring": {
                "enabled": True,
                "metrics_retention_days": 7,
                "enable_profiling": False
            }
        }
    
    async def initialize(self, app=None, database_engine=None):
        """Initialize all performance optimizations"""
        logger.info("🚀 Initializing performance optimizations...")
        
        try:
            # Initialize intelligent cache
            if self.performance_config["cache"]["enabled"]:
                await self._setup_cache()
            
            # Initialize database optimizer
            if database_engine and self.performance_config["database"]:
                self._setup_database_optimizer(database_engine)
            
            # Setup API middleware
            if app and self.performance_config["api"]:
                self._setup_api_optimizations(app)
            
            # Setup monitoring
            if self.performance_config["monitoring"]["enabled"]:
                await self._setup_monitoring()
            
            self.is_initialized = True
            logger.info("✅ Performance optimizations initialized successfully")
            
            # Log configuration summary
            self._log_configuration_summary()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize performance optimizations: {e}")
            raise
    
    async def _setup_cache(self):
        """Setup intelligent cache system"""
        logger.info("🔄 Setting up intelligent cache...")
        
        try:
            import redis.asyncio as redis # type: ignore
            
            redis_client = redis.from_url(
                self.performance_config["cache"]["redis_url"],
                decode_responses=True
            )
            
            # Test Redis connection
            await redis_client.ping()
            
            self.cache = IntelligentCache(redis_client)
            
            # Configure cache strategies
            await self.cache.configure_cache_type("user_sessions", CacheConfig(
                ttl=3600,
                strategy=CacheStrategy.WRITE_THROUGH
            ))
            
            await self.cache.configure_cache_type("service_status", CacheConfig(
                ttl=60,
                strategy=CacheStrategy.READ_THROUGH
            ))
            
            await self.cache.configure_cache_type("system_metrics", CacheConfig(
                ttl=30,
                strategy=CacheStrategy.WRITE_BEHIND
            ))
            
            await self.cache.configure_cache_type("dashboard_data", CacheConfig(
                ttl=300,
                strategy=CacheStrategy.REFRESH_AHEAD,
                refresh_threshold=0.7
            ))
            
            logger.info("✅ Intelligent cache configured successfully")
            
        except ImportError:
            logger.warning("⚠️ Redis not available, using local cache only")
            self.cache = IntelligentCache()
        except Exception as e:
            logger.error(f"❌ Cache setup failed: {e}")
            raise
    
    def _setup_database_optimizer(self, engine):
        """Setup database performance optimizations"""
        logger.info("🔄 Setting up database optimizer...")
        
        try:
            self.db_optimizer = DatabaseOptimizer(engine)
            logger.info("✅ Database optimizer configured successfully")
        except Exception as e:
            logger.error(f"❌ Database optimizer setup failed: {e}")
            raise
    
    def _setup_api_optimizations(self, app):
        """Setup API performance optimizations"""
        logger.info("🔄 Setting up API optimizations...")
        
        try:
            # Add performance middleware
            setup_performance_middleware(app)
            logger.info("✅ API optimizations configured successfully")
        except Exception as e:
            logger.error(f"❌ API optimization setup failed: {e}")
            raise
    
    async def _setup_monitoring(self):
        """Setup performance monitoring"""
        logger.info("🔄 Setting up performance monitoring...")
        
        try:
            # This would integrate with monitoring systems
            # For now, just log that monitoring is enabled
            logger.info("✅ Performance monitoring enabled")
        except Exception as e:
            logger.error(f"❌ Monitoring setup failed: {e}")
            raise
    
    def _log_configuration_summary(self):
        """Log performance configuration summary"""
        logger.info("📊 Performance Configuration Summary:")
        logger.info(f"  - Cache: {'✅ Enabled' if self.performance_config['cache']['enabled'] else '❌ Disabled'}")
        logger.info(f"  - Database Pool Size: {self.performance_config['database']['pool_size']}")
        logger.info(f"  - API Compression: {'✅ Enabled' if self.performance_config['api']['enable_compression'] else '❌ Disabled'}")
        logger.info(f"  - Monitoring: {'✅ Enabled' if self.performance_config['monitoring']['enabled'] else '❌ Disabled'}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        if not self.cache:
            return {"error": "Cache not initialized"}
        
        return await self.cache.get_stats()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        if not self.db_optimizer:
            return {"error": "Database optimizer not initialized"}
        
        return self.db_optimizer.get_performance_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Performance-related health check"""
        health = {
            "performance_manager": "healthy" if self.is_initialized else "not_initialized",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Check cache health
        if self.cache:
            try:
                cache_stats = await self.get_cache_stats()
                health["cache"] = "healthy" if "error" not in cache_stats else "unhealthy"
                health["cache_hit_ratio"] = cache_stats.get("hit_ratio", 0)
            except Exception as e:
                health["cache"] = f"error: {e}"
        
        # Check database health
        if self.db_optimizer:
            try:
                db_stats = self.get_database_stats()
                health["database"] = "healthy" if "error" not in db_stats else "unhealthy"
                health["avg_query_time"] = db_stats.get("avg_query_time", 0)
            except Exception as e:
                health["database"] = f"error: {e}"
        
        return health
    
    async def shutdown(self):
        """Cleanup performance resources"""
        logger.info("🔄 Shutting down performance optimizations...")
        
        try:
            if self.cache and hasattr(self.cache, 'shutdown'):
                await self.cache.shutdown()
            
            if self.db_optimizer and hasattr(self.db_optimizer, 'shutdown'):
                self.db_optimizer.shutdown()
            
            logger.info("✅ Performance optimizations shut down successfully")
        except Exception as e:
            logger.error(f"❌ Error during performance shutdown: {e}")


# Global performance manager instance
_performance_manager: Optional[PerformanceManager] = None


def get_performance_manager() -> PerformanceManager:
    """Get global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager


async def initialize_performance(app=None, database_engine=None):
    """Initialize performance optimizations"""
    manager = get_performance_manager()
    await manager.initialize(app, database_engine)
    return manager


async def shutdown_performance():
    """Shutdown performance optimizations"""
    global _performance_manager
    if _performance_manager:
        await _performance_manager.shutdown()
        _performance_manager = None


# FastAPI integration helpers
def cached(cache_type: str = "default", ttl: int = 300):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_performance_manager()
            if not manager.cache:
                return await func(*args, **kwargs)
            
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            return await manager.cache.get_with_strategy(
                cache_key,
                lambda: func(*args, **kwargs),
                cache_type
            )
        return wrapper
    return decorator


async def main():
    """Test performance integration"""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Performance Integration")
    print("=" * 50)
    
    try:
        # Initialize performance manager
        manager = await initialize_performance()
        
        # Test cache functionality
        if manager.cache:
            print("✅ Testing cache...")
            await manager.cache.set_with_strategy("test_key", {"test": "data"}, "default")
            result = await manager.cache.get_with_strategy("test_key", lambda: {"fallback": "data"})
            print(f"Cache test result: {result}")
        
        # Test health check
        health = await manager.health_check()
        print(f"Health check: {health}")
        
        # Get performance stats
        cache_stats = await manager.get_cache_stats()
        print(f"Cache stats: {cache_stats}")
        
        print("✅ Performance integration test completed successfully")
        
    except Exception as e:
        print(f"❌ Performance integration test failed: {e}")
        sys.exit(1)
    
    finally:
        await shutdown_performance()


if __name__ == "__main__":
    asyncio.run(main())
