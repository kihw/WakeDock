#!/bin/sh
# WakeDock Caddy Configuration Script
# This script is called by WakeDock to setup initial Caddy configuration

CADDY_ADMIN_URL="${CADDY_ADMIN_URL:-http://caddy:2019}"

# Wait for Caddy to be available
echo "Waiting for Caddy admin API..."
while ! curl -s "$CADDY_ADMIN_URL/config/" > /dev/null 2>&1; do
    sleep 2
done

echo "Caddy is ready. Setting up initial configuration..."

# Initial configuration for WakeDock
INITIAL_CONFIG=$(cat <<EOF
{
  "apps": {
    "http": {
      "servers": {
        "main": {
          "listen": [":80"],
          "routes": [
            {
              "match": [{"path": ["/api/*"]}],
              "handle": [
                {
                  "handler": "reverse_proxy",
                  "upstreams": [{"dial": "wakedock:8000"}]
                }
              ]
            },
            {
              "match": [{"path": ["/*"]}],
              "handle": [
                {
                  "handler": "reverse_proxy",
                  "upstreams": [{"dial": "dashboard:3000"}]
                }
              ]
            }
          ]
        }
      }
    }
  }
}
EOF
)

# Apply configuration
curl -X POST "$CADDY_ADMIN_URL/config/" \
     -H "Content-Type: application/json" \
     -d "$INITIAL_CONFIG"

if [ $? -eq 0 ]; then
    echo "✅ Initial Caddy configuration applied successfully"
else
    echo "❌ Failed to apply Caddy configuration"
    exit 1
fi
