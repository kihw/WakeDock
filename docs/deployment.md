# WakeDock Deployment Guide

## Overview

This guide covers production deployment of WakeDock in various environments.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ storage
- Domain name (for HTTPS)

## Production Deployment

### 1. Quick Production Setup

```bash
# Clone repository
git clone https://github.com/your-org/wakedock.git
cd wakedock

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Environment Configuration

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://wakedock:password@db:5432/wakedock

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-admin-password

# Caddy
CADDY_ADMIN_API=localhost:2019
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com

# Docker
DOCKER_SOCKET=/var/run/docker.sock

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 3. Launch Production Stack

```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose -f docker-compose.prod.yml exec api python -m wakedock.database.cli init

# Create admin user
docker-compose -f docker-compose.prod.yml exec api python -m wakedock.database.cli create-user admin admin@example.com --admin
```

### 4. Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check API health
curl https://your-domain.com/api/v1/system/health

# Check dashboard
open https://your-domain.com
```

## Docker Compose Production

### Complete Production Stack

```yaml
 

services:
  api:
    image: wakedock:latest
    environment:
      - DATABASE_URL=postgresql://wakedock:${DB_PASSWORD}@db:5432/wakedock
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data:/app/data
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=wakedock
      - POSTGRES_USER=wakedock
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./caddy/Caddyfile.prod:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    environment:
      - DOMAIN=${DOMAIN}
      - EMAIL=${EMAIL}
    restart: unless-stopped

  dashboard:
    image: wakedock-dashboard:latest
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  caddy_data:
  caddy_config:
```

## Kubernetes Deployment

### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: wakedock
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wakedock-config
  namespace: wakedock
data:
  DATABASE_URL: "postgresql://wakedock:password@postgres:5432/wakedock"
  CADDY_ADMIN_API: "localhost:2019"
  DOMAIN: "your-domain.com"
```

### Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: wakedock-secrets
  namespace: wakedock
type: Opaque
stringData:
  SECRET_KEY: "your-super-secret-key"
  JWT_SECRET_KEY: "your-jwt-secret-key"
  DB_PASSWORD: "secure-db-password"
```

### Deployment
```yaml
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
      - name: api
        image: wakedock:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: wakedock-config
        - secretRef:
            name: wakedock-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'wakedock'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'

  - job_name: 'docker'
    static_configs:
      - targets: ['localhost:9323']
```

### Grafana Dashboard

Import dashboard from `examples/monitoring/grafana-dashboard.json`

## Security Hardening

### 1. Network Security

```bash
# Create dedicated network
docker network create wakedock-network

# Restrict external access
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

### 2. Container Security

```dockerfile
# Use non-root user
USER 1000:1000

# Read-only filesystem
--read-only --tmpfs /tmp

# Security options
--security-opt=no-new-privileges:true
--cap-drop=ALL
--cap-add=NET_BIND_SERVICE
```

### 3. Database Security

```env
# Strong passwords
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
JWT_SECRET_KEY=$(openssl rand -base64 64)

# SSL connections
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U wakedock wakedock > backup.sql

# Restore backup
docker-compose exec -T db psql -U wakedock wakedock < backup.sql
```

### Configuration Backup

```bash
# Backup configuration
tar -czf wakedock-config-$(date +%Y%m%d).tar.gz \
  .env \
  caddy/ \
  config/ \
  examples/
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### Load Balancing

```caddyfile
# Caddyfile
your-domain.com {
    reverse_proxy {
        to api:8000
        health_uri /health
        health_interval 30s
        health_timeout 5s
    }
}
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Test connection
   docker-compose exec api python -c "from wakedock.database import engine; print(engine.execute('SELECT 1').scalar())"
   ```

2. **Caddy Configuration Issues**
   ```bash
   # Validate Caddyfile
   docker-compose exec caddy caddy validate --config /etc/caddy/Caddyfile
   
   # Check Caddy logs
   docker-compose logs caddy
   ```

3. **Docker Socket Permissions**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   
   # Check socket permissions
   ls -la /var/run/docker.sock
   ```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_services_status ON services(status);
CREATE INDEX idx_services_created_at ON services(created_at);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

### Caching

```python
# Redis caching
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300
```

### Resource Limits

```yaml
# Recommended limits
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## Maintenance

### Regular Tasks

```bash
# Update containers
docker-compose pull
docker-compose up -d

# Clean up unused resources
docker system prune -f

# Backup database
./scripts/backup.sh

# Check logs
docker-compose logs --tail=100 -f
```

### Health Monitoring

```bash
# Setup health checks
./scripts/health-check.sh

# Monitor metrics
curl http://localhost:9090/metrics
```
