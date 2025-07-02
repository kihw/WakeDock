# WakeDock API Documentation

## Overview

The WakeDock API is a RESTful web service built with FastAPI that provides comprehensive Docker container management capabilities. The API follows REST principles and returns JSON responses.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

## Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Login Endpoint

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eUGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJ0eUGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "error": {
    "code": "CONTAINER_NOT_FOUND",
    "message": "Container with ID 'abc123' not found",
    "details": {
      "container_id": "abc123"
    }
  }
}
```

### Common Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## API Endpoints

### Health Check

#### Get API Health Status

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": "healthy",
    "docker": "healthy"
  }
}
```

### Authentication

#### User Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

#### User Logout

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

### Containers

#### List Containers

```http
GET /api/containers
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `all` (boolean) - Include stopped containers
- `status` (string) - Filter by status: running, stopped, paused
- `limit` (integer) - Maximum number of results
- `offset` (integer) - Pagination offset

**Response:**
```json
{
  "containers": [
    {
      "id": "abc123def456",
      "name": "my-container",
      "image": "nginx:latest",
      "status": "running",
      "state": "running",
      "created": "2024-01-15T10:30:00Z",
      "ports": [
        {
          "private_port": 80,
          "public_port": 8080,
          "type": "tcp"
        }
      ],
      "labels": {
        "com.docker.compose.service": "web"
      },
      "networks": ["bridge"],
      "mounts": [
        {
          "source": "/host/path",
          "destination": "/container/path",
          "mode": "rw"
        }
      ]
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### Get Container Details

```http
GET /api/containers/{container_id}
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "abc123def456",
  "name": "my-container",
  "image": "nginx:latest",
  "status": "running",
  "state": "running",
  "created": "2024-01-15T10:30:00Z",
  "started": "2024-01-15T10:31:00Z",
  "finished": null,
  "exit_code": null,
  "ports": [...],
  "environment": {
    "NODE_ENV": "production"
  },
  "labels": {...},
  "networks": [...],
  "mounts": [...],
  "stats": {
    "cpu_usage": 15.5,
    "memory_usage": 128000000,
    "memory_limit": 512000000,
    "network_rx": 1024,
    "network_tx": 2048
  }
}
```

#### Create Container

```http
POST /api/containers
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "my-new-container",
  "image": "nginx:latest",
  "ports": {
    "80/tcp": 8080
  },
  "environment": {
    "NODE_ENV": "production"
  },
  "volumes": {
    "/host/path": "/container/path"
  },
  "networks": ["custom-network"],
  "restart_policy": "unless-stopped",
  "labels": {
    "app": "web-server"
  }
}
```

**Response:**
```json
{
  "id": "new123container456",
  "name": "my-new-container",
  "status": "created",
  "message": "Container created successfully"
}
```

#### Start Container

```http
POST /api/containers/{container_id}/start
Authorization: Bearer <access_token>
```

#### Stop Container

```http
POST /api/containers/{container_id}/stop
Authorization: Bearer <access_token>
```

**Optional Body:**
```json
{
  "timeout": 10
}
```

#### Restart Container

```http
POST /api/containers/{container_id}/restart
Authorization: Bearer <access_token>
```

#### Remove Container

```http
DELETE /api/containers/{container_id}
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `force` (boolean) - Force removal of running container
- `volumes` (boolean) - Remove associated volumes

#### Get Container Logs

```http
GET /api/containers/{container_id}/logs
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `tail` (integer) - Number of lines from the end of logs
- `since` (string) - Show logs since timestamp/duration
- `follow` (boolean) - Follow log output
- `timestamps` (boolean) - Include timestamps

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "stream": "stdout",
      "message": "Server starting on port 80"
    }
  ]
}
```

#### Execute Command in Container

```http
POST /api/containers/{container_id}/exec
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "command": ["ls", "-la"],
  "working_dir": "/app",
  "user": "root",
  "environment": {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  }
}
```

**Response:**
```json
{
  "exit_code": 0,
  "stdout": "total 8\ndrwxr-xr-x 2 root root 4096 Jan 15 10:30 .\n",
  "stderr": ""
}
```

### Images

#### List Images

```http
GET /api/images
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `all` (boolean) - Include intermediate images
- `dangling` (boolean) - Only show dangling images

**Response:**
```json
{
  "images": [
    {
      "id": "sha256:abc123...",
      "tags": ["nginx:latest", "nginx:1.21"],
      "created": "2024-01-15T10:30:00Z",
      "size": 142000000,
      "virtual_size": 142000000,
      "containers": 2
    }
  ],
  "total": 1
}
```

#### Get Image Details

```http
GET /api/images/{image_id}
Authorization: Bearer <access_token>
```

#### Pull Image

```http
POST /api/images/pull
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "repository": "nginx",
  "tag": "latest",
  "auth": {
    "username": "docker-username",
    "password": "docker-password"
  }
}
```

