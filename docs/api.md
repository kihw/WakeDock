# WakeDock API Documentation

## Overview

WakeDock provides a RESTful API for managing Docker containers and services through a centralized interface.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except health checks) require JWT authentication.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Services API

### List Services
```http
GET /services
```

Response:
```json
{
  "services": [
    {
      "id": "uuid",
      "name": "my-app",
      "image": "nginx:latest",
      "status": "running",
      "ports": ["80:8080"],
      "environment": {},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Service
```http
GET /services/{service_id}
```

### Create Service
```http
POST /services
Content-Type: application/json

{
  "name": "my-app",
  "image": "nginx:latest",
  "ports": ["80:8080"],
  "environment": {
    "ENV": "production"
  },
  "volumes": [
    "/host/path:/container/path"
  ],
  "networks": ["default"],
  "restart_policy": "unless-stopped",
  "labels": {
    "caddy": "my-app.example.com",
    "caddy.reverse_proxy": "{{upstreams 8080}}"
  }
}
```

### Update Service
```http
PUT /services/{service_id}
Content-Type: application/json

{
  "name": "my-app-updated",
  "image": "nginx:1.21",
  "ports": ["80:8080", "443:8443"]
}
```

### Delete Service
```http
DELETE /services/{service_id}
```

### Service Actions
```http
POST /services/{service_id}/start
POST /services/{service_id}/stop
POST /services/{service_id}/restart
POST /services/{service_id}/logs
```

## System API

### System Status
```http
GET /system/status
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "services_count": 5,
  "running_services": 4,
  "docker_version": "20.10.0",
  "caddy_status": "running"
}
```

### System Health
```http
GET /system/health
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "docker": "ok", 
    "caddy": "ok",
    "disk_space": "ok"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### System Metrics
```http
GET /system/metrics
```

Response:
```json
{
  "cpu_usage": 25.5,
  "memory_usage": 1024,
  "memory_total": 8192,
  "disk_usage": 2048,
  "disk_total": 10240,
  "network_rx": 1024,
  "network_tx": 512,
  "containers": {
    "total": 10,
    "running": 8,
    "stopped": 2
  }
}
```

## Users API (Admin Only)

### List Users
```http
GET /users
```

### Create User
```http
POST /users
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "role": "user"
}
```

### Update User
```http
PUT /users/{user_id}
```

### Delete User
```http
DELETE /users/{user_id}
```

## Configuration API

### Get Configuration
```http
GET /config
```

### Update Configuration
```http
PUT /config
Content-Type: application/json

{
  "caddy": {
    "admin_api": "localhost:2019",
    "config_file": "/etc/caddy/Caddyfile"
  },
  "docker": {
    "socket": "/var/run/docker.sock",
    "api_version": "auto"
  },
  "database": {
    "url": "sqlite:///wakedock.db"
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid service configuration",
    "details": {
      "field": "ports",
      "issue": "Invalid port mapping format"
    }
  }
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

API requests are rate limited:
- Authenticated users: 1000 requests/hour
- Unauthenticated: 100 requests/hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## WebSocket API

Real-time updates available via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.send(JSON.stringify({
  type: 'subscribe',
  topics: ['services', 'system']
}));
```

Events:
- `service.created`
- `service.updated`
- `service.deleted`
- `service.status_changed`
- `system.alert`

# API Documentation

*Documentation to be completed*
