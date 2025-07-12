# WakeDock Deployment Guide

## Overview

This guide covers various deployment scenarios for WakeDock, from development environments to production setups with high availability and monitoring.

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- **Docker**: 20.10+ with Docker Compose v2
- **Memory**: 2GB+ RAM (4GB+ recommended)
- **Storage**: 10GB+ available disk space
- **Network**: HTTPS-capable domain (for production)

### Security Requirements

- **Firewall**: Configure appropriate ports
- **SSL Certificates**: Valid certificates for HTTPS
- **Secrets Management**: Secure storage for sensitive data
- **Backup Strategy**: Regular data backups

## Quick Deployment

### Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/wakedock.git
cd wakedock

# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Access dashboard
open http://localhost:3000
```

### Production Quick Start

```bash
# Clone and configure
git clone https://github.com/your-org/wakedock.git
cd wakedock

# Configure production environment
cp .env.example .env.prod
nano .env.prod

# Deploy production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Configuration

### Environment Variables

Create `.env` file with the following variables:

```bash
# Core Configuration
WAKEDOCK_VERSION=latest
WAKEDOCK_CORE_PORT=8000
WAKEDOCK_LOG_LEVEL=INFO
RESTART_POLICY=unless-stopped

# Dashboard Configuration
DASHBOARD_PORT=3000
DASHBOARD_DOMAIN=wakedock.yourdomain.com

# Database Configuration
DATABASE_URL=postgresql://wakedock:password@postgres:5432/wakedock
# Or for SQLite:
# DATABASE_URL=sqlite:///data/wakedock.db

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-here
CORS_ORIGINS=https://wakedock.yourdomain.com,https://dashboard.yourdomain.com

# Docker Configuration
DOCKER_SOCKET_PATH=/var/run/docker.sock

# Caddy Configuration
CADDY_DOMAIN=wakedock.yourdomain.com
CADDY_EMAIL=admin@yourdomain.com

# Monitoring (Optional)
ENABLE_MONITORING=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
```

### Config File Setup

Create `config/config.yml`:

```yaml
wakedock:
  host: 0.0.0.0
  port: 8000
  data_path: /app/data
  debug: false

database:
  url: ${DATABASE_URL}
  pool_size: 10
  max_overflow: 20

logging:
  level: ${WAKEDOCK_LOG_LEVEL}
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: /app/logs/wakedock.log

docker:
  socket_path: ${DOCKER_SOCKET_PATH}
  timeout: 60

security:
  jwt_secret: ${JWT_SECRET_KEY}
  cors_origins: ${CORS_ORIGINS}
  rate_limit_per_minute: 60

monitoring:
  enabled: ${ENABLE_MONITORING}
  prometheus_endpoint: /metrics
  health_check_interval: 30
```

## Production Deployment

### Standard Production Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create wakedock user
sudo useradd -m -s /bin/bash wakedock
sudo usermod -aG docker wakedock
```

#### 2. Application Deployment

```bash
# Switch to wakedock user
sudo su - wakedock

# Clone repository
git clone https://github.com/your-org/wakedock.git
cd wakedock

# Create directories
mkdir -p data logs config backups

# Configure environment
cp .env.example .env
nano .env

# Configure application
cp config/config.example.yml config/config.yml
nano config/config.yml

# Deploy production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 3. SSL Certificate Setup

```bash
# Using Caddy with automatic certificates
echo "wakedock.yourdomain.com {
    reverse_proxy wakedock:8000
    encode gzip
}

dashboard.yourdomain.com {
    reverse_proxy dashboard:3000
    encode gzip
}" > caddy/Caddyfile

# Restart Caddy
docker-compose restart caddy
```

### High Availability Setup

#### Load Balancer Configuration

```yaml
# docker-compose.ha.yml
 

services:
  # Multiple WakeDock instances
  wakedock-1:
    extends:
      file: docker-compose.yml
      service: wakedock
    container_name: wakedock-1

  wakedock-2:
    extends:
      file: docker-compose.yml
      service: wakedock
    container_name: wakedock-2

  # Load balancer
  nginx:
    image: nginx:alpine
    container_name: wakedock-lb
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - wakedock-1
      - wakedock-2
```

#### Database Clustering

```yaml
# PostgreSQL with replication
  postgres-primary:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: reppass
    volumes:
      - postgres_primary_data:/var/lib/postgresql/data

  postgres-replica:
    image: postgres:15
    environment:
      PGUSER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_MASTER_SERVICE: postgres-primary
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
```

## Container Orchestration

### Docker Swarm Deployment

#### 1. Initialize Swarm

```bash
# On manager node
docker swarm init --advertise-addr <manager-ip>

# On worker nodes (use token from manager)
docker swarm join --token <token> <manager-ip>:2377
```

#### 2. Deploy Stack

