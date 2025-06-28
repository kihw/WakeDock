# WakeDock Configuration Guide

## Overview

WakeDock uses a layered configuration system supporting YAML, JSON, and environment variables. This guide covers all configuration options and best practices.

## Configuration Sources

Configuration is loaded in the following order (later sources override earlier ones):

1. Default values
2. Configuration files (`config/config.yml`, `config/config.json`)
3. Environment variables
4. Command-line arguments

## Configuration File Structure

### Basic Configuration (`config/config.yml`)

```yaml
# Application settings
app:
  name: "WakeDock"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 8000
  
# Database configuration
database:
  url: "postgresql://wakedock:password@localhost:5432/wakedock"
  pool_size: 10
  pool_timeout: 30
  echo: false
  
# Security settings
security:
  secret_key: "your-secret-key-here"
  jwt_secret_key: "your-jwt-secret-key-here"
  jwt_algorithm: "HS256"
  jwt_expiration: 3600  # seconds
  password_min_length: 8
  rate_limit:
    enabled: true
    requests_per_minute: 60
    burst_size: 100
    
# Docker configuration
docker:
  socket_path: "/var/run/docker.sock"
  api_version: "auto"
  timeout: 60
  cleanup_orphaned: true
  
# Caddy proxy settings
caddy:
  admin_endpoint: "http://localhost:2019"
  config_path: "/etc/caddy/Caddyfile"
  reload_timeout: 30
  health_check_interval: 60
  
# Logging configuration
logging:
  level: "INFO"
  format: "json"
  file: null  # Set to file path for file logging
  max_size: "100MB"
  backup_count: 5
  
# Monitoring settings
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_port: 8080
  collect_interval: 30
  retention_days: 30
  
# Services configuration
services:
  - name: "wordpress"
    subdomain: "blog"
    docker_image: "wordpress:latest"
    ports:
      - "80:80"
    environment:
      WORDPRESS_DB_HOST: "db"
      WORDPRESS_DB_NAME: "wordpress"
    auto_shutdown:
      enabled: true
      idle_timeout: 1800  # 30 minutes
    health_check:
      enabled: true
      path: "/"
      interval: 30
      timeout: 10
    loading_page:
      enabled: true
      template: "default"
      
# Plugin configuration
plugins:
  enabled: true
  paths:
    - "/app/plugins"
  auto_load: true
  
# Backup settings
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention_days: 30
  storage:
    type: "local"
    path: "/app/backups"
```

## Environment Variables

All configuration options can be overridden using environment variables with the `WAKEDOCK_` prefix:

### Application Settings
- `WAKEDOCK_APP_DEBUG` - Enable debug mode
- `WAKEDOCK_APP_HOST` - Bind host
- `WAKEDOCK_APP_PORT` - Bind port

### Database Settings
- `DATABASE_URL` - Database connection URL
- `WAKEDOCK_DATABASE_POOL_SIZE` - Connection pool size
- `WAKEDOCK_DATABASE_POOL_TIMEOUT` - Pool timeout

### Security Settings
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT signing key
- `WAKEDOCK_SECURITY_JWT_EXPIRATION` - JWT expiration time

### Docker Settings
- `DOCKER_HOST` - Docker daemon socket
- `WAKEDOCK_DOCKER_TIMEOUT` - Docker API timeout

### Caddy Settings
- `CADDY_ADMIN_ENDPOINT` - Caddy admin API URL
- `WAKEDOCK_CADDY_CONFIG_PATH` - Caddyfile path

## Configuration Validation

WakeDock validates configuration on startup. Use the CLI to validate configuration:

```bash
# Validate current configuration
wakedock config validate

# Validate specific file
wakedock config validate --config-file config/production.yml

# Show current configuration
wakedock config show
```

## Configuration Examples

### Development Configuration

```yaml
app:
  debug: true
  host: "localhost"
  port: 8000
  
database:
  url: "sqlite:///./wakedock.db"
  
logging:
  level: "DEBUG"
  format: "text"
  
monitoring:
  enabled: false
```

### Production Configuration

```yaml
app:
  debug: false
  host: "0.0.0.0"
  port: 8000
  
database:
  url: "${DATABASE_URL}"
  pool_size: 20
  
security:
  secret_key: "${SECRET_KEY}"
  jwt_secret_key: "${JWT_SECRET_KEY}"
  rate_limit:
    enabled: true
    requests_per_minute: 100
    
logging:
  level: "INFO"
  format: "json"
  file: "/var/log/wakedock.log"
  
monitoring:
  enabled: true
  retention_days: 90
```

### High-Availability Configuration

```yaml
app:
  debug: false
  
database:
  url: "${DATABASE_URL}"
  pool_size: 50
  
security:
  rate_limit:
    enabled: true
    requests_per_minute: 200
    burst_size: 500
    
caddy:
  health_check_interval: 30
  
monitoring:
  enabled: true
  collect_interval: 15
  
backup:
  enabled: true
  schedule: "0 */6 * * *"  # Every 6 hours
  retention_days: 90
```

## Service Configuration

### Basic Service

```yaml
services:
  - name: "my-app"
    subdomain: "app"
    docker_image: "nginx:alpine"
    ports:
      - "80:80"
```

