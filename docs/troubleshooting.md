# WakeDock Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with WakeDock deployments.

## Quick Diagnostics

### Health Check Commands

```bash
# Check all services status
docker-compose ps

# Check API health
curl http://localhost:8000/api/v1/system/health

# Check Caddy status
curl http://localhost:2019/config/

# Check database connection
docker-compose exec api python -c "from wakedock.database import engine; print('DB OK' if engine.execute('SELECT 1').scalar() == 1 else 'DB FAIL')"

# Check Docker daemon
docker version
docker system info
```

### Log Collection

```bash
# Collect all logs
mkdir -p troubleshooting-$(date +%Y%m%d)
cd troubleshooting-$(date +%Y%m%d)

# API logs
docker-compose logs api > api.log

# Database logs  
docker-compose logs db > db.log

# Caddy logs
docker-compose logs caddy > caddy.log

# Dashboard logs
docker-compose logs dashboard > dashboard.log

# System logs
journalctl -u docker > docker-system.log
dmesg > kernel.log

# Package logs
tar -czf logs-$(date +%Y%m%d-%H%M%S).tar.gz *.log
```

## Common Issues

### 1. Service Won't Start

#### Symptoms
- Container exits immediately
- "Exited (1)" status in `docker-compose ps`
- Application logs show startup errors

#### Diagnosis
```bash
# Check container status
docker-compose ps

# View startup logs
docker-compose logs api

# Check resource usage
docker stats

# Inspect container
docker-compose exec api /bin/sh
```

#### Solutions

**Database Connection Issues**
```bash
# Check database status
docker-compose exec db pg_isready -U wakedock

# Test connection manually
docker-compose exec api python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://wakedock:password@db:5432/wakedock')
    print('Database connection OK')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

**Environment Variable Issues**
```bash
# Check environment variables
docker-compose exec api env | grep -E "(DATABASE_URL|SECRET_KEY|JWT_SECRET_KEY)"

# Validate .env file
cat .env | grep -v "^#" | grep -v "^$"
```

**Port Conflicts**
```bash
# Check port usage
netstat -tulpn | grep -E "(8000|5432|2019|3000)"

# Use different ports
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

### 2. Database Issues

#### Symptoms
- "Connection refused" errors
- "Database doesn't exist" errors
- Migration failures

#### Diagnosis
```bash
# Check database container
docker-compose exec db psql -U wakedock -d wakedock -c "SELECT version();"

# Check tables
docker-compose exec db psql -U wakedock -d wakedock -c "\dt"

# Check database size
docker-compose exec db psql -U wakedock -d wakedock -c "
SELECT 
    pg_size_pretty(pg_database_size('wakedock')) as db_size,
    pg_size_pretty(pg_total_relation_size('services')) as services_size;
"
```

#### Solutions

**Initialize Database**
```bash
# Run migrations
docker-compose exec api python -m wakedock.database.cli init

# Create tables manually
docker-compose exec db psql -U wakedock -d wakedock -f /app/migrations/001_initial.sql
```

**Reset Database**
```bash
# Backup first
docker-compose exec db pg_dump -U wakedock wakedock > backup.sql

# Reset
docker-compose down
docker volume rm wakedock_postgres_data
docker-compose up -d
docker-compose exec api python -m wakedock.database.cli init
```

**Performance Issues**
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Docker Issues

#### Symptoms
- "Cannot connect to Docker daemon"
- "Permission denied" when accessing Docker socket
- Containers not starting

#### Diagnosis
```bash
# Check Docker daemon
systemctl status docker

# Check Docker socket permissions
ls -la /var/run/docker.sock

# Check Docker version compatibility
docker version
docker-compose version
```

#### Solutions

**Permission Issues**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Fix socket permissions
sudo chmod 666 /var/run/docker.sock
```

**Docker Daemon Issues**
```bash
# Restart Docker daemon
sudo systemctl restart docker

# Check Docker configuration
sudo cat /etc/docker/daemon.json

# Clean up Docker resources
docker system prune -f
docker volume prune -f
```

**Resource Constraints**
```bash
# Check disk space
df -h
docker system df

