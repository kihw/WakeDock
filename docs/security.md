# WakeDock Security Guide

## Overview

This guide covers security best practices, threat mitigation, and secure configuration for WakeDock deployments.

## Security Architecture

### Defense in Depth

1. **Network Security**: Firewalls, VPNs, network segmentation
2. **Application Security**: Authentication, authorization, input validation
3. **Container Security**: Image scanning, runtime protection
4. **Infrastructure Security**: Host hardening, access controls
5. **Data Security**: Encryption, backup security

## Authentication & Authorization

### JWT Token Security

```python
# Strong JWT configuration
JWT_SECRET_KEY = os.urandom(64).hex()  # 512-bit key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8  # Short expiration
JWT_REFRESH_ENABLED = True
```

### Password Security

```python
# Strong password requirements
MIN_PASSWORD_LENGTH = 12
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_NUMBERS = True
REQUIRE_SPECIAL_CHARS = True

# Secure hashing
BCRYPT_ROUNDS = 12  # Minimum 12 rounds
```

### Multi-Factor Authentication

```python
# Enable TOTP/HOTP
MFA_ENABLED = True
MFA_ISSUER = "WakeDock"
MFA_BACKUP_CODES = 8
```

### Role-Based Access Control

```python
# Define roles with minimal privileges
ROLES = {
    "viewer": ["services:read", "system:read"],
    "operator": ["services:*", "system:read"],
    "admin": ["*:*"]
}
```

## Input Validation & Sanitization

### API Input Validation

```python
from pydantic import BaseModel, validator
from typing import List, Dict, Optional
import re

class ServiceCreateRequest(BaseModel):
    name: str
    image: str
    ports: Optional[List[str]] = []
    environment: Optional[Dict[str, str]] = {}
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', v):
            raise ValueError('Invalid service name format')
        if len(v) > 64:
            raise ValueError('Service name too long')
        return v
    
    @validator('image')
    def validate_image(cls, v):
        # Allow only trusted registries
        allowed_registries = ['docker.io', 'gcr.io', 'ghcr.io']
        if not any(v.startswith(registry) for registry in allowed_registries):
            raise ValueError('Untrusted image registry')
        return v
    
    @validator('ports')
    def validate_ports(cls, v):
        for port in v:
            if not re.match(r'^\d+:\d+(/tcp|/udp)?$', port):
                raise ValueError('Invalid port mapping format')
        return v
```

### SQL Injection Prevention

```python
# Always use parameterized queries
from sqlalchemy.text import text

# Good - parameterized
query = text("SELECT * FROM services WHERE name = :name")
result = db.execute(query, name=service_name)

# Bad - string concatenation
# query = f"SELECT * FROM services WHERE name = '{service_name}'"
```

## Container Security

### Image Security

```dockerfile
# Use minimal base images
FROM python:3.11-alpine

# Create non-root user
RUN addgroup -g 1001 wakedock && \
    adduser -D -u 1001 -G wakedock wakedock

# Install security updates
RUN apk update && apk upgrade

# Use non-root user
USER wakedock:wakedock

# Set read-only filesystem
RUN mkdir -p /tmp && chown wakedock:wakedock /tmp
VOLUME /tmp
```

### Runtime Security

```yaml
# docker-compose security settings
 

services:
  api:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
    user: "1001:1001"
```

### Image Scanning

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build image
        run: docker build -t wakedock:test .
        
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'wakedock:test'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

## Network Security

### TLS/HTTPS Configuration

```caddyfile
# Caddyfile - Force HTTPS
{
    # Global options
    admin localhost:2019
    email admin@yourdomain.com
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    }
}

yourdomain.com {
    reverse_proxy api:8000 {
        # Health check
        health_uri /health
        health_interval 30s
        health_timeout 5s
        
        # Headers
        header_up Host {upstream_hostport}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
    
    # Dashboard
    handle /dashboard* {
        reverse_proxy dashboard:3000
    }
    
    # Security
    encode gzip
    
    # Rate limiting
    rate_limit {
        zone static_zone {
            key {remote_host}
            events 100
            window 1m
        }
    }
}
```

### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port from default)
sudo ufw allow 2222/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow specific IPs for API access
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Enable firewall
sudo ufw enable
```

### Docker Network Security

```yaml
# Isolated networks
 

networks:
  frontend:
    driver: bridge
    internal: false
  backend:
    driver: bridge
    internal: true

services:
  api:
    networks:
      - frontend
      - backend
    
  db:
    networks:
      - backend  # Database only accessible internally
```

## Secrets Management

### Environment Variables

```bash
# Use external secret management
export SECRET_KEY=$(vault kv get -field=secret_key secret/wakedock)
export JWT_SECRET_KEY=$(vault kv get -field=jwt_key secret/wakedock)
export DB_PASSWORD=$(vault kv get -field=db_password secret/wakedock)
```

### Docker Secrets

```yaml
# docker-compose with secrets
 

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true

services:
  api:
    secrets:
      - db_password
      - jwt_secret
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: wakedock-secrets
type: Opaque
data:
  secret-key: <base64-encoded-secret>
  jwt-secret: <base64-encoded-jwt-secret>
  db-password: <base64-encoded-password>
```

## Rate Limiting & DDoS Protection

### Application-Level Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/services")
@limiter.limit("100/minute")  # 100 requests per minute
async def list_services(request: Request):
    pass

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # Strict limit for auth
async def login(request: Request):
    pass
```

### Redis-Based Rate Limiting

```python
import redis
import time
from typing import Optional

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is within rate limit
        
        :param key: Unique identifier (IP, user ID, etc.)
        :param limit: Maximum requests allowed
        :param window: Time window in seconds
        """
        current_time = int(time.time())
        pipeline = self.redis.pipeline()
        
        # Remove expired entries
        pipeline.zremrangebyscore(key, 0, current_time - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipeline.expire(key, window)
        
        results = pipeline.execute()
        current_requests = results[1]
        
        return current_requests < limit
```

