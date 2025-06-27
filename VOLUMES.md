# WakeDock Volume and Permissions Troubleshooting

## Database Permission Issues

### Problem
When starting WakeDock with Docker, you might encounter errors like:
```
PermissionError: [Errno 13] Permission denied: '/app/data/.write_test'
sqlite3.OperationalError: unable to open database file
```

### Root Cause
This happens when Docker volume mounts have incorrect permissions. The WakeDock container runs as a non-root user (`wakedock`, UID 1000) for security, but the mounted host directories might be owned by root or have restrictive permissions.

### Solutions

#### Option 1: Use Named Volumes (Recommended for Development)
The default `docker-compose.yml` now uses Docker named volumes instead of bind mounts for the database. This allows Docker to manage permissions automatically.

**Pros:**
- No permission issues
- Automatic cleanup
- Better security

**Cons:**
- Data is stored inside Docker's volume storage
- Less direct access from host system

#### Option 2: Fix Host Directory Permissions (For Custom Deployments)
If you need to use bind mounts (host directories), ensure they have correct permissions:

**Linux/macOS:**
```bash
# Set ownership to UID 1000 (wakedock user in container)
sudo chown -R 1000:1000 /path/to/your/data/directory
# Or set permissions to be writable by all
sudo chmod -R 755 /path/to/your/data/directory
```

**Windows:**
```powershell
# Ensure the directory exists and is writable
# Windows Docker Desktop handles most permission issues automatically
```

#### Option 3: Use External Database (Production)
For production deployments, use the `docker-compose.prod.yml` which includes PostgreSQL:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Fallback Behavior
WakeDock includes automatic fallback behavior:

1. **First**, it tries to use the configured data directory (`/app/data`)
2. **If that fails** due to permissions, it falls back to `/tmp/wakedock/`
3. **If database initialization fails completely**, the application will still start but log warnings

**Note:** When using the fallback location (`/tmp/wakedock/`), data will be lost when the container restarts.

### Verification
To verify your setup is working correctly:

1. Check the container logs for any permission warnings
2. Look for messages like "Using fallback database path"
3. Test database functionality through the web interface

### Environment Variables
You can override the database location using environment variables:

```bash
# Use a custom database URL
DATABASE_URL=sqlite:///custom/path/wakedock.db

# Or modify the data path
WAKEDOCK_DATA_PATH=/custom/data/path
```

## Volume Configuration Summary

### Development (docker-compose.yml)
- Uses **named volumes** for data storage
- Automatic permission handling
- Data persists but is managed by Docker

### Production (docker-compose.prod.yml)
- Uses **PostgreSQL** for the database
- Bind mounts for specific directories
- Requires proper host directory permissions

### Testing (docker-compose.test.yml)
- Uses temporary, in-memory storage
- No persistent data requirements
