# ⚡ PERFORMANCE OPTIMISATION - WakeDock

**Priorité: 🟡 MOYENNE**  
**Timeline: 2-3 semaines**  
**Équipe: Performance Engineer + Backend Dev + DevOps + Frontend Dev**

## 📋 Vue d'Ensemble

Ce document détaille les optimisations de performance pour l'ensemble de la stack WakeDock. Suite à l'audit technique, plusieurs goulots d'étranglement ont été identifiés au niveau du backend Python, du frontend SvelteKit, de la base de données, et de l'infrastructure Docker.

---

## 🎯 OBJECTIFS DE PERFORMANCE

### 📊 Targets Spécifiques

```yaml
Backend Performance:
  - API Response Time: <200ms P95, <100ms P50
  - Database Query Time: <50ms P95, <20ms P50
  - Memory Usage: <512MB par container
  - CPU Usage: <50% en nominal

Frontend Performance:
  - First Contentful Paint: <1.5s
  - Largest Contentful Paint: <2.5s
  - Time to Interactive: <3s
  - Cumulative Layout Shift: <0.1

Infrastructure:
  - Container Start Time: <10s
  - Docker Image Size: <200MB
  - Network Latency: <50ms interne
  - Disk I/O: <100ms P95
```

---

## 🔧 OPTIMISATIONS BACKEND

### 1. Optimisation Base de Données

**Problème:** Requêtes N+1, pas d'indexation optimale, connexions multiples

**Solutions:**

```python
# src/wakedock/database/optimizations.py
from sqlalchemy import event, text
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.pool import QueuePool
import time

class DatabaseOptimizer:
    """Optimisations performance base de données"""
    
    def __init__(self, engine):
        self.engine = engine
        self.query_times = []
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
                logger.warning(f"Slow query ({total:.3f}s): {statement[:100]}...")

# Configuration pool optimisée
class OptimizedDatabase:
    """Configuration database optimisée pour performance"""
    
    @staticmethod
    def create_engine(database_url: str):
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

# Requêtes optimisées avec eager loading
class ServiceRepository:
    """Repository avec requêtes optimisées"""
    
    async def get_services_with_metrics(self) -> List[Service]:
        """Récupère services avec métriques en une requête"""
        
        return await self.db.execute(
            select(Service)
            .options(
                # Charger relations en une requête
                selectinload(Service.metrics)
                .selectinload(ServiceMetric.latest_values),
                
                selectinload(Service.logs)
                .limit(10)  # Derniers 10 logs seulement
                .options(selectinload(ServiceLog.level)),
                
                joinedload(Service.user)  # Join simple pour user
            )
            .where(Service.status.in_([ServiceStatus.RUNNING, ServiceStatus.STARTING]))
            .order_by(Service.created_at.desc())
        ).scalars().all()
    
    async def get_service_metrics_aggregate(self, service_id: str, hours: int = 24) -> Dict:
        """Métriques agrégées via SQL pour performance"""
        
        query = text("""
            SELECT 
                AVG(cpu_usage) as avg_cpu,
                MAX(cpu_usage) as max_cpu,
                AVG(memory_usage) as avg_memory,
                MAX(memory_usage) as max_memory,
                COUNT(*) as sample_count
            FROM service_metrics 
            WHERE service_id = :service_id 
                AND timestamp >= NOW() - INTERVAL ':hours hours'
        """)
        
        result = await self.db.execute(query, {
            "service_id": service_id,
            "hours": hours
        })
        
        return result.fetchone()._asdict()
```

**Index Optimization:**

```sql
-- migrations/004_performance_indexes.sql

-- Index composites pour requêtes fréquentes
CREATE INDEX CONCURRENTLY idx_services_status_created 
ON services(status, created_at DESC) 
WHERE status IN ('running', 'starting');

-- Index partiel pour logs récents
CREATE INDEX CONCURRENTLY idx_service_logs_recent 
ON service_logs(service_id, timestamp DESC) 
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- Index pour métriques par fenêtre temporelle
CREATE INDEX CONCURRENTLY idx_metrics_time_window 
ON service_metrics(service_id, timestamp DESC)
INCLUDE (cpu_usage, memory_usage);

-- Partitioning pour logs (si volume important)
CREATE TABLE service_logs_y2024m01 PARTITION OF service_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

### 2. Cache Redis Intelligent

```python
# src/wakedock/infrastructure/cache/intelligent.py
import asyncio
import json
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass
from enum import Enum