### Advanced Service with Docker Compose

```yaml
services:
  - name: "complex-app"
    subdomain: "complex"
    docker_compose: |
      version: '3.8'
      services:
        app:
          image: myapp:latest
          ports:
            - "3000:3000"
          environment:
            - NODE_ENV=production
        redis:
          image: redis:alpine
          ports:
            - "6379:6379"
    auto_shutdown:
      enabled: true
      idle_timeout: 3600
      check_interval: 300
    health_check:
      enabled: true
      path: "/health"
      interval: 30
      timeout: 10
      retries: 3
    loading_page:
      enabled: true
      template: "custom"
      message: "Starting Complex App..."
```

### Service with Environment Variables

```yaml
services:
  - name: "wordpress"
    subdomain: "blog"
    docker_image: "wordpress:latest"
    ports:
      - "80:80"
    environment:
      WORDPRESS_DB_HOST: "${DB_HOST}"
      WORDPRESS_DB_NAME: "${DB_NAME}"
      WORDPRESS_DB_USER: "${DB_USER}"
      WORDPRESS_DB_PASSWORD: "${DB_PASSWORD}"
    volumes:
      - "wordpress_data:/var/www/html"
```

## Configuration Templates

### Nginx Service

```yaml
services:
  - name: "static-site"
    subdomain: "www"
    docker_image: "nginx:alpine"
    ports:
      - "80:80"
    volumes:
      - "./html:/usr/share/nginx/html:ro"
    auto_shutdown:
      enabled: false  # Keep static sites running
```

### Node.js Application

```yaml
services:
  - name: "node-app"
    subdomain: "api"
    docker_image: "node:18-alpine"
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: "production"
      PORT: "3000"
    command: "npm start"
    health_check:
      enabled: true
      path: "/health"
      interval: 30
```

### Python Flask Application

```yaml
services:
  - name: "flask-app"
    subdomain: "python"
    docker_image: "python:3.11-slim"
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: "production"
      FLASK_APP: "app.py"
    command: "flask run --host=0.0.0.0"
```

## Security Configuration

### Basic Security

```yaml
security:
  secret_key: "generate-strong-secret-key"
  jwt_secret_key: "generate-strong-jwt-key"
  password_min_length: 12
  rate_limit:
    enabled: true
    requests_per_minute: 60
```

### Enhanced Security

```yaml
security:
  secret_key: "${SECRET_KEY}"
  jwt_secret_key: "${JWT_SECRET_KEY}"
  jwt_algorithm: "RS256"  # Use RSA instead of HMAC
  jwt_expiration: 900     # 15 minutes
  password_min_length: 12
  require_https: true
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst_size: 200
    per_user: true
  cors:
    allowed_origins: 
      - "https://your-domain.com"
    allow_credentials: true
```

## Monitoring Configuration

### Basic Monitoring

```yaml
monitoring:
  enabled: true
  metrics_port: 9090
  collect_interval: 60
```

### Advanced Monitoring

```yaml
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_port: 8080
  collect_interval: 30
  retention_days: 90
  exporters:
    prometheus:
      enabled: true
      port: 9090
    grafana:
      enabled: true
      datasource_url: "http://prometheus:9090"
  alerts:
    cpu_threshold: 80
    memory_threshold: 85
    disk_threshold: 90
```

## Best Practices

### 1. Use Environment Variables for Secrets

Never store secrets in configuration files:

```yaml
# Good
database:
  url: "${DATABASE_URL}"
  
# Bad
database:
  url: "postgresql://user:password@host/db"
```

### 2. Separate Configurations by Environment

Use different configuration files for different environments:

- `config/development.yml`
- `config/staging.yml`
- `config/production.yml`

### 3. Validate Configuration

Always validate configuration before deploying:

```bash
wakedock config validate --config-file config/production.yml
```

### 4. Use Configuration Management

For large deployments, use configuration management tools:

- Ansible
- Terraform
- Kubernetes ConfigMaps

### 5. Monitor Configuration Changes

Track configuration changes in version control and audit logs.

## Troubleshooting

### Configuration Not Loading

1. Check file permissions
2. Verify YAML/JSON syntax
3. Check environment variable names
4. Review logs for parsing errors

### Service Not Starting

1. Verify Docker image availability
2. Check port conflicts
3. Validate environment variables
4. Review service logs

### Caddy Not Reloading

1. Check Caddy admin API endpoint
2. Verify Caddyfile syntax
3. Check file permissions
4. Review Caddy logs

## Configuration Schema

WakeDock provides a JSON schema for configuration validation:

```bash
# Download schema
curl -o config.schema.json https://raw.githubusercontent.com/your-org/wakedock/main/config/config.schema.json

# Validate configuration
jsonschema -i config/config.yml config.schema.json
```

## Migration Guide

### From v1.0 to v1.1

Configuration changes:

1. `caddy.admin_url` → `caddy.admin_endpoint`
2. `services[].auto_sleep` → `services[].auto_shutdown`
3. Added `monitoring.retention_days`

### Migration Script

```bash
# Backup current configuration
cp config/config.yml config/config.yml.backup

# Run migration script
wakedock config migrate --from 1.0 --to 1.1
```
