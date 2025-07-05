# 🚀 GUIDE D'INTÉGRATION SÉCURITÉ - WakeDock

**Objectif**: Intégrer les services de sécurité implémentés dans l'application principale

---

## 📋 ÉTAPES D'INTÉGRATION

### 1. **Mise à jour des dépendances**

Ajouter dans `requirements.txt`:
```txt
PyJWT>=2.8.0
qrcode>=7.4.2
user-agents>=2.2.0
pyotp>=2.9.0
```

### 2. **Configuration dans `main.py`**

```python
# src/wakedock/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Imports des services de sécurité
from wakedock.security.manager import get_security_manager, initialize_security, shutdown_security
from wakedock.security.ids_middleware import IntrusionDetectionMiddleware
from wakedock.security.session_timeout import SessionTimeoutMiddleware, get_session_timeout_manager
from wakedock.api.middleware.rate_limiter import RateLimiterMiddleware

app = FastAPI(title="WakeDock API", version="1.0.0")

# Configuration sécurité
security_config = {
    "jwt_secret_key": "your-production-secret-key",  # À charger depuis env
    "security": {
        "environment": "production",
        "session": {
            "idle_timeout_minutes": 60,
            "max_concurrent_sessions": 5
        },
        "features": {
            "enable_mfa": True,
            "enable_intrusion_detection": True,
            "enable_api_rate_limiting": True
        }
    }
}

@app.on_event("startup")
async def startup_event():
    """Initialiser les services de sécurité au démarrage"""
    try:
        # Initialiser les services de sécurité
        security_services = await initialize_security(security_config)
        
        # Ajouter les middlewares de sécurité
        app.add_middleware(
            IntrusionDetectionMiddleware,
            ids=security_services.intrusion_detection_system
        )
        
        app.add_middleware(
            SessionTimeoutMiddleware,
            session_manager=security_services.session_timeout_manager
        )
        
        app.add_middleware(
            RateLimiterMiddleware,
            requests_per_minute=100
        )
        
        logger.info("Services de sécurité initialisés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la sécurité: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Arrêter les services de sécurité"""
    await shutdown_security()
```

### 3. **Mise à jour des routes d'authentification**

Le fichier `src/wakedock/api/auth/routes.py` est déjà mis à jour avec:
- JWT rotation automatique
- Endpoints de sécurité admin
- Gestion des sessions
- Statistiques de sécurité

### 4. **Configuration frontend (optionnel)**

Pour utiliser les nouvelles fonctionnalités côté client:

```javascript
// dashboard/src/lib/auth/security.js

// Gérer les avertissements de session timeout
export function handleSessionWarnings(response) {
  const timeoutWarning = response.headers.get('X-Session-Warning-Active');
  const warningMessage = response.headers.get('X-Session-Warning-Message');
  
  if (timeoutWarning === 'true' && warningMessage) {
    // Afficher une notification à l'utilisateur
    showSessionWarning(warningMessage);
  }
}

// Étendre la session automatiquement
export async function extendSession() {
  try {
    const response = await fetch('/auth/session/extend', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    if (response.ok) {
      console.log('Session étendue avec succès');
    }
  } catch (error) {
    console.error('Erreur lors de l\'extension de session:', error);
  }
}

// Rotation automatique des tokens
export async function checkTokenRotation() {
  const refreshToken = getRefreshToken();
  
  try {
    const response = await fetch('/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (response.ok) {
      const data = await response.json();
      
      if (data.rotated) {
        // Nouveaux tokens reçus
        setTokens(data.access_token, data.refresh_token);
        console.log('Tokens tournés automatiquement');
      }
    }
  } catch (error) {
    console.error('Erreur lors de la rotation des tokens:', error);
  }
}
```

---

## 🔧 CONFIGURATION PRODUCTION

### Variables d'environnement à définir:

```bash
# .env
JWT_SECRET_KEY=your-very-secure-secret-key-change-this
SECURITY_ENVIRONMENT=production
SESSION_TIMEOUT_MINUTES=60
MAX_CONCURRENT_SESSIONS=5
ENABLE_MFA=true
ENABLE_INTRUSION_DETECTION=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

### Configuration de base de données:

Les services utilisent les modèles existants. Si nécessaire, ajouter:

```sql
-- Optionnel: Table d'audit des tokens
CREATE TABLE IF NOT EXISTS token_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_token_expires TIMESTAMP WITH TIME ZONE,
    refresh_token_expires TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

---

## 📊 MONITORING ET TESTS

### Endpoints de monitoring:

```bash
# Statistiques de sécurité (admin requis)
GET /auth/security/statistics

# Événements de sécurité récents
GET /auth/security/events?limit=50

# Top menaces
GET /auth/security/threats

# Stats JWT rotation
GET /auth/jwt/rotation/stats

# Stats sessions
GET /auth/session/stats
```

### Tests d'intégration:

```bash
# Test des services de sécurité
python3 test_security_features.py

# Test de l'API d'authentification
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Test de la rotation JWT
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token"}'
```

---

## 🚨 POINTS D'ATTENTION

### Sécurité:
1. **Changer la clé secrète JWT** en production
2. **Configurer HTTPS** obligatoire
3. **Sauvegarder les clés** de récupération MFA
4. **Monitorer les logs** de sécurité

### Performance:
1. **Ajuster les seuils** de détection selon le trafic
2. **Configurer le nettoyage** automatique des données anciennes
3. **Monitorer la mémoire** utilisée par les caches

### Maintenance:
1. **Nettoyer régulièrement** les tokens révoqués
2. **Analyser les événements** de sécurité
3. **Mettre à jour les patterns** de détection

---

## ✅ CHECKLIST DE DÉPLOIEMENT

- [ ] Dépendances installées
- [ ] Configuration sécurité ajoutée à main.py
- [ ] Variables d'environnement définies
- [ ] Tests de sécurité passent
- [ ] Middlewares configurés
- [ ] Endpoints de monitoring testés
- [ ] Documentation à jour
- [ ] Monitoring des logs configuré
- [ ] Alertes de sécurité configurées
- [ ] Processus de sauvegarde MFA défini

---

## 🎯 PROCHAINES ÉTAPES

1. **Intégrer dans main.py** (30 min)
2. **Tester l'intégration** (1h)
3. **Configurer le monitoring** (30 min)
4. **Documentation utilisateur** (2h)
5. **Tests de charge** (1h)

**Total estimé**: 5 heures pour intégration complète

---

🎉 **Une fois intégré, WakeDock disposera d'un système de sécurité de niveau enterprise !**