class CacheStrategy(Enum):
    """Stratégies de cache disponibles"""
    WRITE_THROUGH = "write_through"      # Cache + DB simultané
    WRITE_BEHIND = "write_behind"        # Cache immédiat, DB async
    REFRESH_AHEAD = "refresh_ahead"      # Refresh proactif
    READ_THROUGH = "read_through"        # Cache miss = DB fetch

@dataclass
class CacheConfig:
    """Configuration cache par type de données"""
    ttl: int
    strategy: CacheStrategy
    max_size: Optional[int] = None
    refresh_threshold: float = 0.8  # Refresh à 80% du TTL
    compress: bool = False

class IntelligentCache:
    """Cache Redis avec stratégies intelligentes"""
    
    CACHE_CONFIGS = {
        # Données quasi-statiques
        "user_permissions": CacheConfig(
            ttl=3600, strategy=CacheStrategy.REFRESH_AHEAD
        ),
        "system_config": CacheConfig(
            ttl=1800, strategy=CacheStrategy.WRITE_THROUGH
        ),
        
        # Données temps réel
        "system_metrics": CacheConfig(
            ttl=30, strategy=CacheStrategy.WRITE_BEHIND
        ),
        "service_status": CacheConfig(
            ttl=60, strategy=CacheStrategy.READ_THROUGH
        ),
        
        # Données calculées coûteuses
        "dashboard_overview": CacheConfig(
            ttl=300, strategy=CacheStrategy.REFRESH_AHEAD,
            refresh_threshold=0.7
        ),
        
        # Logs et historiques (compression)
        "service_logs": CacheConfig(
            ttl=900, strategy=CacheStrategy.READ_THROUGH,
            compress=True, max_size=1000
        )
    }
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.background_tasks = set()
    
    async def get_with_strategy(
        self, 
        key: str, 
        fetcher: Callable, 
        cache_type: str = "default"
    ) -> Any:
        """Récupération avec stratégie intelligente"""
        
        config = self.CACHE_CONFIGS.get(cache_type, 
            CacheConfig(ttl=300, strategy=CacheStrategy.READ_THROUGH))
        
        # Tenter récupération cache
        cached_data = await self._get_from_cache(key, config)
        
        if cached_data is not None:
            # Cache hit - vérifier si refresh nécessaire
            if config.strategy == CacheStrategy.REFRESH_AHEAD:
                await self._check_refresh_ahead(key, config, fetcher)
            return cached_data
        
        # Cache miss - stratégie selon type
        if config.strategy == CacheStrategy.READ_THROUGH:
            return await self._read_through(key, config, fetcher)
        else:
            # Fallback standard
            data = await fetcher()
            await self._set_to_cache(key, data, config)
            return data
    
    async def _check_refresh_ahead(
        self, 
        key: str, 
        config: CacheConfig, 
        fetcher: Callable
    ):
        """Vérification refresh proactif"""
        
        ttl_remaining = await self.redis.ttl(key)
        if ttl_remaining > 0:
            ttl_ratio = ttl_remaining / config.ttl
            
            # Si proche expiration, refresh en arrière-plan
            if ttl_ratio < config.refresh_threshold:
                task = asyncio.create_task(
                    self._background_refresh(key, config, fetcher)
                )
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)
    
    async def _background_refresh(
        self, 
        key: str, 
        config: CacheConfig, 
        fetcher: Callable
    ):
        """Refresh en arrière-plan"""
        try:
            fresh_data = await fetcher()
            await self._set_to_cache(key, fresh_data, config)
            logger.debug(f"Background refresh completed for {key}")
        except Exception as e:
            logger.error(f"Background refresh failed for {key}: {e}")
    
    async def set_with_strategy(
        self, 
        key: str, 
        data: Any, 
        cache_type: str = "default"
    ):
        """Écriture avec stratégie"""
        
        config = self.CACHE_CONFIGS.get(cache_type)
        if not config:
            return
        
        if config.strategy == CacheStrategy.WRITE_THROUGH:
            # Cache + DB simultané (implémentation dépendante du contexte)
            await self._set_to_cache(key, data, config)
        
        elif config.strategy == CacheStrategy.WRITE_BEHIND:
            # Cache immédiat, DB en arrière-plan
            await self._set_to_cache(key, data, config)
            # Note: DB update should be handled by caller in background
    
    async def _get_from_cache(self, key: str, config: CacheConfig) -> Any:
        """Récupération optimisée du cache"""
        
        raw_data = await self.redis.get(key)
        if not raw_data:
            return None
        
        if config.compress:
            # Décompression si nécessaire
            import gzip
            raw_data = gzip.decompress(raw_data)
        
        return json.loads(raw_data)
    
    async def _set_to_cache(self, key: str, data: Any, config: CacheConfig):
        """Écriture optimisée au cache"""
        
        serialized = json.dumps(data, default=str)
        
        if config.compress:
            import gzip
            serialized = gzip.compress(serialized.encode())
        
        await self.redis.setex(key, config.ttl, serialized)
