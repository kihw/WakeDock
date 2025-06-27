#!/bin/bash
set -e

# Handle Docker socket permissions
if [ -S /var/run/docker.sock ]; then
    DOCKER_SOCK=/var/run/docker.sock
    DOCKER_GID=$(stat -c '%g' $DOCKER_SOCK)
    
    # Check if docker group exists with this GID
    if ! getent group $DOCKER_GID >/dev/null 2>&1; then
        # Create docker group with the correct GID
        groupadd -g $DOCKER_GID docker
    fi
    
    # Add wakedock user to docker group
    usermod -aG $(getent group $DOCKER_GID | cut -d: -f1) wakedock
    
    echo "✅ Docker socket permissions configured (GID: $DOCKER_GID)"
else
    echo "⚠️ Docker socket not found at /var/run/docker.sock"
fi

# Execute the main command
exec "$@"
