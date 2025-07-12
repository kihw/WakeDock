#!/bin/bash

echo "🔍 Phase 1: Diagnostic Complet - WakeDock Authentication"
echo "========================================================"

# Variables d'environnement
DOMAIN="admin.mtool.ovh"
API_BASE="https://${DOMAIN}/api/v1"
CONFIG_URL="https://${DOMAIN}/api/config"

echo "📍 Configuration détectée:"
echo "  - Domaine: ${DOMAIN}"
echo "  - API Base: ${API_BASE}"
echo "  - Config URL: ${CONFIG_URL}"
echo ""

# Test 1: Connectivité de base
echo "1. 🌐 Test de connectivité de base"
echo "=================================="

echo "✓ Test ping vers ${DOMAIN}:"
ping -c 2 $DOMAIN 2>/dev/null | grep "time=" || echo "❌ Ping échoué"

echo "✓ Test résolution DNS:"
nslookup $DOMAIN | grep "Address:" || echo "❌ DNS échoué"

echo "✓ Test HTTPS handshake:"
curl -s -I https://$DOMAIN | head -1

echo ""

# Test 2: Endpoints publics
echo "2. 🔓 Test des endpoints publics"
echo "================================"

echo "✓ Test endpoint de configuration:"
CONFIG_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nCONTENT_TYPE:%{content_type}" $CONFIG_URL)
echo "$CONFIG_RESPONSE"
echo ""

echo "✓ Test endpoint de santé (si accessible):"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "${API_BASE}/health" 2>/dev/null)
echo "$HEALTH_RESPONSE"
echo ""

# Test 3: Test de login détaillé
echo "3. 🔑 Test de login détaillé"
echo "==========================="

# Préparer les données de login
LOGIN_DATA='{"username": "admin", "password": "admin"}'
echo "✓ Données de login préparées: $LOGIN_DATA"

# Test avec debug complet
echo "✓ Test POST login avec debug complet:"
LOGIN_RESULT=$(curl -v -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Origin: https://${DOMAIN}" \
  -H "User-Agent: WakeDock-Debug/1.0" \
  -d "$LOGIN_DATA" \
  --connect-timeout 10 \
  --max-time 30 \
  -w "\n===RESPONSE_INFO===\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}\nSIZE_DOWNLOAD:%{size_download}\n" \
  2>&1)

echo "$LOGIN_RESULT"
echo ""

# Test 4: Vérification des logs backend
echo "4. 📋 Logs backend pendant le test"
echo "=================================="

echo "✓ Logs récents du core:"
docker logs wakedock-core --tail=20 --since="1m"
echo ""

echo "✓ Logs récents du dashboard:"
docker logs wakedock-dashboard --tail=10 --since="1m"
echo ""

# Test 5: Test connectivité interne
echo "5. 🔗 Test connectivité interne"
echo "==============================="

echo "✓ Test dashboard -> core:"
docker exec wakedock-dashboard curl -s -f http://wakedock-core:8000/api/v1/health | head -1 || echo "❌ Connexion dashboard->core échouée"

echo "✓ Test core accessible depuis l'extérieur via Caddy:"
docker exec wakedock-caddy curl -s -f http://wakedock-core:8000/api/v1/health | head -1 || echo "❌ Connexion caddy->core échouée"

echo ""

# Test 6: Configuration environnement
echo "6. ⚙️  Configuration environnement"
echo "=================================="

echo "✓ Variables d'environnement dashboard:"
docker exec wakedock-dashboard env | grep -E "(VITE_|NODE_|API)" | sort

echo ""
echo "✓ Variables d'environnement core:"
docker exec wakedock-core env | grep -E "(DATABASE|REDIS|API|AUTH)" | sort || echo "Aucune variable trouvée"

echo ""

# Test 7: Test des endpoints spécifiques
echo "7. 🎯 Test des endpoints spécifiques"
echo "===================================="

echo "✓ Test endpoint debug auth (si existant):"
curl -s -X POST "${API_BASE}/auth/login_debug" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_DATA" | head -5 || echo "Endpoint debug non disponible"

echo ""
echo "✓ Test endpoint login brut:"
curl -s -X POST "${API_BASE}/auth/login_raw_debug" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_DATA" | head -5 || echo "Endpoint debug brut non disponible"

echo ""

# Résumé
echo "📊 RÉSUMÉ DU DIAGNOSTIC"
echo "======================"
echo "Temps d'exécution: $(date)"
echo "Tous les tests ci-dessus terminés."
echo ""
echo "👆 Analysez les résultats pour identifier:"
echo "  - Les codes HTTP retournés"
echo "  - Les messages d'erreur dans les logs"
echo "  - Les problèmes de connectivité réseau"
echo "  - Les erreurs de configuration"
echo ""
echo "🔧 Prochaines étapes suggérées:"
echo "  1. Vérifier la configuration de la base de données"
echo "  2. Valider les modèles de données d'authentification"
echo "  3. Examiner la configuration Caddy pour le routage"
echo "  4. Tester la création d'un utilisateur admin"
