#!/bin/bash

echo "Testing API endpoints..."

echo "1. Testing /api/v1/services:"
curl -s -o /dev/null -w "%{http_code}" http://wakedock:8000/api/v1/services || echo "CURL failed"

echo ""

echo "2. Testing /api/v1/system/overview:"
curl -s -o /dev/null -w "%{http_code}" http://wakedock:8000/api/v1/system/overview || echo "CURL failed"

echo ""

echo "3. Testing via Caddy proxy:"
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/services || echo "CURL failed"

echo ""

echo "4. Testing via Caddy proxy (system):"
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/system/overview || echo "CURL failed"

echo ""
echo "Done."
