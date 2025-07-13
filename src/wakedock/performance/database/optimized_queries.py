"""
Optimized Database Queries and Repository Pattern
High-performance database access with caching integration
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy import text, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import select

from wakedock.database.models import Service, ServiceLog, ServiceMetric, User, Backup
from wakedock.cache.redis_cache import cache, CacheKey


class OptimizedServiceRepository:
    """Optimized service repository with caching"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_summary(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data in single optimized query"""
        cache_key = CacheKey.dashboard_summary(user_id)
        
        async def fetch_summary():
            # Single CTE query for maximum efficiency
            query = text("""
                WITH RECURSIVE 
                service_summary AS (
                    SELECT 
                        status,
                        COUNT(*) as count,
                        COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy_count,
                        COUNT(*) FILTER (WHERE health_status = 'unhealthy') as unhealthy_count
                    FROM services s
                    WHERE (:user_id IS NULL OR s.user_id = :user_id)
                        AND s.created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY status
                ),
                latest_metrics AS (
                    SELECT DISTINCT ON (sm.service_id)
                        sm.service_id,
                        sm.cpu_usage,
                        sm.memory_usage,
                        sm.network_io,
                        sm.disk_io,
                        sm.timestamp
                    FROM service_metrics sm
                    INNER JOIN services s ON sm.service_id = s.id
                    WHERE (:user_id IS NULL OR s.user_id = :user_id)
                        AND sm.timestamp >= NOW() - INTERVAL '1 hour'
                    ORDER BY sm.service_id, sm.timestamp DESC
                ),
                system_averages AS (
                    SELECT 
                        AVG(cpu_usage) as avg_cpu,
                        AVG(memory_usage) as avg_memory,
                        MAX(cpu_usage) as max_cpu,
                        MAX(memory_usage) as max_memory,
                        COUNT(DISTINCT service_id) as services_with_metrics
                    FROM latest_metrics
                ),
                alert_summary AS (
                    SELECT 
                        COUNT(*) FILTER (WHERE level = 'ERROR') as critical_alerts,
                        COUNT(*) FILTER (WHERE level = 'WARN') as warning_alerts,
                        COUNT(*) FILTER (WHERE level = 'INFO') as info_logs
                    FROM service_logs sl
                    INNER JOIN services s ON sl.service_id = s.id
                    WHERE (:user_id IS NULL OR s.user_id = :user_id)
                        AND sl.timestamp >= NOW() - INTERVAL '1 hour'
                ),
                backup_summary AS (
                    SELECT 
                        COUNT(*) as total_backups,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed_backups,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_backups,
                        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as recent_backups
                    FROM backups b
                    INNER JOIN services s ON b.service_id = s.id
                    WHERE (:user_id IS NULL OR s.user_id = :user_id)
                )
                SELECT 
                    -- Service counts by status
                    COALESCE(
                        json_object_agg(
                            ss.status, 
                            json_build_object(
                                'count', ss.count,
                                'healthy', ss.healthy_count,
                                'unhealthy', ss.unhealthy_count
                            )
                        ) FILTER (WHERE ss.status IS NOT NULL), 
                        '{}'::json
                    ) as services,
                    
                    -- System metrics
                    json_build_object(
                        'avg_cpu', COALESCE(sa.avg_cpu, 0),
                        'avg_memory', COALESCE(sa.avg_memory, 0),
                        'max_cpu', COALESCE(sa.max_cpu, 0),
                        'max_memory', COALESCE(sa.max_memory, 0),
                        'services_with_metrics', COALESCE(sa.services_with_metrics, 0)
                    ) as system_metrics,
                    
                    -- Alert counts
                    json_build_object(
                        'critical', COALESCE(als.critical_alerts, 0),
                        'warning', COALESCE(als.warning_alerts, 0),
                        'info', COALESCE(als.info_logs, 0)
                    ) as alerts,
                    
                    -- Backup summary
                    json_build_object(
                        'total', COALESCE(bs.total_backups, 0),
                        'completed', COALESCE(bs.completed_backups, 0),
                        'failed', COALESCE(bs.failed_backups, 0),
                        'recent', COALESCE(bs.recent_backups, 0)
                    ) as backups,
                    
                    -- Metadata
                    NOW() as snapshot_time
                FROM service_summary ss
                FULL OUTER JOIN system_averages sa ON true
                FULL OUTER JOIN alert_summary als ON true
                FULL OUTER JOIN backup_summary bs ON true
            """)
            
            result = await self.db.execute(query, {'user_id': user_id})
            row = result.fetchone()
            
            if row:
                return {
                    'services': dict(row.services) if row.services else {},
                    'system_metrics': dict(row.system_metrics),
                    'alerts': dict(row.alerts),
                    'backups': dict(row.backups),
                    'snapshot_time': row.snapshot_time.isoformat(),
                    'user_id': user_id
                }
            
            return {
                'services': {},
                'system_metrics': {'avg_cpu': 0, 'avg_memory': 0, 'max_cpu': 0, 'max_memory': 0},
                'alerts': {'critical': 0, 'warning': 0, 'info': 0},
                'backups': {'total': 0, 'completed': 0, 'failed': 0, 'recent': 0},
                'snapshot_time': datetime.now().isoformat(),
                'user_id': user_id
            }
        
        return await cache.get_or_set(cache_key, fetch_summary, ttl=60)  # 1 minute cache
    
    async def get_services_optimized(
        self, 
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """Get services with optimized loading and caching"""
        cache_key = CacheKey.service_list(user_id, status)
        
        async def fetch_services():
            # Build base query with optimal joins
            query = text("""
                SELECT 
                    s.id,
                    s.name,
                    s.status,
                    s.health_status,
                    s.docker_image,
                    s.created_at,
                    s.updated_at,
                    s.user_id,
                    -- Latest metrics (LATERAL join for efficiency)
                    m.cpu_usage as latest_cpu,
                    m.memory_usage as latest_memory,
                    m.network_io as latest_network_io,
                    m.disk_io as latest_disk_io,
                    m.timestamp as metrics_timestamp,
                    -- Recent error count
                    COALESCE(e.error_count, 0) as recent_errors
                FROM services s
                LEFT JOIN LATERAL (
                    SELECT cpu_usage, memory_usage, network_io, disk_io, timestamp
                    FROM service_metrics sm 
                    WHERE sm.service_id = s.id 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ) m ON true
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) as error_count
                    FROM service_logs sl
                    WHERE sl.service_id = s.id 
                        AND sl.level = 'ERROR'
                        AND sl.timestamp >= NOW() - INTERVAL '1 hour'
                ) e ON true
                WHERE (:user_id IS NULL OR s.user_id = :user_id)
                    AND (:status IS NULL OR s.status = :status)
                ORDER BY s.updated_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.db.execute(query, {
                'user_id': user_id,
                'status': status,
                'limit': limit,
                'offset': offset
            })
            
            services = []
            for row in result:
                service_data = {
                    'id': row.id,
                    'name': row.name,
                    'status': row.status,
                    'health_status': row.health_status,
                    'docker_image': row.docker_image,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                    'user_id': row.user_id,
                    'recent_errors': row.recent_errors
                }
                
                if include_metrics and row.latest_cpu is not None:
                    service_data['latest_metrics'] = {
                        'cpu_usage': row.latest_cpu,
                        'memory_usage': row.latest_memory,
                        'network_io': row.latest_network_io,
                        'disk_io': row.latest_disk_io,
                        'timestamp': row.metrics_timestamp.isoformat() if row.metrics_timestamp else None
                    }
                
                services.append(service_data)
            
            return services
        
        return await cache.get_or_set(cache_key, fetch_services, ttl=30)  # 30 second cache
    
    async def get_service_metrics_aggregated(
        self, 
        service_id: str, 
        timeframe: str = "1h",
        aggregation: str = "5m"
    ) -> List[Dict[str, Any]]:
        """Get aggregated metrics for a service"""
        cache_key = CacheKey.service_metrics(service_id, timeframe)
        
        async def fetch_metrics():
            # Map timeframe to SQL intervals
            timeframe_map = {
                "1h": "1 hour",
                "6h": "6 hours", 
                "24h": "24 hours",
                "7d": "7 days",
                "30d": "30 days"
            }
            
            aggregation_map = {
                "1m": "1 minute",
                "5m": "5 minutes",
                "15m": "15 minutes",
                "1h": "1 hour",
                "6h": "6 hours",
                "1d": "1 day"
            }
            
            interval = timeframe_map.get(timeframe, "1 hour")
            agg_interval = aggregation_map.get(aggregation, "5 minutes")
            
            query = text("""
                SELECT 
                    DATE_TRUNC(:aggregation, timestamp) as time_bucket,
                    AVG(cpu_usage) as avg_cpu,
                    MAX(cpu_usage) as max_cpu,
                    MIN(cpu_usage) as min_cpu,
                    AVG(memory_usage) as avg_memory,
                    MAX(memory_usage) as max_memory,
                    MIN(memory_usage) as min_memory,
                    AVG((network_io->>'rx')::bigint) as avg_network_rx,
                    AVG((network_io->>'tx')::bigint) as avg_network_tx,
                    AVG(disk_io) as avg_disk_io,
                    COUNT(*) as sample_count
                FROM service_metrics
                WHERE service_id = :service_id
                    AND timestamp >= NOW() - INTERVAL :timeframe
                GROUP BY time_bucket
                ORDER BY time_bucket ASC
            """)
            
            result = await self.db.execute(query, {
                'service_id': service_id,
                'timeframe': interval,
                'aggregation': agg_interval
            })
            
            metrics = []
            for row in result:
                metrics.append({
                    'timestamp': row.time_bucket.isoformat(),
                    'cpu': {
                        'avg': round(row.avg_cpu or 0, 2),
                        'max': round(row.max_cpu or 0, 2),
                        'min': round(row.min_cpu or 0, 2)
                    },
                    'memory': {
                        'avg': round(row.avg_memory or 0, 2),
                        'max': round(row.max_memory or 0, 2),
                        'min': round(row.min_memory or 0, 2)
                    },
                    'network': {
                        'rx': int(row.avg_network_rx or 0),
                        'tx': int(row.avg_network_tx or 0)
                    },
                    'disk_io': int(row.avg_disk_io or 0),
                    'sample_count': row.sample_count
                })
            
            return metrics
        
        # Longer cache for aggregated data
        cache_ttl = {"1h": 60, "6h": 300, "24h": 600, "7d": 1800, "30d": 3600}
        ttl = cache_ttl.get(timeframe, 300)
        
        return await cache.get_or_set(cache_key, fetch_metrics, ttl=ttl)
    
    async def get_service_logs_optimized(
        self, 
        service_id: str,
        level: Optional[str] = None,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get service logs with efficient filtering"""
        cache_key = CacheKey.service_logs(service_id, level, limit)
        
        async def fetch_logs():
            conditions = ["service_id = :service_id"]
            params = {'service_id': service_id, 'limit': limit}
            
            if level:
                conditions.append("level = :level")
                params['level'] = level
            
            if since:
                conditions.append("timestamp >= :since")
                params['since'] = since
            else:
                # Default to last 24 hours for performance
                conditions.append("timestamp >= NOW() - INTERVAL '24 hours'")
            
            where_clause = " AND ".join(conditions)
            
            query = text(f"""
                SELECT 
                    id,
                    level,
                    message,
                    timestamp,
                    service_id
                FROM service_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(query, params)
            
            logs = []
            for row in result:
                logs.append({
                    'id': row.id,
                    'level': row.level,
                    'message': row.message,
                    'timestamp': row.timestamp.isoformat(),
                    'service_id': row.service_id
                })
            
            return logs
        
        # Shorter cache for logs (they change frequently)
        return await cache.get_or_set(cache_key, fetch_logs, ttl=30)
    
    async def invalidate_service_cache(self, service_id: str) -> None:
        """Invalidate all cache entries for a service"""
        await cache.invalidate_service(service_id)
    
    async def invalidate_user_cache(self, user_id: int) -> None:
        """Invalidate all cache entries for a user"""
        await cache.invalidate_user(user_id)


class CachedUserRepository:
    """Cached user repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile with caching"""
        cache_key = CacheKey.user_profile(user_id)
        
        async def fetch_user():
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        
        return await cache.get_or_set(cache_key, fetch_user, ttl=300)  # 5 minutes


class SystemStatsRepository:
    """System-wide statistics repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        cache_key = CacheKey.system_stats()
        
        async def fetch_stats():
            query = text("""
                SELECT 
                    -- Service counts
                    COUNT(DISTINCT s.id) as total_services,
                    COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'running') as running_services,
                    COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'stopped') as stopped_services,
                    COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'error') as error_services,
                    
                    -- User stats
                    COUNT(DISTINCT u.id) as total_users,
                    COUNT(DISTINCT u.id) FILTER (WHERE u.is_active = true) as active_users,
                    
                    -- Log stats (last 24h)
                    COUNT(DISTINCT sl.id) FILTER (
                        WHERE sl.timestamp >= NOW() - INTERVAL '24 hours'
                    ) as logs_24h,
                    COUNT(DISTINCT sl.id) FILTER (
                        WHERE sl.timestamp >= NOW() - INTERVAL '24 hours' 
                        AND sl.level = 'ERROR'
                    ) as errors_24h,
                    
                    -- Backup stats
                    COUNT(DISTINCT b.id) as total_backups,
                    COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') as completed_backups,
                    
                    -- System uptime (approximate)
                    EXTRACT(EPOCH FROM (NOW() - MIN(s.created_at))) / 86400 as system_age_days
                    
                FROM services s
                FULL OUTER JOIN users u ON true
                FULL OUTER JOIN service_logs sl ON sl.service_id = s.id
                FULL OUTER JOIN backups b ON b.service_id = s.id
            """)
            
            result = await self.db.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    'services': {
                        'total': row.total_services or 0,
                        'running': row.running_services or 0,
                        'stopped': row.stopped_services or 0,
                        'error': row.error_services or 0
                    },
                    'users': {
                        'total': row.total_users or 0,
                        'active': row.active_users or 0
                    },
                    'logs': {
                        'total_24h': row.logs_24h or 0,
                        'errors_24h': row.errors_24h or 0
                    },
                    'backups': {
                        'total': row.total_backups or 0,
                        'completed': row.completed_backups or 0
                    },
                    'system_age_days': round(row.system_age_days or 0, 1),
                    'timestamp': datetime.now().isoformat()
                }
            
            return {}
        
        return await cache.get_or_set(cache_key, fetch_stats, ttl=120)  # 2 minutes
