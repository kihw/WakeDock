#!/bin/bash

echo "Reloading Caddy configuration..."

# Method 1: API reload
echo "Trying API reload..."
curl -X POST http://localhost:2019/config/reload || echo "API reload failed"

# Method 2: Signal reload
echo "Trying signal reload..."
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile || echo "Signal reload failed"

echo "Done."
