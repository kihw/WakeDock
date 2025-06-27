#!/bin/bash

# WakeDock Quick Deploy Script for Docker Hosting Platforms (Dokploy, etc.)

set -e

echo "🐳 WakeDock Quick Deploy Starting..."

# Create network if it doesn't exist
NETWORK_NAME=${WAKEDOCK_NETWORK}
echo "Checking for Docker network: $NETWORK_NAME"

if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo "Creating Docker network: $NETWORK_NAME"
    docker network create "$NETWORK_NAME" || echo "Network might already exist, continuing..."
else
    echo "✅ Network $NETWORK_NAME exists"
fi

# Create data directories
echo "Creating data directories..."
mkdir -p "${WAKEDOCK_DATA_DIR}"
mkdir -p "${WAKEDOCK_CORE_DATA}"
mkdir -p "${WAKEDOCK_LOGS_DIR}"
mkdir -p "${WAKEDOCK_CONFIG_DIR}"
mkdir -p "${CADDY_DATA_DIR}"
mkdir -p "${CADDY_CONFIG_DIR}"
mkdir -p "${CADDY_CONFIG_VOLUME}"
mkdir -p "${DASHBOARD_DATA_DIR}"

# Setup initial Caddy configuration
echo "Setting up initial Caddy configuration..."
if [ ! -f "${CADDY_CONFIG_VOLUME}/Caddyfile" ]; then
    cp ./caddy/Caddyfile.auto "${CADDY_CONFIG_VOLUME}/Caddyfile"
    echo "✅ Initial Caddyfile created"
fi

echo "✅ Directories created"

# Load production environment if available
if [ -f ".env.production" ]; then
    echo "Loading production environment..."
    cp .env.production .env
fi

# Validate environment
if [ -z "$WAKEDOCK_NETWORK" ]; then
    export WAKEDOCK_NETWORK=caddy_net
fi

if [ -z "$WAKEDOCK_DOMAIN" ]; then
    export WAKEDOCK_DOMAIN=localhost
fi

echo "🚀 Starting WakeDock services..."
echo "Network: $WAKEDOCK_NETWORK"
echo "Domain: $WAKEDOCK_DOMAIN"

# Run docker-compose
docker-compose up -d --build

echo "✅ WakeDock deployed successfully!"
echo ""
echo "Services:"
echo "🌐 Dashboard: http://localhost:${DASHBOARD_PORT}"
echo "🔧 API: http://localhost:${WAKEDOCK_CORE_PORT}"
echo "⚙️ Caddy Admin: http://localhost:${CADDY_ADMIN_PORT}"