```yaml
# docker-stack.yml
 

services:
  wakedock:
    image: wakedock/api:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    networks:
      - wakedock
    secrets:
      - jwt_secret
    configs:
      - source: wakedock_config
        target: /app/config/config.yml

networks:
  wakedock:
    driver: overlay

secrets:
  jwt_secret:
    external: true

configs:
  wakedock_config:
    external: true
```

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml wakedock
```

### Kubernetes Deployment

#### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: wakedock
```

#### 2. ConfigMap and Secrets

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wakedock-config
  namespace: wakedock
data:
  config.yml: |
    wakedock:
      host: 0.0.0.0
      port: 8000
    database:
      url: postgresql://user:pass@postgres:5432/wakedock
---
apiVersion: v1
kind: Secret
metadata:
  name: wakedock-secrets
  namespace: wakedock
type: Opaque
data:
  jwt-secret: <base64-encoded-secret>
  db-password: <base64-encoded-password>
```

#### 3. Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wakedock-api
  namespace: wakedock
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wakedock-api
  template:
    metadata:
      labels:
        app: wakedock-api
    spec:
      containers:
      - name: wakedock
        image: wakedock/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: wakedock-secrets
              key: jwt-secret
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: docker-sock
          mountPath: /var/run/docker.sock
      volumes:
      - name: config
        configMap:
          name: wakedock-config
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
---
apiVersion: v1
kind: Service
metadata:
  name: wakedock-api-service
  namespace: wakedock
spec:
  selector:
    app: wakedock-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

## Monitoring and Observability

### Prometheus + Grafana Setup

```yaml
# monitoring/docker-compose.yml
 

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: wakedock-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    container_name: wakedock-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/var/lib/grafana/dashboards

volumes:
  prometheus_data:
  grafana_data:
```

### Application Metrics

```python
# In your WakeDock application
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('wakedock_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('wakedock_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

set -e

BACKUP_DIR="/opt/wakedock/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="wakedock_backup_${DATE}.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop services
docker-compose stop

# Backup database
docker-compose exec -T postgres pg_dump -U wakedock wakedock > "db_backup_${DATE}.sql"

# Backup configuration and data
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    config/ \
    data/ \
    "db_backup_${DATE}.sql" \
    docker-compose.yml \
    .env

# Restart services
docker-compose start

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "wakedock_backup_*.tar.gz" -mtime +30 -delete

# Cleanup database backup
rm "db_backup_${DATE}.sql"

echo "Backup completed: $BACKUP_FILE"
```

### Recovery Procedure

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
docker-compose down

# Extract backup
tar -xzf "$BACKUP_FILE"

# Restore database
docker-compose up -d postgres
sleep 10
cat db_backup_*.sql | docker-compose exec -T postgres psql -U wakedock wakedock

# Start all services
docker-compose up -d

echo "Restore completed from: $BACKUP_FILE"
```

## Security Hardening

### Firewall Configuration

```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow WakeDock ports (if needed)
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable
```

### Docker Security

```yaml
# docker-compose.security.yml
 

services:
  wakedock:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/tmp
    user: "1000:1000"
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
```

### SSL/TLS Configuration

```bash
# Generate strong SSL configuration
echo "ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;" > nginx/ssl.conf
```

## Performance Optimization

### Database Optimization

```yaml
# PostgreSQL performance tuning
environment:
  - POSTGRES_INITDB_ARGS=--data-checksums
  - POSTGRES_CONFIG=max_connections=200
  - POSTGRES_CONFIG=shared_buffers=256MB
  - POSTGRES_CONFIG=effective_cache_size=1GB
  - POSTGRES_CONFIG=work_mem=4MB
  - POSTGRES_CONFIG=maintenance_work_mem=64MB
```

### Application Optimization

```python
# Async database operations
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

# Connection pooling
@asynccontextmanager
async def get_db_session():
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Caching Strategy

```yaml
# Redis for caching
  redis:
    image: redis:alpine
    container_name: wakedock-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
```

## Troubleshooting

### Common Issues

#### Port Conflicts

```bash
# Check port usage
sudo netstat -tulpn | grep :8000

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:8000)
```

#### Docker Socket Permissions

```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
```

#### Database Connection Issues

```bash
# Check database logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U wakedock -d wakedock -c "SELECT version();"
```

### Health Checks

```bash
#!/bin/bash
# health-check.sh

# Check services
services=("wakedock" "dashboard" "caddy" "postgres")

for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
    fi
done

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
fi

# Check dashboard
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Dashboard is accessible"
else
    echo "❌ Dashboard is not accessible"
fi
```

## Maintenance

### Update Procedure

```bash
#!/bin/bash
# update.sh

# Backup before update
./backup.sh

# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate

# Run database migrations if needed
docker-compose exec wakedock python manage.py migrate

# Verify deployment
./health-check.sh
```

### Log Management

```bash
# Configure log rotation
echo "/opt/wakedock/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    copytruncate
}" | sudo tee /etc/logrotate.d/wakedock
```

For additional support, see:
- [Architecture Documentation](../architecture/README.md)
- [Development Guide](../development/SETUP.md)
- [API Reference](../api/README.md)