# Check memory usage
free -h
docker stats

# Clean up unused resources
docker system prune -a -f
```

### 4. Caddy Issues

#### Symptoms
- SSL certificate errors
- Reverse proxy not working
- 502/503 errors

#### Diagnosis
```bash
# Check Caddy configuration
docker-compose exec caddy caddy validate --config /etc/caddy/Caddyfile

# Check Caddy admin API
curl http://localhost:2019/config/

# Check certificate status
curl -I https://yourdomain.com

# Check Caddy logs
docker-compose logs caddy | grep -E "(error|warn|fail)"
```

#### Solutions

**Configuration Issues**
```bash
# Validate Caddyfile syntax
docker-compose exec caddy caddy fmt --overwrite /etc/caddy/Caddyfile

# Reload configuration
curl -X POST http://localhost:2019/load \
  -H "Content-Type: application/json" \
  -d @caddy-config.json
```

**Certificate Issues**
```bash
# Check certificate directory
docker-compose exec caddy ls -la /data/caddy/certificates/

# Force certificate renewal
docker-compose exec caddy caddy trust

# Check DNS resolution
nslookup yourdomain.com
dig yourdomain.com
```

**Upstream Issues**
```bash
# Test backend connectivity
docker-compose exec caddy wget -O- http://api:8000/health

# Check service discovery
docker-compose exec caddy nslookup api
```

### 5. Dashboard Issues

#### Symptoms
- Dashboard not loading
- API calls failing
- Build errors

#### Diagnosis
```bash
# Check dashboard container
docker-compose logs dashboard

# Check API connectivity from dashboard
docker-compose exec dashboard curl http://api:8000/api/v1/system/health

# Check build process
docker-compose exec dashboard npm run build
```

#### Solutions

**Build Issues**
```bash
# Clear npm cache
docker-compose exec dashboard npm cache clean --force

# Rebuild node_modules
docker-compose exec dashboard rm -rf node_modules package-lock.json
docker-compose exec dashboard npm install

# Check TypeScript compilation
docker-compose exec dashboard npm run check
```

**API Connection Issues**
```bash
# Check API endpoint configuration
docker-compose exec dashboard cat src/lib/api.ts | grep baseURL

# Test API from dashboard container
docker-compose exec dashboard curl -v http://api:8000/api/v1/system/health
```

### 6. Performance Issues

#### Symptoms
- Slow response times
- High CPU/memory usage
- Timeouts

#### Diagnosis
```bash
# Monitor resource usage
docker stats

# Check system resources
htop
iotop
nethogs

# Profile application
docker-compose exec api python -m cProfile -o profile.out -m wakedock.main
```

#### Solutions

**Database Performance**
```sql
-- Add indexes
CREATE INDEX CONCURRENTLY idx_services_status ON services(status);
CREATE INDEX CONCURRENTLY idx_services_name ON services(name);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM services WHERE status = 'running';

-- Update statistics
ANALYZE;
```

**Application Performance**
```python
# Enable caching
REDIS_URL = "redis://redis:6379/0"
CACHE_TTL = 300

# Optimize queries
# Use select_related() and prefetch_related()
services = db.query(Service).options(joinedload(Service.containers)).all()
```

**System Performance**
```bash
# Increase limits
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
echo 'fs.file-max=65536' >> /etc/sysctl.conf
sysctl -p

# Optimize Docker
echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' > /etc/docker/daemon.json
systemctl restart docker
```

### 7. Network Issues

#### Symptoms
- Services can't communicate
- External access blocked
- DNS resolution failures

#### Diagnosis
```bash
# Check network configuration
docker network ls
docker-compose exec api cat /etc/hosts
docker-compose exec api nslookup db

# Test connectivity
docker-compose exec api ping db
docker-compose exec api telnet db 5432
docker-compose exec api curl http://caddy:80
```

#### Solutions

**Network Connectivity**
```bash
# Restart network
docker-compose down
docker network prune -f
docker-compose up -d

