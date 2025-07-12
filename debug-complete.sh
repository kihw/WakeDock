#!/bin/bash

echo "🎯 PLAN DE DÉBOGAGE EXÉCUTABLE - WakeDock Authentication"
echo "======================================================="
echo "Date: $(date)"
echo ""

cd /Docker/code/WakeDock

# Phase 1: État initial et redémarrage
echo "📋 PHASE 1: DIAGNOSTIC ET REDÉMARRAGE"
echo "===================================="

echo "État initial des conteneurs:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep wakedock || echo "❌ Aucun conteneur WakeDock trouvé"

echo ""
echo "🔄 Redémarrage des services..."
docker-compose restart wakedock-core wakedock-dashboard wakedock-caddy

echo "⏳ Attente 15 secondes pour le démarrage..."
sleep 15

# Phase 2: Tests de connectivité
echo ""
echo "🌐 PHASE 2: TESTS DE CONNECTIVITÉ"
echo "================================="

echo "Test 1: Health check interne"
docker exec wakedock-core curl -f http://localhost:8000/api/v1/health 2>/dev/null | head -1 && echo "✅ Core health OK" || echo "❌ Core health failed"

echo ""
echo "Test 2: Health check via Caddy"
curl -f -m 10 https://admin.mtool.ovh/api/v1/health 2>/dev/null | head -1 && echo "✅ Public API OK" || echo "❌ Public API failed"

echo ""
echo "Test 3: Config endpoint"
curl -f -m 10 https://admin.mtool.ovh/api/config 2>/dev/null | head -1 && echo "✅ Config API OK" || echo "❌ Config API failed"

# Phase 3: Correction du cache
echo ""
echo "🛠️  PHASE 3: CORRECTION DU CACHE"
echo "==============================="

echo "Exécution du script de correction du cache..."
docker exec wakedock-core python /app/fix_cache.py 2>/dev/null || echo "❌ Script de correction du cache échoué"

# Phase 4: Test d'authentification
echo ""
echo "🔐 PHASE 4: TEST D'AUTHENTIFICATION"
echo "=================================="

echo "Test 1: Création/vérification utilisateur admin"
docker exec wakedock-core python /app/create_admin_user.py 2>/dev/null && echo "✅ Admin user OK" || echo "❌ Admin user failed"

echo ""
echo "Test 2: Login avec credentials admin"
LOGIN_RESPONSE=$(curl -s -X POST "https://admin.mtool.ovh/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -m 15 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login réussi!"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "Token reçu: ${TOKEN:0:20}..."
    
    # Test avec le token
    echo ""
    echo "Test 3: Utilisation du token pour /auth/me"
    ME_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "https://admin.mtool.ovh/api/v1/auth/me" -m 10 2>/dev/null)
    
    if echo "$ME_RESPONSE" | grep -q "username"; then
        echo "✅ Token fonctionnel - /auth/me OK"
    else
        echo "❌ Token non fonctionnel"
        echo "Response: $ME_RESPONSE"
    fi
    
    echo ""
    echo "Test 4: Test API services avec token"
    SERVICES_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "https://admin.mtool.ovh/api/v1/services" -m 10 2>/dev/null)
    
    if echo "$SERVICES_RESPONSE" | grep -q '\['; then
        echo "✅ API services accessible"
    else
        echo "❌ API services inaccessible"
        echo "Response: $SERVICES_RESPONSE"
    fi
    
else
    echo "❌ Login échoué"
    echo "Response: $LOGIN_RESPONSE"
fi

# Phase 5: Logs d'erreur
echo ""
echo "📋 PHASE 5: LOGS D'ERREUR"
echo "========================"

echo "Logs Core (dernières 10 lignes):"
docker logs wakedock-core --tail=10 2>/dev/null | tail -5

echo ""
echo "Logs Dashboard (dernières 5 lignes):"
docker logs wakedock-dashboard --tail=5 2>/dev/null

echo ""
echo "Logs Caddy (dernières 3 lignes):"
docker logs wakedock-caddy --tail=3 2>/dev/null

# Phase 6: Résumé et recommandations
echo ""
echo "🎯 PHASE 6: RÉSUMÉ ET RECOMMANDATIONS"
echo "===================================="

echo "✅ Services redémarrés"
echo "✅ Tests de connectivité effectués"
echo "✅ Correction du cache tentée"
echo "✅ Tests d'authentification effectués"
echo ""

echo "🔍 POUR DÉBOGUER LES PROBLÈMES FRONTEND:"
echo "1. Ouvrez les DevTools du navigateur (F12)"
echo "2. Aller dans l'onglet Console"
echo "3. Rafraîchir la page et observer les erreurs"
echo "4. Vérifier l'onglet Network pour les requêtes qui échouent"
echo "5. Vérifier l'onglet Application > Service Workers"

echo ""
echo "🛠️  COMMANDES UTILES POUR INVESTIGATION:"
echo "- docker logs wakedock-core -f    # Logs temps réel"
echo "- docker exec -it wakedock-core bash  # Shell dans le conteneur"
echo "- docker-compose restart          # Redémarrage complet"

echo ""
echo "📅 Diagnostic terminé: $(date)"
