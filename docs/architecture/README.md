# WakeDock Architecture

## Overview

WakeDock is a comprehensive Docker container management platform consisting of:

1. **Backend API Service** - Python FastAPI application
2. **Frontend Dashboard** - SvelteKit web application  
3. **Reverse Proxy** - Caddy web server
4. **Database** - SQLite (default) or PostgreSQL
5. **Monitoring** - Prometheus + Grafana (optional)

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │     Caddy       │    │   Dashboard     │
│                 │◄──►│  Reverse Proxy  │◄──►│   (SvelteKit)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  WakeDock API   │    │    Database     │
                       │   (FastAPI)     │◄──►│  (SQLite/PG)    │
                       └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │  Docker Engine  │
                       │   (Containers)  │
                       └─────────────────┘
```

## Component Details

### Backend API Service (`src/wakedock/`)

The core Python application built with:

- **FastAPI** - High-performance web framework
- **SQLAlchemy** - Database ORM
- **Docker SDK** - Container management
- **JWT Authentication** - Secure token-based auth
- **WebSocket Support** - Real-time updates

Key modules:
- `api/` - REST API endpoints
- `core/` - Business logic (orchestrator, monitoring)
- `database/` - Data models and database management
- `auth/` - Authentication and authorization
- `config/` - Configuration management

### Frontend Dashboard (`dashboard/`)

Modern web application built with:

- **SvelteKit** - Full-stack web framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool
- **Playwright** - End-to-end testing

Key features:
- Responsive design
- Real-time updates via WebSocket
- Accessibility compliant (WCAG 2.1)
- Progressive Web App (PWA) support

### Reverse Proxy (`caddy/`)

Caddy server provides:

- **Automatic HTTPS** - Let's Encrypt integration
- **Load Balancing** - Multi-instance support
- **Static File Serving** - Dashboard assets
- **API Proxying** - Backend route forwarding
- **Security Headers** - CORS, CSP, etc.

### Database Layer

Supports multiple database backends:

- **SQLite** (default) - File-based, zero-config
- **PostgreSQL** - Production-ready, scalable
- **MySQL/MariaDB** - Alternative SQL database

Features:
- **Alembic Migrations** - Schema versioning
- **Connection Pooling** - Performance optimization
- **Backup/Restore** - Data protection

## Security Architecture

### Authentication Flow

1. User login via web interface
2. Credentials validated against database
3. JWT tokens issued (access + refresh)
4. Tokens stored securely (httpOnly cookies)
5. API requests authenticated via JWT

### Authorization Levels

- **Admin** - Full system access
- **User** - Limited container management
- **Viewer** - Read-only access

### Security Features

- **CSRF Protection** - Token-based validation
- **Rate Limiting** - Prevent abuse
- **Input Validation** - Sanitize all inputs
- **Secure Headers** - HSTS, CSP, etc.
- **Audit Logging** - Track all actions

## Data Flow

### Container Management

1. User initiates action in dashboard
2. Dashboard sends API request to backend
3. Backend validates request + permissions
4. Backend interacts with Docker Engine
5. Real-time updates sent via WebSocket
6. Dashboard updates UI state

### Monitoring Data

1. Monitoring service collects metrics
2. Data stored in time-series database
3. Metrics exposed via API endpoints
4. Dashboard renders charts and graphs
5. Alerts triggered on thresholds

## Deployment Patterns

### Development

- Docker Compose with live reload
- Local file mounting for development
- Debug logging enabled
- Test database isolation

### Production

- Multi-stage Docker builds
- Separate service containers
- External database configuration
- Monitoring and logging setup

### High Availability

- Load balancer (Caddy/nginx)
- Multiple API instances
- Database clustering
- Shared storage volumes

## Configuration Management

### Environment Variables

- `WAKEDOCK_CONFIG_PATH` - Config file location
- `WAKEDOCK_DATA_PATH` - Data directory
- `WAKEDOCK_LOG_LEVEL` - Logging verbosity
- `JWT_SECRET_KEY` - Token signing key

### Config File Structure

```yaml
wakedock:
  data_path: "/app/data"
  host: "0.0.0.0"
  port: 8000

database:
  url: "sqlite:///wakedock.db"
  
logging:
  level: "INFO"
  file: "/app/logs/wakedock.log"

docker:
  socket_path: "/var/run/docker.sock"
  
security:
  jwt_secret: "your-secret-key"
  cors_origins: ["http://localhost:3000"]
```

## Performance Considerations

### Optimization Strategies

- **Database Indexing** - Query performance
- **Connection Pooling** - Resource efficiency
- **Response Caching** - Reduce API calls
- **Static Asset CDN** - Frontend performance
- **WebSocket Compression** - Reduce bandwidth

### Monitoring Metrics

- API response times
- Database query performance
- Container resource usage
- Memory and CPU utilization
- Error rates and logs

## Troubleshooting

### Common Issues

1. **Permission Errors** - Docker socket access
2. **Database Locks** - SQLite concurrent access
3. **Network Issues** - Container connectivity
4. **Certificate Errors** - HTTPS configuration

### Debug Tools

- Application logs (`/app/logs/`)
- Database query logs
- Docker daemon logs
- Network connectivity tests
- Health check endpoints

## Development Workflow

### Setup

1. Clone repository
2. Install dependencies
3. Configure environment
4. Run database migrations
5. Start development servers

### Testing

- Unit tests (pytest)
- Integration tests (API)
- End-to-end tests (Playwright)
- Performance testing (load tests)

### Deployment

1. Build Docker images
2. Push to registry
3. Update compose files
4. Deploy to production
5. Monitor health checks

## API Reference

See [API Documentation](../api/README.md) for detailed endpoint documentation.

## Contributing

See [Development Guide](../development/SETUP.md) for development setup and contribution guidelines.

## Plans

See [services and stacks integration plan](services_stacks_integration_plan.md) for the proposed fusion of services and stacks.

