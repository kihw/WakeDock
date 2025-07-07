#!/bin/bash

# WakeDock Docker Swarm Deployment Script
set -e

echo "🚀 Starting WakeDock Docker Swarm deployment..."

# Load environment variables
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    set -a
    source .env
    set +a
else
    echo "⚠️  Warning: .env file not found. Using defaults."
fi

# Check if Docker is in swarm mode
if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
    echo "🔧 Initializing Docker Swarm..."
    docker swarm init
fi

# Create necessary networks
echo "🔗 Creating Docker networks..."
docker network create --driver overlay --attachable wakedock_wakedock_network || echo "Network already exists"

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p ./data/postgres
mkdir -p ./data/redis
mkdir -p ./data/caddy
mkdir -p ./data/caddy-config
mkdir -p ./data/caddy-volume
mkdir -p ./data/dashboard
mkdir -p ./data/wakedock-core
mkdir -p ./data/logs

# Set permissions
echo "🔐 Setting directory permissions..."
chmod 755 ./data/postgres
chmod 755 ./data/redis
chmod 755 ./data/caddy
chmod 755 ./data/caddy-config
chmod 755 ./data/caddy-volume

# Remove existing stack if it exists
echo "🗑️  Removing existing stack if present..."
docker stack rm wakedock || true

# Wait for stack to be fully removed
echo "⏳ Waiting for stack removal to complete..."
sleep 10

# Deploy the stack
echo "🚀 Deploying WakeDock stack..."
docker stack deploy -c docker-swarm.yml wakedock

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Service status:"
docker stack services wakedock

# Check service logs
echo "📝 Recent service logs:"
echo "=== PostgreSQL ==="
docker service logs wakedock_postgres --tail 10 || true

echo "=== Redis ==="
docker service logs wakedock_redis --tail 10 || true

echo "=== WakeDock ==="
docker service logs wakedock_wakedock --tail 10 || true

echo "✅ Deployment completed!"
echo "🌐 Services should be available at:"
echo "  - WakeDock API: http://localhost:${WAKEDOCK_CORE_PORT:-8000}"
echo "  - Dashboard: http://localhost:${CADDY_HTTP_PORT:-80}"
echo "  - Caddy Admin: http://localhost:${CADDY_ADMIN_PORT:-2019}"
echo ""
echo "To check logs: docker service logs wakedock_<service_name>"
echo "To scale services: docker service scale wakedock_<service_name>=<replicas>"
echo "To remove stack: docker stack rm wakedock"
