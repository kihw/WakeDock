"""
Migration pour optimisations de performance
Ajoute les index optimisés et partitioning si nécessaire
"""

# migrations/004_performance_indexes.sql

-- Index composites pour requêtes fréquentes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_status_created 
ON services(status, created_at DESC) 
WHERE status IN ('running', 'starting', 'stopping');

-- Index pour requêtes par utilisateur
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_user_status 
ON services(user_id, status, created_at DESC);

-- Index partiel pour logs récents seulement
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_logs_recent 
ON service_logs(service_id, timestamp DESC, level) 
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- Index pour métriques par fenêtre temporelle
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_time_window 
ON service_metrics(service_id, timestamp DESC)
INCLUDE (cpu_usage, memory_usage, network_io);

-- Index pour recherche par nom de service
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_services_name_trgm 
ON services USING gin (name gin_trgm_ops);

-- Index pour métriques agrégées
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_aggregation 
ON service_metrics(service_id, DATE_TRUNC('hour', timestamp));

-- Statistiques étendues pour optimiseur
CREATE STATISTICS IF NOT EXISTS stats_services_status_user 
ON status, user_id FROM services;

CREATE STATISTICS IF NOT EXISTS stats_metrics_time_service 
ON service_id, timestamp FROM service_metrics;

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