## Logging & Monitoring

### Security Event Logging

```python
import logging
from datetime import datetime
from typing import Dict, Any

# Configure security logger
security_logger = logging.getLogger('wakedock.security')
security_logger.setLevel(logging.INFO)

# JSON formatter for structured logging
import json

class SecurityFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'event': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'action'):
            log_data['action'] = record.action
            
        return json.dumps(log_data)

# Security events to log
def log_authentication_attempt(username: str, ip: str, success: bool):
    security_logger.info(
        f"Authentication attempt for user {username}",
        extra={
            'user_id': username,
            'ip_address': ip,
            'action': 'login_attempt',
            'success': success
        }
    )

def log_privilege_escalation_attempt(user_id: str, action: str, ip: str):
    security_logger.warning(
        f"Privilege escalation attempt by user {user_id}: {action}",
        extra={
            'user_id': user_id,
            'ip_address': ip,
            'action': 'privilege_escalation',
            'success': False
        }
    )
```

### Intrusion Detection

```python
# Anomaly detection
class SecurityMonitor:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def detect_brute_force(self, ip: str, threshold: int = 10, window: int = 300):
        """Detect brute force attacks"""
        key = f"failed_logins:{ip}"
        failed_attempts = self.redis.get(key) or 0
        
        if int(failed_attempts) >= threshold:
            self.block_ip(ip, duration=3600)  # Block for 1 hour
            security_logger.critical(
                f"Brute force attack detected from IP {ip}",
                extra={'ip_address': ip, 'action': 'brute_force_detected'}
            )
    
    def detect_unusual_activity(self, user_id: str, action: str):
        """Detect unusual user activity"""
        # Implementation for behavioral analysis
        pass
    
    def block_ip(self, ip: str, duration: int):
        """Block IP address"""
        self.redis.setex(f"blocked_ip:{ip}", duration, "1")
```

## Data Protection

### Database Encryption

```python
# Enable database encryption at rest
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"

# Column-level encryption for sensitive data
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### Backup Security

```bash
#!/bin/bash
# Secure backup script

# Encrypt backup
gpg --cipher-algo AES256 --compress-algo 1 --s2k-cipher-algo AES256 \
    --s2k-digest-algo SHA512 --s2k-mode 3 --s2k-count 65011712 \
    --force-mdc --encrypt --armor \
    --recipient backup@yourdomain.com \
    --output backup-$(date +%Y%m%d).sql.gpg \
    backup.sql

# Upload to secure storage
aws s3 cp backup-$(date +%Y%m%d).sql.gpg s3://secure-backups/ \
    --sse AES256 \
    --storage-class STANDARD_IA

# Remove local unencrypted backup
rm backup.sql
```

## Incident Response

### Security Incident Playbook

1. **Detection**: Monitor logs and alerts
2. **Containment**: Isolate affected systems
3. **Investigation**: Analyze attack vectors
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore services safely
6. **Lessons Learned**: Update security measures

### Emergency Procedures

```bash
#!/bin/bash
# Emergency security script

# Block all external traffic
sudo iptables -A INPUT -j DROP
sudo iptables -A OUTPUT -j DROP
sudo iptables -A FORWARD -j DROP

# Stop all services
docker-compose down

# Create forensic backup
dd if=/dev/sda of=/mnt/forensic/disk-image.dd bs=1M

# Notify security team
curl -X POST https://alerts.company.com/security \
  -H "Content-Type: application/json" \
  -d '{"alert": "security_incident", "severity": "critical", "host": "'$(hostname)'"}'
```

## Compliance

### GDPR Compliance

```python
# Data retention policy
DATA_RETENTION_DAYS = 365

# User data deletion
async def delete_user_data(user_id: str):
    """Delete all user data for GDPR compliance"""
    # Delete user record
    await db.execute("DELETE FROM users WHERE id = ?", user_id)
    
    # Delete audit logs
    await db.execute("DELETE FROM audit_logs WHERE user_id = ?", user_id)
    
    # Anonymize remaining references
    await db.execute(
        "UPDATE services SET created_by = 'deleted_user' WHERE created_by = ?",
        user_id
    )
```

### SOC 2 Compliance

- **Security**: Access controls, encryption, monitoring
- **Availability**: Uptime monitoring, redundancy, disaster recovery
- **Processing Integrity**: Input validation, error handling
- **Confidentiality**: Data classification, access restrictions
- **Privacy**: Data minimization, consent management

## Security Checklist

### Pre-Deployment

- [ ] Change all default passwords
- [ ] Enable TLS/HTTPS everywhere
- [ ] Configure firewalls and network segmentation
- [ ] Set up monitoring and alerting
- [ ] Implement rate limiting
- [ ] Enable audit logging
- [ ] Scan images for vulnerabilities
- [ ] Review IAM permissions
- [ ] Configure backup encryption
- [ ] Test disaster recovery procedures

### Regular Maintenance

- [ ] Update dependencies monthly
- [ ] Rotate secrets quarterly
- [ ] Review access logs weekly
- [ ] Scan for vulnerabilities weekly
- [ ] Test backups monthly
- [ ] Update security policies annually
- [ ] Conduct penetration testing annually
- [ ] Review incident response procedures quarterly

## Contact Information

### Security Team
- Email: security@yourdomain.com
- PGP Key: [Key ID and fingerprint]
- Emergency: +1-XXX-XXX-XXXX

### Vulnerability Disclosure
See [SECURITY.md](../SECURITY.md) for responsible disclosure guidelines.
