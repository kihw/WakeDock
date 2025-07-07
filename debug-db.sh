#!/bin/bash

# WakeDock Database Debug Script
set -e

echo "🔍 WakeDock Database Debug Script"
echo "================================="

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Check if postgres service is running
echo "📊 Checking PostgreSQL service status..."
docker service ps wakedock_postgres || echo "❌ PostgreSQL service not found"

# Get postgres container ID
POSTGRES_CONTAINER=$(docker ps -q -f "name=wakedock_postgres")

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ PostgreSQL container not found or not running"
    exit 1
fi

echo "🐘 PostgreSQL container found: $POSTGRES_CONTAINER"

# Check if database exists and user can connect
echo "🔐 Testing database connection..."
docker exec -it $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();" || {
    echo "❌ Database connection failed"
    
    # Try to connect as superuser to check if user exists
    echo "🔧 Checking if user exists..."
    docker exec -it $POSTGRES_CONTAINER psql -U postgres -c "SELECT usename FROM pg_user WHERE usename = '$POSTGRES_USER';" || {
        echo "❌ Cannot connect to database at all"
        exit 1
    }
    
    # Check if database exists
    echo "🔧 Checking if database exists..."
    docker exec -it $POSTGRES_CONTAINER psql -U postgres -c "SELECT datname FROM pg_database WHERE datname = '$POSTGRES_DB';" || {
        echo "❌ Cannot query databases"
        exit 1
    }
    
    # Try to create user and database if they don't exist
    echo "🔧 Attempting to create user and database..."
    docker exec -it $POSTGRES_CONTAINER psql -U postgres -c "
        CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
        CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;
        GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    " || echo "⚠️  User or database may already exist"
}

# Check Redis connection
echo "📊 Checking Redis service status..."
docker service ps wakedock_redis || echo "❌ Redis service not found"

REDIS_CONTAINER=$(docker ps -q -f "name=wakedock_redis")

if [ -z "$REDIS_CONTAINER" ]; then
    echo "❌ Redis container not found or not running"
else
    echo "🔴 Redis container found: $REDIS_CONTAINER"
    echo "🔐 Testing Redis connection..."
    docker exec -it $REDIS_CONTAINER redis-cli -a $REDIS_PASSWORD ping || {
        echo "❌ Redis connection failed"
        echo "🔧 Checking Redis configuration..."
        docker exec -it $REDIS_CONTAINER redis-cli config get requirepass || echo "❌ Cannot get Redis config"
    }
fi

# Check WakeDock service
echo "📊 Checking WakeDock service status..."
docker service ps wakedock_wakedock || echo "❌ WakeDock service not found"

# Show recent logs
echo "📝 Recent service logs:"
echo "=== PostgreSQL Logs ==="
docker service logs wakedock_postgres --tail 20 || echo "❌ Cannot get PostgreSQL logs"

echo ""
echo "=== Redis Logs ==="
docker service logs wakedock_redis --tail 20 || echo "❌ Cannot get Redis logs"

echo ""
echo "=== WakeDock Logs ==="
docker service logs wakedock_wakedock --tail 20 || echo "❌ Cannot get WakeDock logs"

echo ""
echo "✅ Debug check completed!"
echo "💡 Common solutions:"
echo "  - If auth fails: docker stack rm wakedock && ./deploy-swarm.sh"
echo "  - If containers not found: docker stack deploy -c docker-swarm.yml wakedock"
echo "  - Check logs: docker service logs wakedock_<service> --follow"