# Check firewall rules
sudo iptables -L
sudo ufw status
```

**DNS Issues**
```bash
# Check Docker DNS
docker-compose exec api cat /etc/resolv.conf

# Use custom DNS
echo "dns: 8.8.8.8" >> docker-compose.override.yml
```

### 8. Authentication Issues

#### Symptoms
- Login failures
- Token validation errors
- Permission denied

#### Diagnosis
```bash
# Check user creation
docker-compose exec api python -c "
from wakedock.database import get_session
from wakedock.auth.models import User
with get_session() as db:
    users = db.query(User).all()
    print(f'Users: {[u.username for u in users]}')
"

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

#### Solutions

**Create Admin User**
```bash
# Create admin user
docker-compose exec api python -m wakedock.database.cli create-user admin admin@example.com --admin

# Reset password
docker-compose exec api python -c "
from wakedock.database import get_session
from wakedock.auth.models import User
from wakedock.auth.password import hash_password
with get_session() as db:
    user = db.query(User).filter(User.username == 'admin').first()
    user.password_hash = hash_password('newpassword')
    db.commit()
"
```

**Token Issues**
```bash
# Check JWT configuration
docker-compose exec api python -c "
import os
print('JWT_SECRET_KEY:', os.getenv('JWT_SECRET_KEY', 'NOT SET'))
print('SECRET_KEY:', os.getenv('SECRET_KEY', 'NOT SET'))
"

# Generate new secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 64  # For SECRET_KEY
```

## Monitoring and Alerts

### Health Monitoring Script

```bash
#!/bin/bash
# health-monitor.sh

ALERT_EMAIL="admin@yourdomain.com"
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

check_service() {
    local service=$1
    local endpoint=$2
    
    if ! curl -sf "$endpoint" > /dev/null; then
        echo "ALERT: $service is down"
        
        # Send email alert
        echo "Service $service is not responding at $endpoint" | \
            mail -s "WakeDock Alert: $service Down" "$ALERT_EMAIL"
        
        # Send Slack notification
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"🚨 WakeDock Alert: $service is down at $endpoint\"}"
        
        return 1
    fi
    return 0
}

# Check services
check_service "API" "http://localhost:8000/health"
check_service "Dashboard" "http://localhost:3000"
check_service "Caddy" "http://localhost:2019/config/"

# Check database
if ! docker-compose exec -T db pg_isready -U wakedock > /dev/null 2>&1; then
    echo "ALERT: Database is down"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "ALERT: Disk usage is at ${DISK_USAGE}%"
fi
```

### Log Monitoring

```bash
#!/bin/bash
# log-monitor.sh

# Monitor error patterns
docker-compose logs --tail=100 api | grep -i error
docker-compose logs --tail=100 caddy | grep -i error
docker-compose logs --tail=100 db | grep -i error

# Monitor performance issues
docker-compose logs --tail=100 api | grep -E "(slow|timeout|memory)"

# Monitor security events
docker-compose logs --tail=100 api | grep -E "(failed.*login|unauthorized|blocked)"
```

## Getting Help

### Information to Collect

When reporting issues, please provide:

1. **System Information**
   ```bash
   uname -a
   docker version
   docker-compose version
   cat /etc/os-release
   ```

2. **WakeDock Configuration**
   ```bash
   cat docker-compose.yml
   cat .env (remove sensitive data)
   docker-compose config
   ```

3. **Logs**
   ```bash
   docker-compose logs --tail=50 api
   docker-compose logs --tail=50 db
   docker-compose logs --tail=50 caddy
   ```

4. **Resource Usage**
   ```bash
   docker stats --no-stream
   df -h
   free -h
   ```

### Support Channels

- **GitHub Issues**: https://github.com/your-org/wakedock/issues
- **Documentation**: https://wakedock.readthedocs.io/
- **Community Chat**: https://discord.gg/wakedock
- **Security Issues**: security@yourdomain.com

### Professional Support

For enterprise support, contact: support@yourdomain.com

Include:
- Detailed problem description
- Steps to reproduce
- Expected vs actual behavior
- System information and logs
- Business impact and urgency
