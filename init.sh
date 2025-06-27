#!/bin/bash

# WakeDock Initialization Script
# Creates necessary directories and files for deployment

set -e

echo "🚀 Initializing WakeDock..."

# Source environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set defaults if not set
WAKEDOCK_DATA_DIR=${WAKEDOCK_DATA_DIR:-/Docker/config/wakedock}
CADDY_DATA_DIR=${CADDY_DATA_DIR:-${WAKEDOCK_DATA_DIR}/caddy-data}
CADDY_CONFIG_DIR=${CADDY_CONFIG_DIR:-${WAKEDOCK_DATA_DIR}/caddy-config}

echo "📁 Creating data directories..."

# Create directories
mkdir -p "${WAKEDOCK_DATA_DIR}"
mkdir -p "${CADDY_DATA_DIR}"
mkdir -p "${CADDY_CONFIG_DIR}"

# Set permissions
chmod 755 "${WAKEDOCK_DATA_DIR}"
chmod 755 "${CADDY_DATA_DIR}" 2>/dev/null || true
chmod 755 "${CADDY_CONFIG_DIR}" 2>/dev/null || true

echo "🌐 Creating Docker network..."
docker network create ${WAKEDOCK_NETWORK:-caddy_net} 2>/dev/null || echo "Network already exists"

echo "✅ WakeDock initialization complete!"
echo ""
echo "You can now run:"
echo "  docker-compose up -d"
