-- Performance Optimization Migrations for WakeDock
-- Comprehensive index and optimization strategy

-- =====================================================
-- SERVICES TABLE OPTIMIZATIONS
-- =====================================================

-- Composite index for frequently queried service combinations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_status_user_created 
ON services(status, user_id, created_at DESC) 
WHERE status IN ('running', 'starting', 'stopping', 'stopped', 'error');

-- Index for service health monitoring queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_health_status_updated
ON services(health_status, updated_at DESC)
WHERE health_status IS NOT NULL;

-- Index for user service counts
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_user_status_count
ON services(user_id, status)
WHERE status IS NOT NULL;

-- Partial index for active services only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_active_performance
ON services(id, name, status, updated_at)
WHERE status IN ('running', 'starting');

-- =====================================================
-- SERVICE_LOGS TABLE OPTIMIZATIONS  
-- =====================================================

-- Composite index for log queries with time filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_logs_service_time_level
ON service_logs(service_id, timestamp DESC, level)
WHERE timestamp >= NOW() - INTERVAL '30 days';

-- Partial index for recent error logs
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_logs_recent_errors
ON service_logs(service_id, timestamp DESC, level, message) 
WHERE timestamp >= NOW() - INTERVAL '7 days' 
  AND level IN ('ERROR', 'CRITICAL');

-- Index for log search and filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_logs_search
ON service_logs USING gin(to_tsvector('english', message))
WHERE level IN ('ERROR', 'WARN', 'INFO');

-- =====================================================
-- SERVICE_METRICS TABLE OPTIMIZATIONS
-- =====================================================

-- Time-series index for metrics with INCLUDE for covering queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_time_service_include 
ON service_metrics(service_id, timestamp DESC)
INCLUDE (cpu_usage, memory_usage, network_io, disk_io);

-- Index for recent metrics aggregation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_recent_aggregation
ON service_metrics(service_id, timestamp DESC)
WHERE timestamp >= NOW() - INTERVAL '24 hours';

-- Partial index for high resource usage detection
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_high_usage
ON service_metrics(service_id, timestamp, cpu_usage, memory_usage)
WHERE cpu_usage > 80 OR memory_usage > 80;

-- =====================================================
-- SYSTEM STATISTICS AND EXTENDED STATISTICS
-- =====================================================

-- Multi-column statistics for better query planning
CREATE STATISTICS IF NOT EXISTS stats_services_multi 
ON status, user_id, created_at FROM services;

CREATE STATISTICS IF NOT EXISTS stats_metrics_correlation
ON service_id, timestamp, cpu_usage, memory_usage FROM service_metrics;

CREATE STATISTICS IF NOT EXISTS stats_logs_service_level
ON service_id, level, timestamp FROM service_logs;

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

-- Index sur la vue matérialisée
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_metrics_hourly_unique 
ON mv_service_metrics_hourly(service_id, hour);

-- Vue pour dashboard rapide
CREATE OR REPLACE VIEW v_dashboard_quick AS
SELECT 
    s.status,
    COUNT(*) as service_count,
    COALESCE(AVG(m.avg_cpu), 0) as avg_cpu,
    COALESCE(AVG(m.avg_memory), 0) as avg_memory
FROM services s
LEFT JOIN mv_service_metrics_hourly m ON s.id = m.service_id 
    AND m.hour >= DATE_TRUNC('hour', NOW() - INTERVAL '1 hour')
GROUP BY s.status;

-- Fonction pour refresh automatique de la vue matérialisée
CREATE OR REPLACE FUNCTION refresh_metrics_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_service_metrics_hourly;
END;
$$ LANGUAGE plpgsql;

-- Job automatique (nécessite pg_cron extension)
-- SELECT cron.schedule('refresh-metrics-mv', '0 * * * *', 'SELECT refresh_metrics_mv();');
