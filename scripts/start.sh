#!/bin/bash
# Application startup script for WakeDock

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Default values
MODE="production"
CONFIG_FILE=""
SKIP_HEALTH_CHECK=false
INIT_DB=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            MODE="development"
            shift
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        --init-db)
            INIT_DB=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --dev, --development    Start in development mode"
            echo "  --config FILE          Use specific config file"
            echo "  --skip-health-check    Skip initial health checks"
            echo "  --init-db              Initialize database before starting"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log "Starting WakeDock in $MODE mode..."

# Set environment variables based on mode
if [ "$MODE" = "development" ]; then
    export WAKEDOCK_DEBUG=true
    export WAKEDOCK_LOG_LEVEL=DEBUG
    export AUTO_RELOAD=true
    log "Development mode enabled"
else
    export WAKEDOCK_DEBUG=false
    export WAKEDOCK_LOG_LEVEL=INFO
    export AUTO_RELOAD=false
    log "Production mode enabled"
fi

# Set config file if specified
if [ -n "$CONFIG_FILE" ]; then
    export WAKEDOCK_CONFIG_PATH="$CONFIG_FILE"
    log "Using config file: $CONFIG_FILE"
fi

# Create necessary directories
log "Creating necessary directories..."
mkdir -p data logs config backups

# Set proper permissions
chmod 755 data logs config backups

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    log "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
else
    warn ".env file not found. Using default configuration."
fi

# Validate required environment variables
REQUIRED_VARS=("WAKEDOCK_SECRET_KEY" "DATABASE_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        error "Required environment variable $var is not set"
        exit 1
    fi
done

# Database initialization
if [ "$INIT_DB" = true ]; then
    log "Initializing database..."
    python -m alembic upgrade head
    if [ $? -eq 0 ]; then
        success "Database initialized successfully"
    else
        error "Database initialization failed"
        exit 1
    fi
fi

# Health checks (unless skipped)
if [ "$SKIP_HEALTH_CHECK" = false ]; then
    log "Performing health checks..."
    
    # Check if Docker daemon is accessible
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            success "Docker daemon is accessible"
        else
            warn "Docker daemon is not accessible. Some features may not work."
        fi
    else
        warn "Docker is not installed. Docker management features will be disabled."
    fi
    
    # Check if Caddy is accessible (if configured)
    if [ -n "$CADDY_ADMIN_URL" ]; then
        if curl -s -f "$CADDY_ADMIN_URL/config" >/dev/null 2>&1; then
            success "Caddy is accessible"
        else
            warn "Caddy is not accessible at $CADDY_ADMIN_URL. Proxy features may not work."
        fi
    fi
    
    # Check database connectivity
    log "Testing database connection..."
    python -c "
import sys
import asyncio
from wakedock.database.database import test_connection

async def test():
    try:
        await test_connection()
        print('Database connection successful')
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        success "Database connection test passed"
    else
        error "Database connection test failed"
        exit 1
    fi
fi

# Start the application
log "Starting WakeDock application..."

if [ "$MODE" = "development" ]; then
    # Development mode with auto-reload
    exec uvicorn wakedock.main:app \
        --host "${WAKEDOCK_HOST:-0.0.0.0}" \
        --port "${WAKEDOCK_PORT:-8000}" \
        --reload \
        --reload-dir src \
        --log-level debug
else
    # Production mode
    exec uvicorn wakedock.main:app \
        --host "${WAKEDOCK_HOST:-0.0.0.0}" \
        --port "${WAKEDOCK_PORT:-8000}" \
        --workers "${WAKEDOCK_WORKERS:-4}" \
        --log-level "${WAKEDOCK_LOG_LEVEL:-info}" \
        --access-log \
        --proxy-headers \
        --forwarded-allow-ips "*"
fi