```

---

### 3. Optimisation API et Async

```python
# src/wakedock/api/optimizations.py
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import aiohttp
from fastapi import BackgroundTasks

class APIOptimizer:
    """Optimisations performance API"""
    
    def __init__(self):
        self.connection_pool = aiohttp.TCPConnector(
            limit=100,           # Max connexions totales
            limit_per_host=20,   # Max par host
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
    
    @asynccontextmanager
    async def batch_operations(self):
        """Context manager pour opérations par batch"""
        operations = []
        
        try:
            yield operations
            
            # Exécuter toutes les opérations en parallèle
            if operations:
                await asyncio.gather(*operations, return_exceptions=True)
        finally:
            pass
    
    async def parallel_service_status(self, service_ids: List[str]) -> Dict[str, Any]:
        """Récupération statut services en parallèle"""
        
        async def get_service_status(service_id: str):
            try:
                # Simulation appel Docker API
                await asyncio.sleep(0.1)  # Simule latence réseau
                return {
                    "id": service_id, 
                    "status": "running", 
                    "cpu": 45.2,
                    "memory": 128.5
                }
            except Exception as e:
                return {"id": service_id, "error": str(e)}
        
        # Limiter concurrence pour éviter surcharge
        semaphore = asyncio.Semaphore(10)
        
        async def bounded_status(service_id: str):
            async with semaphore:
                return await get_service_status(service_id)
        
        # Exécuter en parallèle avec limite concurrence
        results = await asyncio.gather(
            *[bounded_status(sid) for sid in service_ids],
            return_exceptions=True
        )
        
        return {r["id"]: r for r in results if isinstance(r, dict)}

# Middleware compression response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

class PerformanceMiddleware:
    """Middleware performance pour FastAPI"""
    
    @staticmethod
    def setup_app(app):
        # Compression responses
        app.add_middleware(
            GZipMiddleware, 
            minimum_size=1000,  # Compresser si >1KB
            compresslevel=6     # Bon compromis vitesse/taille
        )
        
        # CORS optimisé
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # À restreindre en production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            max_age=3600  # Cache preflight 1h
        )

# Pagination efficace
class PaginationOptimizer:
    """Pagination optimisée pour grandes datasets"""
    
    @staticmethod
    async def cursor_paginate(
        query, 
        cursor_field: str = "id",
        limit: int = 50,
        cursor: Optional[Any] = None
    ):
        """Pagination basée curseur (plus efficace que OFFSET)"""
        
        if cursor:
            query = query.where(getattr(query.column_descriptions[0]['type'], cursor_field) > cursor)
        
        # +1 pour détecter s'il y a une page suivante
        results = await query.limit(limit + 1).all()
        
        has_next = len(results) > limit
        if has_next:
            results = results[:-1]
        
        next_cursor = getattr(results[-1], cursor_field) if results and has_next else None
        
        return {
            "data": results,
            "pagination": {
                "has_next": has_next,
                "next_cursor": next_cursor,
                "limit": limit
            }
        }

# Response streaming pour gros volumes
from fastapi.responses import StreamingResponse
import json