#### Remove Image

```http
DELETE /api/images/{image_id}
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `force` (boolean) - Force removal
- `no_prune` (boolean) - Don't delete untagged parents

### Networks

#### List Networks

```http
GET /api/networks
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "networks": [
    {
      "id": "network123",
      "name": "bridge",
      "driver": "bridge",
      "scope": "local",
      "created": "2024-01-15T10:30:00Z",
      "containers": [
        {
          "id": "container123",
          "name": "my-container",
          "ip_address": "172.17.0.2"
        }
      ]
    }
  ]
}
```

#### Create Network

```http
POST /api/networks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "my-network",
  "driver": "bridge",
  "options": {
    "com.docker.network.bridge.enable_icc": "true"
  },
  "ipam": {
    "driver": "default",
    "config": [
      {
        "subnet": "172.20.0.0/16"
      }
    ]
  }
}
```

#### Remove Network

```http
DELETE /api/networks/{network_id}
Authorization: Bearer <access_token>
```

### Volumes

#### List Volumes

```http
GET /api/volumes
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "volumes": [
    {
      "name": "my-volume",
      "driver": "local",
      "created": "2024-01-15T10:30:00Z",
      "mount_point": "/var/lib/docker/volumes/my-volume/_data",
      "labels": {},
      "containers": ["container123"]
    }
  ]
}
```

#### Create Volume

```http
POST /api/volumes
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "my-new-volume",
  "driver": "local",
  "driver_opts": {},
  "labels": {
    "environment": "production"
  }
}
```

#### Remove Volume

```http
DELETE /api/volumes/{volume_name}
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `force` (boolean) - Force removal

### System Information

#### Get System Info

```http
GET /api/system/info
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "version": "20.10.17",
  "api_version": "1.41",
  "containers": 5,
  "containers_running": 3,
  "containers_paused": 0,
  "containers_stopped": 2,
  "images": 10,
  "storage_driver": "overlay2",
  "memory_total": 8589934592,
  "cpu_count": 4,
  "architecture": "x86_64",
  "operating_system": "Ubuntu 22.04.1 LTS"
}
```

#### Get System Events

```http
GET /api/system/events
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `since` (string) - Show events since timestamp
- `until` (string) - Show events until timestamp
- `filters` (string) - JSON encoded filters

### Statistics

#### Get Container Stats

```http
GET /api/containers/{container_id}/stats
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "container_id": "abc123",
  "name": "my-container",
  "cpu_usage": 15.5,
  "memory_usage": 128000000,
  "memory_limit": 512000000,
  "memory_percentage": 25.0,
  "network_rx": 1024,
  "network_tx": 2048,
  "block_read": 4096,
  "block_write": 8192,
  "pids": 10,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Get System Stats

```http
GET /api/system/stats
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "containers": {
    "total": 5,
    "running": 3,
    "stopped": 2
  },
  "images": {
    "total": 10,
    "size": 2000000000
  },
  "volumes": {
    "total": 3
  },
  "networks": {
    "total": 4
  },
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 2147483648,
    "memory_total": 8589934592,
    "disk_usage": 10737418240,
    "disk_total": 107374182400
  }
}
```

## WebSocket Events

The API provides real-time updates via WebSocket connections.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

### Event Types

#### Container Events

```json
{
  "type": "container",
  "action": "start",
  "container": {
    "id": "abc123",
    "name": "my-container",
    "status": "running"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### System Events

```json
{
  "type": "system",
  "action": "stats_update",
  "data": {
    "cpu_usage": 45.2,
    "memory_usage": 2147483648
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authenticated requests**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## Versioning

The API uses URL versioning:

- `v1`: Current stable version
- `v2`: Next version (when available)

Example: `/api/v1/containers`

## SDKs and Examples

### Python SDK

```python
from wakedock_client import WakeDockClient

client = WakeDockClient(
    base_url="http://localhost:8000",
    username="admin",
    password="password"
)

# List containers
containers = client.containers.list()

# Start container
client.containers.start("container_id")
```

### JavaScript SDK

```javascript
import { WakeDockClient } from 'wakedock-js-client';

const client = new WakeDockClient({
  baseURL: 'http://localhost:8000',
  username: 'admin',
  password: 'password'
});

// List containers
const containers = await client.containers.list();

// Start container
await client.containers.start('container_id');
```

### cURL Examples

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# List containers
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/containers

# Start container
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/containers/abc123/start
```

## OpenAPI Specification

The complete OpenAPI specification is available at:
- **Interactive docs**: http://localhost:8000/docs
- **JSON specification**: http://localhost:8000/openapi.json

## Support

For API support and questions:
- **Documentation**: [Development Guide](../development/SETUP.md)
- **Issues**: GitHub Issues
- **Discord**: Community chat
