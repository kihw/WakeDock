# WakeDock Documentation

WakeDock is a Docker orchestration platform with integrated Caddy reverse proxy and Svelte dashboard.

## Table of Contents

- [API Documentation](api.md)
- [Deployment Guide](deployment.md)  
- [Security Guide](security.md)
- [Troubleshooting](troubleshooting.md)

## Quick Start

See the main [QUICKSTART.md](../QUICKSTART.md) for initial setup instructions.

## Architecture Overview

WakeDock consists of:

- **Backend API**: FastAPI-based REST API for container management
- **Database**: SQLite/PostgreSQL for persistent data storage  
- **Reverse Proxy**: Caddy for automatic HTTPS and load balancing
- **Dashboard**: Svelte-based web interface
- **Container Runtime**: Docker for service orchestration

## Core Components

### API Server
The FastAPI backend provides REST endpoints for:
- Service management (CRUD operations)
- System monitoring and health checks
- User authentication and authorization
- Configuration management

### Database Layer
SQLAlchemy ORM with:
- Service definitions and metadata
- User accounts and permissions
- Audit logs and system events
- Configuration settings

### Caddy Integration
Dynamic reverse proxy configuration:
- Automatic service discovery
- SSL certificate management
- Load balancing and health checks
- Custom routing rules

### Web Dashboard
Svelte-based interface for:
- Service management
- System monitoring
- User administration
- Configuration editing

## Development

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## Support

For issues and questions:
- Check [Troubleshooting](troubleshooting.md)
- Review GitHub Issues
- Follow security reporting in [SECURITY.md](../SECURITY.md)