async def stream_large_dataset(data_generator):
    """Stream response pour éviter surcharge mémoire"""
    
    async def generate():
        yield "["
        first = True
        
        async for item in data_generator:
            if not first:
                yield ","
            yield json.dumps(item, default=str)
            first = False
            
        yield "]"
    
    return StreamingResponse(
        generate(), 
        media_type="application/json",
        headers={"Cache-Control": "no-cache"}
    )
```

---

## 🎨 OPTIMISATIONS FRONTEND

### 1. Lazy Loading et Code Splitting

```typescript
// src/lib/utils/lazy-loading.ts
import { onMount } from 'svelte';

/**
 * Lazy loading pour composants lourds
 */
export function createLazyComponent<T>(
  importFn: () => Promise<{ default: T }>,
  fallback?: any
) {
  let Component: T | null = null;
  let loading = true;
  let error: Error | null = null;

  return {
    component: Component,
    loading,
    error,
    
    async load() {
      try {
        loading = true;
        const module = await importFn();
        Component = module.default;
        loading = false;
        return Component;
      } catch (e) {
        error = e as Error;
        loading = false;
        throw e;
      }
    }
  };
}

// Route-based code splitting
// src/routes/services/+page.ts
export const load = async () => {
  // Import dynamique du composant lourd
  const { default: ServicesTable } = await import('$lib/components/ServicesTable.svelte');
  
  return {
    component: ServicesTable
  };
};
```

### 2. Virtual Scrolling pour Grandes Listes

```svelte
<!-- src/lib/components/VirtualList.svelte -->
<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  
  export let items: any[] = [];
  export let itemHeight: number = 50;
  export let containerHeight: number = 400;
  export let overscan: number = 5;
  
  let container: HTMLElement;
  let scrollTop = 0;
  
  $: visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  $: visibleEnd = Math.min(
    items.length, 
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );
  $: visibleItems = items.slice(visibleStart, visibleEnd);
  $: totalHeight = items.length * itemHeight;
  $: offsetY = visibleStart * itemHeight;
  
  function handleScroll(event: Event) {
    scrollTop = (event.target as HTMLElement).scrollTop;
  }
</script>

<div 
  class="virtual-list-container"
  style="height: {containerHeight}px"
  on:scroll={handleScroll}
  bind:this={container}
>
  <div 
    class="virtual-list-spacer"
    style="height: {totalHeight}px"
  >
    <div 
      class="virtual-list-items"
      style="transform: translateY({offsetY}px)"
    >
      {#each visibleItems as item, index (visibleStart + index)}
        <div 
          class="virtual-list-item"
          style="height: {itemHeight}px"
        >
          <slot {item} index={visibleStart + index} />
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .virtual-list-container {
    overflow-y: auto;
    position: relative;
  }
  
  .virtual-list-spacer {
    position: relative;
  }
  
  .virtual-list-items {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
  }
  
  .virtual-list-item {
    display: flex;
    align-items: center;
  }
</style>
```

### 3. Optimisation Bundle et Assets

```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  
  build: {
    // Optimisations build
    rollupOptions: {
      output: {
        // Code splitting par route
        manualChunks: {
          vendor: ['svelte', '@sveltejs/kit'],
          charts: ['chart.js', 'd3'],
          ui: ['@headlessui/tailwindcss']
        }
      }
    },
    
    // Compression assets
    terserOptions: {
      compress: {
        drop_console: true,    // Supprimer console.log en prod
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.debug']
      }
    }
  },
  
  optimizeDeps: {
    // Pre-bundling dépendances lourdes
    include: [
      'chart.js',
      'd3',
      'lodash-es'
    ]
  },
  
  server: {
    // HMR optimisé
    hmr: {
      overlay: false
    }
  }
});

// Optimisation images
// src/lib/utils/image-optimization.ts
export function optimizeImage(
  src: string, 
  width?: number, 
  quality: number = 80
): string {
  // En production, utiliser un service d'optimisation
  if (import.meta.env.PROD) {
    const params = new URLSearchParams();
    if (width) params.set('w', width.toString());
    params.set('q', quality.toString());
    
    return `/api/images/optimize?src=${encodeURIComponent(src)}&${params}`;
  }
  
  return src;
}

