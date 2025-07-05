"""
Optimisations de performance pour la base de données
Implémente le monitoring et l'optimisation des requêtes
"""

from sqlalchemy import event, text, create_async_engine, select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import time
import logging
from datetime import datetime, timedelta

# Imports locaux - à ajuster selon la structure réelle
try:
    from wakedock.config import settings
except ImportError:
    settings = None

try:
    from wakedock.database.models import Service, ServiceStatus
except ImportError:
    # Définitions temporaires pour le développement
    Service = None
    ServiceStatus = None

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Optimisations performance base de données"""
    
    def __init__(self, engine):
        self.engine = engine
        self.query_times = []
        self.slow_queries = []
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        """Monitor les requêtes lentes"""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            
        @event.listens_for(self.engine, "after_cursor_execute")  
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            self.query_times.append(total)
            
            # Log requêtes lentes (>100ms)
            if total > 0.1:
                slow_query = {
                    'duration': total,
                    'statement': statement[:200],
                    'timestamp': datetime.now(),
                    'parameters': str(parameters)[:100] if parameters else None
                }
                self.slow_queries.append(slow_query)
                logger.warning(f"Slow query ({total:.3f}s): {statement[:100]}...")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        if not self.query_times:
            return {"message": "No queries recorded yet"}
            
        query_times = self.query_times[-1000:]  # Dernières 1000 requêtes
        
        return {
            "total_queries": len(self.query_times),
            "avg_query_time": sum(query_times) / len(query_times),
            "p50_query_time": sorted(query_times)[len(query_times)//2],
            "p95_query_time": sorted(query_times)[int(len(query_times)*0.95)],
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:] if self.slow_queries else []
        }


class OptimizedDatabase:
    """Configuration database optimisée pour performance"""
    
    @staticmethod
    def create_engine(database_url: str):
        """Crée un engine optimisé"""
        return create_async_engine(
            database_url,
            # Pool settings optimisés
            poolclass=QueuePool,
            pool_size=20,           # Connexions permanentes
            max_overflow=50,        # Connexions en burst
            pool_pre_ping=True,     # Vérification santé connexions
            pool_recycle=3600,      # Recyclage après 1h
            
            # Query settings
            query_cache_size=1200,  # Cache requêtes préparées
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "jit": "off",                    # Disable JIT pour petites queries
                    "shared_preload_libraries": "pg_stat_statements",
                    "log_min_duration_statement": "100",  # Log queries >100ms
                }
            }
        )


class OptimizedServiceRepository:
    """Repository avec requêtes optimisées"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_services_with_metrics(self, limit: int = 50) -> List:
        """Récupère services avec métriques en une requête optimisée"""
        
        if not Service:
            logger.warning("Service model not available")
            return []
        
        query = (
            select(Service)
            .options(
                # Charger relations en une requête
                selectinload(Service.metrics),
                selectinload(Service.logs).limit(10),  # Derniers 10 logs seulement
                joinedload(Service.user)  # Join simple pour user
            )
            .where(Service.status.in_([ServiceStatus.RUNNING, ServiceStatus.STARTING]))
            .order_by(Service.created_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_service_metrics_aggregate(self, service_id: str, hours: int = 24) -> Dict:
        """Métriques agrégées via SQL pour performance"""
        
        query = text("""
            SELECT 
                AVG(cpu_usage) as avg_cpu,
                MAX(cpu_usage) as max_cpu,
                AVG(memory_usage) as avg_memory,
                MAX(memory_usage) as max_memory,
                COUNT(*) as sample_count,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time
            FROM service_metrics 
            WHERE service_id = :service_id 
                AND timestamp >= NOW() - INTERVAL '%s hours'
        """ % hours)
        
        result = await self.db.execute(query, {"service_id": service_id})
        row = result.fetchone()
        
        if row:
            return {
                "avg_cpu": float(row.avg_cpu) if row.avg_cpu else 0,
                "max_cpu": float(row.max_cpu) if row.max_cpu else 0,
                "avg_memory": float(row.avg_memory) if row.avg_memory else 0,
                "max_memory": float(row.max_memory) if row.max_memory else 0,
                "sample_count": row.sample_count,
                "start_time": row.start_time,
                "end_time": row.end_time
            }
        
        return {
            "avg_cpu": 0, "max_cpu": 0, "avg_memory": 0, 
            "max_memory": 0, "sample_count": 0,
            "start_time": None, "end_time": None
        }
    
    async def get_services_dashboard_data(self) -> Dict[str, Any]:
        """Données dashboard optimisées en une requête"""
        
        query = text("""
            WITH service_stats AS (
                SELECT 
                    status,
                    COUNT(*) as count
                FROM services 
                GROUP BY status
            ),
            recent_metrics AS (
                SELECT 
                    AVG(cpu_usage) as avg_cpu,
                    AVG(memory_usage) as avg_memory
                FROM service_metrics 
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
            ),
            recent_alerts AS (
                SELECT COUNT(*) as alert_count
                FROM service_logs 
                WHERE level = 'ERROR' 
                    AND timestamp >= NOW() - INTERVAL '24 hours'
            )
            SELECT 
                json_object_agg(ss.status, ss.count) as service_counts,
                rm.avg_cpu,
                rm.avg_memory,
                ra.alert_count
            FROM service_stats ss
            CROSS JOIN recent_metrics rm
            CROSS JOIN recent_alerts ra
        """)
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        if row:
            return {
                "service_counts": row.service_counts or {},
                "avg_cpu": float(row.avg_cpu) if row.avg_cpu else 0,
                "avg_memory": float(row.avg_memory) if row.avg_memory else 0,
                "alert_count": row.alert_count or 0
            }
        
        return {
            "service_counts": {},
            "avg_cpu": 0,
            "avg_memory": 0,
            "alert_count": 0
        }


class QueryOptimizer:
    """Utilitaires d'optimisation de requêtes"""
    
    @staticmethod
    def explain_query(db: AsyncSession, query_text: str, params: Dict = None):
        """Analyse une requête avec EXPLAIN"""
        explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_text}")
        return db.execute(explain_query, params or {})
    
    @staticmethod
    async def get_slow_queries(db: AsyncSession, min_duration_ms: int = 100):
        """Récupère les requêtes lentes depuis pg_stat_statements"""
        query = text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            WHERE mean_time > :min_duration
            ORDER BY mean_time DESC 
            LIMIT 20
        """)
        
        result = await db.execute(query, {"min_duration": min_duration_ms})
        return [dict(row) for row in result.fetchall()]
    
    @staticmethod
    async def get_index_usage(db: AsyncSession):
        """Analyse l'utilisation des index"""
        query = text("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation,
                most_common_vals,
                most_common_freqs
            FROM pg_stats 
            WHERE schemaname = 'public'
                AND tablename IN ('services', 'service_metrics', 'service_logs')
            ORDER BY tablename, attname
        """)
        
        result = await db.execute(query)
        return [dict(row) for row in result.fetchall()]


# Instance globale pour monitoring
db_optimizer = None

def init_db_optimizer(engine):
    """Initialise le monitoring des performances DB"""
    global db_optimizer
    db_optimizer = DatabaseOptimizer(engine)
    return db_optimizer

def get_db_performance_stats():
    """Récupère les stats de performance DB"""
    if db_optimizer:
        return db_optimizer.get_performance_stats()
    return {"error": "Database optimizer not initialized"}
