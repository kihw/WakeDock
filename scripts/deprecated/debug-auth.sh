#!/bin/bash

# WakeDock Authentication Debug Script
# Tests network connectivity and authentication from multiple sources

echo "=== WakeDock Authentication Debug Script ==="
echo "Date: $(date)"
echo "Testing authentication connectivity from multiple sources..."
echo ""

# Test 1: Container to Container (Internal network)
echo "🔍 Test 1: Container-to-container connectivity"
echo "Testing: wakedock-dashboard -> wakedock-core"
docker exec wakedock-dashboard curl -s -o /dev/null -w "%{http_code}" \
  http://wakedock-core:8000/api/v1/health
if [ $? -eq 0 ]; then
    echo "✅ Container-to-container: SUCCESS"
else
    echo "❌ Container-to-container: FAILED"
fi
echo ""

# Test 2: Container to External IP
echo "🔍 Test 2: Container to external IP"
echo "Testing: wakedock-dashboard -> 195.201.199.226:8000"
HTTP_CODE=$(docker exec wakedock-dashboard curl -s -o /dev/null -w "%{http_code}" \
  http://195.201.199.226:8000/api/v1/health)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ External IP connectivity: SUCCESS ($HTTP_CODE)"
else
    echo "❌ External IP connectivity: FAILED ($HTTP_CODE)"
fi
echo ""

# Test 3: Authentication endpoint (container)
echo "🔍 Test 3: Authentication endpoint test"
echo "Testing: wakedock-dashboard -> auth login"
AUTH_RESPONSE=$(docker exec wakedock-dashboard curl -s -X POST \
  http://195.201.199.226:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -w "%{http_code}")

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    echo "✅ Authentication API: SUCCESS"
    echo "   Token received: $(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 | cut -c1-20)..."
else
    echo "❌ Authentication API: FAILED"
    echo "   Response: $AUTH_RESPONSE"
fi
echo ""

# Test 4: CORS Headers Check
echo "🔍 Test 4: CORS Headers Analysis"
echo "Testing: CORS preflight request"
CORS_RESPONSE=$(curl -s -I -X OPTIONS \
  -H "Origin: http://195.201.199.226:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  http://195.201.199.226:8000/api/v1/auth/login)

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS Headers: Present"
    echo "   $(echo "$CORS_RESPONSE" | grep "Access-Control-Allow-Origin")"
else
    echo "❌ CORS Headers: Missing or blocked"
fi
echo ""

# Test 5: Dashboard container environment
echo "🔍 Test 5: Dashboard Environment Check"
echo "Environment variables:"
docker exec wakedock-dashboard env | grep -E "(API_URL|WAKEDOCK|NODE_ENV)" | head -5
echo ""

# Test 6: Network namespace check
echo "🔍 Test 6: Network Configuration"
echo "Dashboard container network:"
docker exec wakedock-dashboard ip route | head -3
echo ""
echo "Core container ports:"
docker exec wakedock-core netstat -ln | grep ":8000" | head -2
echo ""

# Test 7: Service discovery
echo "🔍 Test 7: Service Discovery"
echo "DNS resolution test:"
docker exec wakedock-dashboard nslookup wakedock-core 2>/dev/null || echo "nslookup not available"
docker exec wakedock-dashboard ping -c 1 wakedock-core >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Service discovery: SUCCESS (wakedock-core resolvable)"
else
    echo "❌ Service discovery: FAILED (wakedock-core not resolvable)"
fi
echo ""

# Summary
echo "=== DIAGNOSTIC SUMMARY ==="
echo "Based on the tests above:"
echo "1. If container-to-container works but browser fails -> CORS/Browser issue"
echo "2. If external IP works from container but not browser -> Network policy issue" 
echo "3. If authentication works from container but not browser -> Frontend configuration issue"
echo ""
echo "🔧 Recommended actions based on results:"
echo "- If CORS headers missing: Update CORS configuration in backend"
echo "- If network connectivity issues: Check Docker network configuration"  
echo "- If service discovery works: Consider using internal URLs in frontend"
echo ""
echo "=== END DIAGNOSTIC ==="