// Progressive image loading
export function createProgressiveImage(src: string, placeholder: string) {
  return {
    src: placeholder,
    loaded: false,
    
    load() {
      const img = new Image();
      img.onload = () => {
        this.src = src;
        this.loaded = true;
      };
      img.src = src;
    }
  };
}
```

---

## 🐳 OPTIMISATIONS DOCKER

### 1. Multi-stage Build Optimisé

```dockerfile
# Dockerfile optimisé pour WakeDock backend
FROM python:3.11-slim as base

# Variables build
ARG POETRY_VERSION=1.6.1
ARG PYTHONUNBUFFERED=1
ARG PYTHONDONTWRITEBYTECODE=1

# Optimisations système
RUN apt-get update && apt-get install -y \
    # Dépendances minimales uniquement
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Stage dependencies
FROM base as dependencies

# Installation Poetry
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# Configuration Poetry pour performance
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copier uniquement les fichiers de dépendances d'abord (cache Docker)
COPY pyproject.toml poetry.lock ./

# Installation dépendances avec cache
RUN poetry install --only=main --no-root && rm -rf $POETRY_CACHE_DIR

# Stage production
FROM base as production

# Copier l'environnement virtuel depuis dependencies
COPY --from=dependencies /app/.venv /app/.venv

# Configurer PATH
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copier le code applicatif
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Utilisateur non-root pour sécurité
RUN useradd --create-home --shell /bin/bash wakedock
USER wakedock

# Health check optimisé
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Commande optimisée
CMD ["uvicorn", "wakedock.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker"]
```

```dockerfile
# Dockerfile Frontend optimisé
FROM node:18-alpine as base

# Optimisations Alpine
RUN apk add --no-cache \
    tini \
    && npm config set registry https://registry.npmjs.org/

# Stage dependencies
FROM base as dependencies

WORKDIR /app

# Cache npm avec .npmrc optimisé
COPY .npmrc package*.json ./
RUN npm ci --only=production --ignore-scripts

# Stage build
FROM base as build

WORKDIR /app

# Copier deps depuis cache
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

# Build optimisé
ENV NODE_ENV=production
RUN npm run build

# Stage production
FROM nginx:alpine as production

# Configuration nginx optimisée
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Copier build depuis stage précédent
COPY --from=build /app/build /usr/share/nginx/html

# Compression gzip
RUN gzip -k -6 /usr/share/nginx/html/**/*.{js,css,html,svg}

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 2. Configuration Docker Compose Performance

```yaml
# docker-compose.override.yml - Optimisations performance
version: '3.8'

services:
  wakedock:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # Optimisations réseau
    networks:
      - wakedock-net
    
    # Logging optimisé
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
    
    # Variables optimisation
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - WEB_CONCURRENCY=4  # Workers auto-scaling
    
    # Health check adaptatif
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    # Optimisations PostgreSQL
    environment:
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
      -c work_mem=4MB
      -c min_wal_size=1GB
      -c max_wal_size=4GB
    
    volumes:
      - postgres_data:/var/lib/postgresql/data
      # Optimisation: tmpfs pour logs temporaires
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100M

  redis:
    # Configuration Redis optimisée
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
      --tcp-keepalive 60
      --timeout 300
    
    # Optimisation réseau
    sysctls:
      - net.core.somaxconn=65535

  caddy:
    # Optimisations Caddy
    environment:
      - CADDY_ADMIN=0.0.0.0:2019
    
    # Optimisation: cache statique
    volumes:
      - caddy_data:/data
      - caddy_config:/config
      - type: tmpfs
        target: /tmp/caddy_cache
        tmpfs:
          size: 100M

networks:
  wakedock-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/wakedock/data/postgres
  
  caddy_data:
    driver: local
  caddy_config:
    driver: local
```

---

## 📊 MONITORING PERFORMANCE

### 1. Métriques Performance

