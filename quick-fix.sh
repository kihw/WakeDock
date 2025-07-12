#!/bin/bash

echo "🚀 Correction Rapide - WakeDock Authentication Issues"
echo "=================================================="

# 1. Redémarrer les services avec logs
echo "1. 🔄 Redémarrage des services avec monitoring"
echo "=============================================="

cd /Docker/code/WakeDock

# Arrêter tout
echo "Arrêt des services..."
docker-compose down

# Nettoyer les volumes problématiques (optionnel)
echo "Nettoyage des caches..."
docker volume prune -f

# Redémarrer avec logs
echo "Redémarrage..."
docker-compose up -d

# Attendre que les services soient prêts
echo "Attente du démarrage complet..."
sleep 10

# 2. Vérifier l'état des services
echo ""
echo "2. ✅ Vérification de l'état des services"
echo "========================================"

echo "État des conteneurs:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Health checks:"
docker inspect wakedock-core --format='{{.State.Health.Status}}' 2>/dev/null || echo "❌ Core health unknown"
docker inspect wakedock-dashboard --format='{{.State.Health.Status}}' 2>/dev/null || echo "❌ Dashboard health unknown"

# 3. Test simple de connectivité
echo ""
echo "3. 🌐 Tests de connectivité basiques"
echo "=================================="

# Test health endpoint interne
echo "Test health interne:"
timeout 5 docker exec wakedock-core curl -f http://localhost:8000/api/v1/health 2>/dev/null && echo "✅ Core health OK" || echo "❌ Core health failed"

# Test via Caddy
echo "Test via Caddy (public):"
timeout 5 curl -f https://admin.mtool.ovh/api/v1/health 2>/dev/null && echo "✅ Public health OK" || echo "❌ Public health failed"

# 4. Créer un utilisateur admin si nécessaire
echo ""
echo "4. 👤 Création utilisateur admin"
echo "==============================="

# Essayer de créer l'admin
echo "Tentative de création de l'utilisateur admin..."
timeout 10 docker exec wakedock-core python /app/create_admin_user.py 2>/dev/null && echo "✅ Admin user created/exists" || echo "❌ Admin creation failed"

# 5. Test de login simple
echo ""
echo "5. 🔑 Test de login"
echo "=================="

echo "Test POST login:"
LOGIN_RESPONSE=$(timeout 10 curl -s -X POST "https://admin.mtool.ovh/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login successful!"
    echo "Response preview: $(echo "$LOGIN_RESPONSE" | head -c 100)..."
else
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
fi

# 6. Logs récents
echo ""
echo "6. 📋 Logs récents (dernières 10 lignes)"
echo "========================================"

echo "Core logs:"
docker logs wakedock-core --tail=10 2>/dev/null || echo "❌ Cannot get core logs"

echo ""
echo "Dashboard logs:"
docker logs wakedock-dashboard --tail=5 2>/dev/null || echo "❌ Cannot get dashboard logs"

echo ""
echo "Caddy logs:"
docker logs wakedock-caddy --tail=5 2>/dev/null || echo "❌ Cannot get caddy logs"

# 7. Instructions pour la suite
echo ""
echo "🎯 RÉSULTATS ET PROCHAINES ÉTAPES"
echo "================================="
echo "Temps: $(date)"
echo ""
echo "Si les tests ci-dessus échouent:"
echo "1. Vérifiez les logs complets: docker logs wakedock-core"
echo "2. Vérifiez la configuration de la base de données"
echo "3. Testez l'accès direct: docker exec -it wakedock-core bash"
echo "4. Consultez le dashboard à: https://admin.mtool.ovh"
echo ""
echo "Si les tests réussissent:"
echo "1. Le problème est probablement côté frontend"
echo "2. Vérifiez le Service Worker dans les DevTools"
echo "3. Consultez les erreurs JavaScript dans la console"
