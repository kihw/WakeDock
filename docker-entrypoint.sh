#!/bin/bash
set -e

# This script runs as root to handle Docker socket permissions
# then drops privileges to wakedock user

echo "🐳 WakeDock Docker Entrypoint"

# Handle Docker socket permissions
if [ -S /var/run/docker.sock ]; then
    DOCKER_SOCK=/var/run/docker.sock
    DOCKER_GID=$(stat -c '%g' $DOCKER_SOCK)
    
    echo "Docker socket found with GID: $DOCKER_GID"
    
    # Check if docker group exists with this GID
    if ! getent group $DOCKER_GID >/dev/null 2>&1; then
        # Create docker group with the correct GID
        echo "Creating docker group with GID $DOCKER_GID"
        groupadd -g $DOCKER_GID docker
    else
        echo "Group with GID $DOCKER_GID already exists"
    fi
    
    # Add wakedock user to docker group
    DOCKER_GROUP_NAME=$(getent group $DOCKER_GID | cut -d: -f1)
    echo "Adding wakedock user to group: $DOCKER_GROUP_NAME"
    usermod -aG $DOCKER_GROUP_NAME wakedock
    
    echo "✅ Docker socket permissions configured"
else
    echo "⚠️ Docker socket not found at /var/run/docker.sock"
    echo "   Docker features will not be available"
fi

# Handle Caddy config directory permissions if mounted
if [ -d /etc/caddy ]; then
    echo "Setting up Caddy config directory permissions..."
    chown -R wakedock:wakedock /etc/caddy
    chmod -R 755 /etc/caddy
    echo "✅ Caddy config directory permissions configured"
fi

echo "Switching to wakedock user and starting application..."

# Switch to wakedock user and execute the main command
exec gosu wakedock "$@"