```python
# src/wakedock/monitoring/performance.py
import time
import psutil
import asyncio
from dataclasses import dataclass
from typing import Dict, List
from prometheus_client import Counter, Histogram, Gauge

@dataclass
class PerformanceMetrics:
    """Métriques performance système"""
    cpu_usage: float
    memory_usage: float
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_recv: int
    response_times: Dict[str, float]
    error_rates: Dict[str, float]

class PerformanceMonitor:
    """Monitoring performance en temps réel"""
    
    def __init__(self):
        # Métriques Prometheus
        self.request_duration = Histogram(
            'wakedock_request_duration_seconds',
            'Request duration',
            ['method', 'endpoint', 'status']
        )
        
        self.system_cpu = Gauge(
            'wakedock_system_cpu_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory = Gauge(
            'wakedock_system_memory_percent', 
            'System memory usage percentage'
        )
        
        self.database_connections = Gauge(
            'wakedock_database_connections_active',
            'Active database connections'
        )
        
        self.cache_hit_rate = Gauge(
            'wakedock_cache_hit_rate',
            'Cache hit rate percentage'
        )
    
    async def collect_system_metrics(self) -> PerformanceMetrics:
        """Collecte métriques système"""
        
        # CPU et mémoire
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disque I/O
        disk_io = psutil.disk_io_counters()
        
        # Réseau I/O  
        network_io = psutil.net_io_counters()
        
        # Mise à jour Prometheus
        self.system_cpu.set(cpu_percent)
        self.system_memory.set(memory.percent)
        
        return PerformanceMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_io_read=disk_io.read_bytes,
            disk_io_write=disk_io.write_bytes,
            network_io_sent=network_io.bytes_sent,
            network_io_recv=network_io.bytes_recv,
            response_times={},  # À remplir par middleware
            error_rates={}      # À remplir par middleware
        )
    
    async def analyze_performance_trends(self, hours: int = 24) -> Dict:
        """Analyse tendances performance"""
        
        # Récupérer données historiques depuis Prometheus/InfluxDB
        # (Implémentation dépendante du backend de métriques)
        
        return {
            "avg_response_time": 0.15,
            "p95_response_time": 0.45,
            "error_rate": 0.02,
            "trending": {
                "cpu": "stable",
                "memory": "increasing", 
                "response_time": "improving"
            },
            "recommendations": [
                "Consider scaling up memory",
                "Optimize database queries for /api/services endpoint"
            ]
        }

# Middleware monitoring automatique
from fastapi import Request, Response
import time

class PerformanceMiddleware:
    """Middleware monitoring performance automatique"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            status_code = 500
            raise
        
        finally:
            # Enregistrer métriques
            duration = time.time() - start_time
            
            self.monitor.request_duration.labels(
                method=request.method,
                endpoint=request.url.path,
                status=str(status_code)
            ).observe(duration)
        
        return response
```

### 2. Alerting Performance

