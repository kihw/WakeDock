#!/bin/bash

echo "🔐 Debug Spécifique - Authentification Token WakeDock"
echo "=================================================="

cd /Docker/code/WakeDock

# Test de login complet avec capture du token
echo "1. 🎯 Test Login et Capture Token"
echo "================================="

LOGIN_RESPONSE=$(curl -s -X POST "https://admin.mtool.ovh/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -w "STATUS_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" \
  -m 15)

echo "Login Response:"
echo "$LOGIN_RESPONSE"
echo ""

# Extraire le token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "✅ Token extrait: ${TOKEN:0:50}..."
    
    # Test 1: /auth/me
    echo ""
    echo "2. 🔒 Test /auth/me avec token"
    echo "============================="
    
    ME_RESPONSE=$(curl -s -X GET "https://admin.mtool.ovh/api/v1/auth/me" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/json" \
      -w "\nSTATUS_CODE:%{http_code}" \
      -m 10)
    
    echo "Me Response:"
    echo "$ME_RESPONSE"
    echo ""
    
    # Test 2: /services
    echo "3. 🛠️  Test /services avec token"
    echo "=============================="
    
    SERVICES_RESPONSE=$(curl -s -X GET "https://admin.mtool.ovh/api/v1/services" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/json" \
      -w "\nSTATUS_CODE:%{http_code}" \
      -m 10)
    
    echo "Services Response:"
    echo "$SERVICES_RESPONSE"
    echo ""
    
    # Test 3: /system/overview
    echo "4. 📊 Test /system/overview avec token"
    echo "====================================="
    
    SYSTEM_RESPONSE=$(curl -s -X GET "https://admin.mtool.ovh/api/v1/system/overview" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/json" \
      -w "\nSTATUS_CODE:%{http_code}" \
      -m 10)
    
    echo "System Overview Response:"
    echo "$SYSTEM_RESPONSE"
    echo ""
    
    # Test 4: Vérification du token avec debug
    echo "5. 🔍 Debug Token JWT"
    echo "===================="
    
    # Afficher les parties du JWT token
    IFS='.' read -ra PARTS <<< "$TOKEN"
    echo "Header (base64): ${PARTS[0]}"
    echo "Payload (base64): ${PARTS[1]}"
    echo "Signature: ${PARTS[2]:0:20}..."
    
    # Décoder le payload (si base64 est disponible)
    if command -v base64 >/dev/null 2>&1; then
        echo ""
        echo "Payload décodé:"
        echo "${PARTS[1]}" | base64 -d 2>/dev/null | jq . 2>/dev/null || echo "${PARTS[1]}" | base64 -d 2>/dev/null
    fi
    
else
    echo "❌ Aucun token trouvé dans la réponse"
    echo "Vérification du statut du login..."
    
    # Test avec admin/admin au cas où
    echo ""
    echo "Tentative avec admin/admin:"
    LOGIN_RESPONSE2=$(curl -s -X POST "https://admin.mtool.ovh/api/v1/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "admin"}' \
      -w "\nSTATUS_CODE:%{http_code}" \
      -m 15)
    
    echo "$LOGIN_RESPONSE2"
fi

# Test 5: Vérification des logs backend
echo ""
echo "6. 📋 Logs Backend Récents"
echo "=========================="

echo "Logs d'authentification:"
docker logs wakedock-core --tail=10 2>/dev/null | grep -i "auth\|login\|token" || echo "Aucun log d'auth récent"

echo ""
echo "Logs d'erreur récents:"
docker logs wakedock-core --tail=10 2>/dev/null | grep -i "error\|failed\|exception" || echo "Aucune erreur récente"

# Test 6: Recommandations
echo ""
echo "🎯 RECOMMANDATIONS"
echo "=================="

if [ -n "$TOKEN" ]; then
    echo "✅ Le login fonctionne et génère un token"
    echo "🔍 Vérifiez si les APIs protégées répondent avec le token"
    echo "📱 Dans le navigateur:"
    echo "   1. Ouvrez DevTools (F12)"
    echo "   2. Onglet Network"
    echo "   3. Tentez de vous connecter"
    echo "   4. Vérifiez les headers Authorization dans les requêtes"
    echo "   5. Regardez les réponses pour /auth/me, /services, etc."
else
    echo "❌ Le login échoue, vérifiez:"
    echo "   1. Les credentials (admin/admin123 ou admin/admin)"
    echo "   2. L'utilisateur existe dans la base de données"
    echo "   3. Les logs backend pour plus de détails"
fi

echo ""
echo "✅ Debug terminé - $(date)"
