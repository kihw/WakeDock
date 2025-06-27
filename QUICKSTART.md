# 🚀 Quick Start Guide

Get WakeDock up and running in minutes!

## Prerequisites

- Docker & Docker Compose
- Python 3.8+
- Node.js 18+
- A domain with wildcard DNS (*.yourdomain.com) or use localhost for testing

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/wakedock.git
cd wakedock
```

### 2. Run Setup Script

**Linux/macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

### 3. Configure WakeDock

Edit `config/config.yml`:

```yaml
wakedock:
  domain: "yourdomain.com"  # Change this to your domain
  admin_password: "your-secure-password"  # Change this!

services:
  - name: "nextcloud"
    subdomain: "cloud"
    docker_image: "nextcloud:latest"
    ports: ["8080:80"]
    auto_shutdown:
      inactive_minutes: 30
```

### 4. Start WakeDock

```bash
docker-compose up -d
```

### 5. Access Dashboard

Open your browser and go to:
- `http://admin.localhost` (for local testing)
- `http://admin.yourdomain.com` (with your domain)

## Adding Your First Service

### Via Web Interface (Recommended)

1. Go to the admin dashboard
2. Click "Add Service"
3. Fill in the service details:
   - **Name**: `my-app`
   - **Subdomain**: `app`
   - **Docker Image**: `nginx:latest`
   - **Ports**: `8080:80`
4. Click "Save & Deploy"

### Via Configuration File

Add to `config/config.yml`:

```yaml
services:
  - name: "my-app"
    subdomain: "app"
    docker_image: "nginx:latest"
    ports: ["8080:80"]
    auto_shutdown:
      inactive_minutes: 15
      cpu_threshold: 5
      memory_threshold: 100
```

Then restart WakeDock:

```bash
docker-compose restart wakedock
```

## Testing Your Service

1. Visit `http://app.localhost` (or `http://app.yourdomain.com`)
2. WakeDock will show a loading page while starting the container
3. Once ready, you'll be redirected to your service
4. After 15 minutes of inactivity, the service will automatically stop

## Common Configuration Examples

### WordPress with MySQL

```yaml
services:
  - name: "wordpress"
    subdomain: "blog"
    docker_compose: "./services/wordpress/docker-compose.yml"
    auto_shutdown:
      inactive_minutes: 60
```

Create `services/wordpress/docker-compose.yml`:

```yaml
 
services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    environment:
      WORDPRESS_DB_HOST: db:3306
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
    depends_on:
      - db

  db:
    image: mysql:5.7
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: wordpress
      MYSQL_ROOT_PASSWORD: wordpress
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

### Simple Static Website

```yaml
services:
  - name: "portfolio"
    subdomain: "portfolio"
    docker_image: "nginx:alpine"
    ports: ["8080:80"]
    auto_shutdown:
      inactive_minutes: 30
```

### Development Environment

```yaml
services:
  - name: "dev-env"
    subdomain: "dev"
    docker_image: "code-server:latest"
    ports: ["8080:8080"]
    environment:
      PASSWORD: "your-password"
    auto_shutdown:
      inactive_minutes: 120  # 2 hours
```

## Monitoring & Management

### View Service Status

```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f wakedock

# View service-specific logs
docker logs wakedock-my-app
```

### API Access

```bash
# List services
curl http://admin.localhost:8000/api/v1/services

# Wake a service
curl -X POST http://admin.localhost:8000/api/v1/services/wakedock-my-app/wake

# Sleep a service
curl -X POST http://admin.localhost:8000/api/v1/services/wakedock-my-app/sleep
```

## Production Setup

### 1. Domain Configuration

Set up wildcard DNS for your domain:
```
*.yourdomain.com -> your-server-ip
```

### 2. HTTPS/SSL

WakeDock uses Caddy which automatically handles SSL certificates via Let's Encrypt.

Update your configuration:

```yaml
wakedock:
  domain: "yourdomain.com"
  
caddy:
  # Caddy will automatically request SSL certificates
```

### 3. Security

- Change default passwords
- Set up firewall rules
- Enable authentication for admin interface
- Use environment variables for secrets

### 4. Backup

Important directories to backup:
- `config/` - Configuration files
- `data/` - Application data
- `caddy/data/` - SSL certificates

## Troubleshooting

### Service Won't Start

1. Check logs: `docker-compose logs wakedock`
2. Verify Docker image exists
3. Check port conflicts
4. Ensure sufficient resources

### Can't Access Dashboard

1. Verify DNS resolution: `nslookup admin.yourdomain.com`
2. Check Caddy status: `docker-compose logs caddy`
3. Ensure ports 80/443 are open

### Service Stuck in "Starting" State

1. Check container logs: `docker logs wakedock-service-name`
2. Verify health check endpoints
3. Check resource constraints

### Auto-Shutdown Not Working

1. Verify monitoring is enabled in config
2. Check service access patterns
3. Adjust thresholds in auto_shutdown configuration

## Next Steps

- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Advanced Usage](docs/advanced.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/wakedock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/wakedock/discussions)
- **Documentation**: [docs.wakedock.dev](https://docs.wakedock.dev)
