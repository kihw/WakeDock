# WakeDock Dashboard Deployment Guide

This guide covers various deployment strategies for the WakeDock Dashboard, from development to production environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [CI/CD Setup](#cicd-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Quick Start

For a quick production deployment using Docker:

```bash
# Clone the repository
git clone https://github.com/your-org/wakedock.git
cd wakedock/dashboard

# Create environment configuration
cp .env.example .env
# Edit .env with your production values

# Build and start with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## Development Deployment

### Prerequisites

- Node.js 18+ and npm
- Running WakeDock API server
- Git

### Local Development

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Configure environment variables
export PUBLIC_API_URL=http://localhost:8000
export PUBLIC_WS_URL=ws://localhost:8000/ws

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Development with Docker

```bash
# Build development image
docker build -f Dockerfile.dev -t wakedock-dashboard:dev .

# Run development container
docker run -p 3000:3000 \
  -e PUBLIC_API_URL=http://host.docker.internal:8000 \
  -e PUBLIC_WS_URL=ws://host.docker.internal:8000/ws \
  -v $(pwd):/app \
  wakedock-dashboard:dev
```

## Production Deployment

### Option 1: Node.js Deployment

#### Build for Production

```bash
# Install dependencies
npm ci --only=production

# Build the application
npm run build

# Start the production server
npm start
```

#### Using PM2 (Recommended)

```bash
# Install PM2 globally
npm install -g pm2

# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save
pm2 startup
```

Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'wakedock-dashboard',
    script: 'build/index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      PUBLIC_API_URL: 'https://api.yourdomain.com',
      PUBLIC_WS_URL: 'wss://api.yourdomain.com/ws'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
}
```

### Option 2: Static Deployment

If you prefer static deployment (using adapter-static):

```bash
# Install static adapter
npm install -D @sveltejs/adapter-static

# Update svelte.config.js to use static adapter
# Build static files
npm run build

# Deploy the 'build' directory to your static hosting provider
```

## Docker Deployment

### Production Docker Image

```bash
# Build production image
docker build -f Dockerfile.prod -t wakedock-dashboard:latest .

# Run production container
docker run -d \
  --name wakedock-dashboard \
  -p 3000:3000 \
  -e PUBLIC_API_URL=https://api.yourdomain.com \
  -e PUBLIC_WS_URL=wss://api.yourdomain.com/ws \
  --restart unless-stopped \
  wakedock-dashboard:latest
```

### Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: wakedock-dashboard
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - PUBLIC_API_URL=https://api.yourdomain.com
      - PUBLIC_WS_URL=wss://api.yourdomain.com/ws
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`dashboard.yourdomain.com`)"
      - "traefik.http.routers.dashboard.tls=true"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"

networks:
  default:
    external:
      name: wakedock-network
```

### Multi-stage Production Build

The included `Dockerfile.prod` uses multi-stage builds for optimal image size:

```dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine as production
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=build --chown=nextjs:nodejs /app/build /app
COPY --from=build --chown=nextjs:nodejs /app/package.json /app/package.json
RUN npm ci --only=production && npm cache clean --force
USER nextjs
EXPOSE 3000
CMD ["node", "index.js"]
```

## Environment Configuration

### Required Environment Variables

```bash
# API Configuration
PUBLIC_API_URL=https://api.yourdomain.com
PUBLIC_WS_URL=wss://api.yourdomain.com/ws

# Optional Configuration
PUBLIC_API_TIMEOUT=30000
PUBLIC_SESSION_TIMEOUT=86400000
NODE_ENV=production
PORT=3000
```

### Production Environment Setup

1. **Create production environment file**:
   ```bash
   cp .env.example .env.production
   ```

2. **Configure production values**:
   ```bash
   # .env.production
   NODE_ENV=production
   PUBLIC_API_URL=https://api.yourdomain.com
   PUBLIC_WS_URL=wss://api.yourdomain.com/ws
   PUBLIC_ENABLE_DEBUG=false
   ```

3. **Secure sensitive values**:
   - Use secrets management (Azure Key Vault, AWS Secrets Manager, etc.)
   - Don't commit production secrets to version control
   - Use environment-specific configuration files

## CI/CD Setup

### GitHub Actions

The repository includes GitHub Actions workflows:

- **CI Pipeline** (`.github/workflows/ci.yml`): Runs tests, linting, and builds
- **Deployment Pipeline** (`.github/workflows/deploy.yml`): Handles deployments

#### Required Secrets

Configure these secrets in your GitHub repository:

```
DOCKER_USERNAME          # Docker Hub username
DOCKER_TOKEN            # Docker Hub access token
PRODUCTION_HOST         # Production server hostname
PRODUCTION_USER         # SSH username for production server
PRODUCTION_SSH_KEY      # SSH private key for deployment
PRODUCTION_API_URL      # Production API URL
STAGING_API_URL         # Staging API URL (optional)
SLACK_WEBHOOK_URL       # Slack notifications (optional)
```

### Manual Deployment

```bash
# Build and tag Docker image
docker build -f Dockerfile.prod -t wakedock-dashboard:v1.0.0 .