```python
# src/wakedock/monitoring/alerts.py
from enum import Enum
from typing import List, Dict, Any
import asyncio

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"

class PerformanceAlert:
    """Alerte performance"""
    
    def __init__(
        self, 
        name: str,
        severity: AlertSeverity,
        threshold: float,
        metric_path: str,
        description: str
    ):
        self.name = name
        self.severity = severity
        self.threshold = threshold
        self.metric_path = metric_path
        self.description = description
        self.triggered = False

class AlertManager:
    """Gestionnaire alertes performance"""
    
    PERFORMANCE_ALERTS = [
        PerformanceAlert(
            name="high_response_time",
            severity=AlertSeverity.WARNING,
            threshold=1.0,  # 1 seconde
            metric_path="response_time.p95",
            description="Response time P95 exceeds 1 second"
        ),
        
        PerformanceAlert(
            name="high_cpu_usage",
            severity=AlertSeverity.CRITICAL,
            threshold=85.0,  # 85%
            metric_path="system.cpu_usage",
            description="CPU usage exceeds 85%"
        ),
        
        PerformanceAlert(
            name="high_memory_usage", 
            severity=AlertSeverity.WARNING,
            threshold=80.0,  # 80%
            metric_path="system.memory_usage",
            description="Memory usage exceeds 80%"
        ),
        
        PerformanceAlert(
            name="low_cache_hit_rate",
            severity=AlertSeverity.WARNING,
            threshold=70.0,  # 70% (inverted)
            metric_path="cache.hit_rate",
            description="Cache hit rate below 70%"
        )
    ]
    
    def __init__(self, notification_service):
        self.notifications = notification_service
        self.active_alerts = set()
    
    async def check_alerts(self, metrics: PerformanceMetrics):
        """Vérification alertes basée sur métriques"""
        
        current_values = {
            "response_time.p95": max(metrics.response_times.values()) if metrics.response_times else 0,
            "system.cpu_usage": metrics.cpu_usage,
            "system.memory_usage": metrics.memory_usage,
            "cache.hit_rate": 85.0  # À récupérer du cache Redis
        }
        
        for alert in self.PERFORMANCE_ALERTS:
            current_value = current_values.get(alert.metric_path, 0)
            
            # Logique seuil (inverted pour cache hit rate)
            if alert.name == "low_cache_hit_rate":
                exceeded = current_value < alert.threshold
            else:
                exceeded = current_value > alert.threshold
            
            if exceeded and alert.name not in self.active_alerts:
                # Nouvelle alerte
                await self._trigger_alert(alert, current_value)
                self.active_alerts.add(alert.name)
                
            elif not exceeded and alert.name in self.active_alerts:
                # Résolution alerte
                await self._resolve_alert(alert, current_value)
                self.active_alerts.discard(alert.name)
    
    async def _trigger_alert(self, alert: PerformanceAlert, value: float):
        """Déclencher alerte"""
        
        message = f"🚨 {alert.description}\n"
        message += f"Current value: {value:.2f}\n"
        message += f"Threshold: {alert.threshold}\n"
        message += f"Severity: {alert.severity.value.upper()}"
        
        await self.notifications.send_alert({
            "title": f"Performance Alert: {alert.name}",
            "message": message,
            "severity": alert.severity.value,
            "metric": alert.metric_path,
            "value": value,
            "threshold": alert.threshold
        })
    
    async def _resolve_alert(self, alert: PerformanceAlert, value: float):
        """Résoudre alerte"""
        
        message = f"✅ {alert.description} - RESOLVED\n"
        message += f"Current value: {value:.2f}"
        
        await self.notifications.send_alert({
            "title": f"Alert Resolved: {alert.name}",
            "message": message,
            "severity": "info",
            "resolved": True
        })
```

---

## 🚀 PLAN D'EXÉCUTION

### Phase 1 - Backend Core (Semaine 1)
- [ ] Optimisation requêtes base de données + index
- [ ] Cache Redis intelligent avec stratégies
- [ ] Pool connexions et async optimisé
- [ ] Monitoring métriques de base

### Phase 2 - Frontend Performance (Semaine 2)  
- [ ] Lazy loading et code splitting
- [ ] Virtual scrolling pour listes
- [ ] Optimisation bundle Vite
- [ ] Progressive image loading

### Phase 3 - Infrastructure (Semaine 2-3)
- [ ] Docker multi-stage optimisé
- [ ] Configuration nginx/caddy performance
- [ ] Optimisation volumes et réseau
- [ ] Health checks adaptatifs

### Phase 4 - Monitoring & Tuning (Semaine 3)
- [ ] Dashboard monitoring complet
- [ ] Alerting automatique
- [ ] Load testing et benchmarks
- [ ] Optimisations fines basées données

---

## 📈 BENCHMARKS ET TARGETS

```yaml
Baseline Actuel (estimé):
  - API Response Time: 800ms P95
  - Database Query: 200ms P95
  - Page Load Time: 4.5s
  - Bundle Size: 2.8MB
  - Memory Usage: 1.2GB

Targets Post-Optimisation:
  - API Response Time: 200ms P95 (-75%)
  - Database Query: 50ms P95 (-75%)
  - Page Load Time: 2.5s (-44%)
  - Bundle Size: 800KB (-71%)
  - Memory Usage: 512MB (-57%)

Outils Benchmarking:
  - Backend: ab, wrk, locust
  - Frontend: Lighthouse, WebPageTest
  - Database: pgbench, explain analyze
  - Infrastructure: docker stats, prometheus
```

---

**📞 Contact:** Performance Team  
**📅 Review:** Weekly performance reviews  
**🚨 Escalation:** DevOps Lead pour optimisations infrastructure critiques