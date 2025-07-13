#!/usr/bin/env python
"""
Script pour appliquer les migrations de performance
"""
import asyncio
import logging
from pathlib import Path
from sqlalchemy import text
from src.wakedock.database.database import get_database

logger = logging.getLogger(__name__)

PERFORMANCE_MIGRATIONS = [
    """
    -- Index composites pour requêtes fréquentes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_status_created 
    ON services(status, created_at DESC) 
    WHERE status IN ('running', 'starting', 'stopping');
    """,
    """
    -- Index pour requêtes par utilisateur
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_user_status 
    ON services(user_id, status, created_at DESC);
    """,
    """
    -- Index partiel pour logs récents seulement
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_logs_recent 
    ON service_logs(service_id, timestamp DESC, level) 
    WHERE timestamp >= NOW() - INTERVAL '7 days';
    """,
    """
    -- Index pour métriques par fenêtre temporelle
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_time_window 
    ON service_metrics(service_id, timestamp DESC)
    INCLUDE (cpu_usage, memory_usage, network_io);
    """,
    """
    -- Vues matérialisées pour dashboard performance
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_service_metrics_hourly AS
    SELECT 
        service_id,
        DATE_TRUNC('hour', timestamp) as hour,
        AVG(cpu_usage) as avg_cpu,
        MAX(cpu_usage) as max_cpu,
        AVG(memory_usage) as avg_memory,
        MAX(memory_usage) as max_memory,
        COUNT(*) as sample_count
    FROM service_metrics 
    WHERE timestamp >= NOW() - INTERVAL '24 hours'
    GROUP BY service_id, DATE_TRUNC('hour', timestamp);
    """,
    """
    -- Index pour vue matérialisée
    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_service_metrics_hourly_unique 
    ON mv_service_metrics_hourly(service_id, hour);
    """
]

async def run_performance_migrations():
    """Exécute les migrations de performance"""
    try:
        db = get_database()
        await db.initialize()
        
        with db.get_session() as session:
            for i, migration in enumerate(PERFORMANCE_MIGRATIONS):
                try:
                    logger.info(f"Running migration {i+1}/{len(PERFORMANCE_MIGRATIONS)}")
                    session.execute(text(migration))
                    logger.info(f"Migration {i+1} completed successfully")
                except Exception as e:
                    logger.warning(f"Migration {i+1} failed (might already exist): {e}")
                    continue
        
        logger.info("All performance migrations completed")
        
    except Exception as e:
        logger.error(f"Performance migrations failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_performance_migrations())