# Push to registry
docker push wakedock-dashboard:v1.0.0

# Deploy to production server
ssh user@production-server << 'EOF'
  docker pull wakedock-dashboard:v1.0.0
  docker stop wakedock-dashboard || true
  docker rm wakedock-dashboard || true
  docker run -d \
    --name wakedock-dashboard \
    -p 3000:3000 \
    -e PUBLIC_API_URL=https://api.yourdomain.com \
    --restart unless-stopped \
    wakedock-dashboard:v1.0.0
EOF
```

## Monitoring and Logging

### Health Checks

The dashboard includes a health check endpoint at `/health`:

```bash
curl -f http://localhost:3000/health
```

### Logging

Configure structured logging in production:

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'wakedock-dashboard',
    script: 'build/index.js',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    combine_logs: true,
    merge_logs: true
  }]
}
```

### Monitoring with Prometheus

Add Prometheus metrics endpoint:

```javascript
// In your production setup
const promClient = require('prom-client');
const register = new promClient.Registry();

// Add custom metrics
const httpDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status']
});

register.registerMetric(httpDuration);
```

## Load Balancing

### Nginx Configuration

```nginx
upstream wakedock_dashboard {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
    server 127.0.0.1:3002;
}

server {
    listen 80;
    server_name dashboard.yourdomain.com;
    
    location / {
        proxy_pass http://wakedock_dashboard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Traefik Configuration

```yaml
# traefik.yml
services:
  wakedock-dashboard:
    loadBalancer:
      servers:
        - url: "http://dashboard1:3000"
        - url: "http://dashboard2:3000"
        - url: "http://dashboard3:3000"
      healthCheck:
        path: /health
        interval: 30s
        timeout: 5s
```

## Security Considerations

### HTTPS/TLS

Always use HTTPS in production:

```bash
# With Let's Encrypt and Traefik
labels:
  - "traefik.http.routers.dashboard.tls=true"
  - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
```

### Content Security Policy

Add CSP headers:

```javascript
// In your reverse proxy or application
app.use((req, res, next) => {
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:;"
  );
  next();
});
```

### Environment Security

- Use secrets management systems
- Rotate authentication tokens regularly  
- Monitor access logs
- Keep dependencies updated
- Run security audits: `npm audit`

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check if port is available
netstat -tulpn | grep :3000

# Check application logs
docker logs wakedock-dashboard

# Verify environment variables
docker exec wakedock-dashboard env | grep PUBLIC_
```

#### 2. API Connection Issues

```bash
# Test API connectivity
curl -I https://api.yourdomain.com/health

# Check WebSocket connection
wscat -c wss://api.yourdomain.com/ws
```

#### 3. Build Failures

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### 4. Docker Issues

```bash
# Rebuild without cache
docker build --no-cache -f Dockerfile.prod -t wakedock-dashboard .

# Check container logs
docker logs -f wakedock-dashboard

# Debug container
docker exec -it wakedock-dashboard sh
```

### Performance Tuning

#### Node.js Optimization

```bash
# Increase memory limit
node --max-old-space-size=4096 build/index.js

# Enable cluster mode
export NODE_ENV=production
export WEB_CONCURRENCY=4  # Number of worker processes
```

#### Docker Optimization

```dockerfile
# Multi-stage build with optimizations
FROM node:18-alpine as build
# ... build stage

FROM node:18-alpine as production
# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init
# ... rest of production setup
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "index.js"]
```

### Monitoring Commands

```bash
# Check application health
curl -f http://localhost:3000/health

# Monitor resource usage
docker stats wakedock-dashboard

# Check application logs
docker logs -f --tail=100 wakedock-dashboard

# Monitor with htop/top
htop
```

## Support

For deployment issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review application logs
3. Check [GitHub Issues](https://github.com/your-org/wakedock/issues)
4. Contact support team

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and deployment contribution guidelines.