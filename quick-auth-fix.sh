#!/bin/bash

echo "🚀 Correction Rapide des Problèmes d'Authentification"
echo "=================================================="

cd /Docker/code/WakeDock

# 1. Copier le script corrigé dans le conteneur
echo "1. 📋 Mise à jour du script create_admin_user.py"
docker cp create_admin_user.py wakedock-core:/app/create_admin_user.py

# 2. Créer l'utilisateur admin avec le bon mot de passe
echo ""
echo "2. 👤 Création de l'utilisateur admin"
docker exec wakedock-core python /app/create_admin_user.py

# 3. Test de login avec le bon mot de passe
echo ""
echo "3. 🔐 Test de login avec admin123"
LOGIN_RESPONSE=$(curl -s -X POST "https://admin.mtool.ovh/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -m 15 2>/dev/null)

echo "Response: $LOGIN_RESPONSE"

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login réussi avec admin123!"
    
    # Extraire le token
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "Token: ${TOKEN:0:30}..."
    
    # Test des APIs protégées
    echo ""
    echo "4. 🔒 Test des APIs protégées"
    
    echo "Test /auth/me:"
    ME_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "https://admin.mtool.ovh/api/v1/auth/me" -m 10)
    
    if echo "$ME_RESPONSE" | grep -q "username"; then
        echo "✅ /auth/me fonctionne"
        echo "User: $(echo "$ME_RESPONSE" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)"
    else
        echo "❌ /auth/me échoue: $ME_RESPONSE"
    fi
    
    echo ""
    echo "Test /services:"
    SERVICES_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "https://admin.mtool.ovh/api/v1/services" -m 10)
    
    if echo "$SERVICES_RESPONSE" | grep -q '\['; then
        echo "✅ /services accessible"
        echo "Services count: $(echo "$SERVICES_RESPONSE" | grep -o '\[.*\]' | grep -o ',' | wc -l)"
    else
        echo "❌ /services inaccessible: $SERVICES_RESPONSE"
    fi
    
    echo ""
    echo "Test /system/overview:"
    SYSTEM_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "https://admin.mtool.ovh/api/v1/system/overview" -m 10)
    
    if echo "$SYSTEM_RESPONSE" | grep -q '"cpu'; then
        echo "✅ /system/overview accessible"
    else
        echo "❌ /system/overview inaccessible: $SYSTEM_RESPONSE"
    fi
    
else
    echo "❌ Login échoué avec admin123"
    
    # Test avec admin au cas où
    echo ""
    echo "Tentative avec admin/admin:"
    LOGIN_RESPONSE2=$(curl -s -X POST "https://admin.mtool.ovh/api/v1/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "admin"}' \
      -m 15 2>/dev/null)
    
    if echo "$LOGIN_RESPONSE2" | grep -q "access_token"; then
        echo "✅ Login réussi avec admin/admin"
    else
        echo "❌ Login échoué aussi avec admin/admin"
        echo "Response: $LOGIN_RESPONSE2"
    fi
fi

# 5. Vérification du frontend
echo ""
echo "5. 🌐 Instructions pour tester le frontend"
echo "========================================="
echo "1. Ouvrez https://admin.mtool.ovh dans votre navigateur"
echo "2. Ouvrez les DevTools (F12)"
echo "3. Allez sur l'onglet Console"
echo "4. Tentez de vous connecter avec:"
echo "   - Username: admin"
echo "   - Password: admin123"
echo "5. Vérifiez qu'il n'y a plus d'erreur 'toFixed' dans la console"
echo "6. Vérifiez que les services et métriques s'affichent"

echo ""
echo "✅ Script de correction terminé - $(date)"
