# 🚨 CORRECTIONS CRITIQUES - WakeDock

**Priorité: 🔴 CRITIQUE**  
**Timeline: IMMÉDIAT (1-2 semaines)**  
**Équipe: Dev Lead + Senior Dev**

## 📋 Vue d'Ensemble

Ce document liste les corrections critiques identifiées suite au diagnostic de timeout de connexion et l'analyse complète du codebase. Ces issues doivent être résolues **IMMÉDIATEMENT** pour la stabilité et sécurité du système.

---

## 🔒 ISSUES DE SÉCURITÉ CRITIQUES

### 🚨 1. Logique 2FA Défaillante - **RÉSOLU PARTIELLEMENT**
**Fichier:** `dashboard/src/lib/stores/auth.ts:215`  
**Statut:** ⚠️ TEMPORAIREMENT DÉSACTIVÉ  

```typescript
// ❌ PROBLÈME ORIGINAL
requiresTwoFactor: !options?.twoFactorCode && emailOrUsername === 'admin@wakedock.com'

// ⚠️ FIX TEMPORAIRE ACTUEL  
requiresTwoFactor: !options?.twoFactorCode && (emailOrUsername === 'admin' && false)

// ✅ FIX DÉFINITIF À IMPLÉMENTER
requiresTwoFactor: response.user?.twoFactorEnabled || false
```

**Actions Requises:**
- [ ] Implémenter champ `twoFactorEnabled` dans User model
- [ ] Configurer TOTP/Authenticator support
- [ ] Tests de sécurité 2FA complets
- [ ] Documentation activation 2FA

---

### 🚨 2. Content Security Policy Inadéquate
**Fichier:** `dashboard/src/hooks.server.ts:61,73`  
**Statut:** ⚠️ FIX PARTIEL APPLIQUÉ

```typescript
// ❌ PROBLÈME: URL hardcodée localhost
const wakedockApiUrl = process.env.WAKEDOCK_API_URL || 'http://localhost:8000';

// ✅ FIX APPLIQUÉ
const wakedockApiUrl = process.env.WAKEDOCK_API_URL || process.env.PUBLIC_API_URL || 'http://195.201.199.226:8000';
```

**Actions Requises:**
- [ ] Configuration dynamique CSP via environment
- [ ] Whitelist IPs via configuration sécurisée
- [ ] Tests CSP automatisés
- [ ] Monitoring violations CSP

---

### 🚨 3. Logs de Debug en Production
**Fichier:** `dashboard/src/lib/api.ts:263,279`  
**Statut:** ❌ NON RÉSOLU

```typescript
// ❌ PROBLÈME: Logs forcés en production
console.log('🚀 API Request START:', { url, method, ... });
console.log('✅ API Response received:', { url, status, ... });

// ✅ SOLUTION
if (config.enableDebug || process.env.NODE_ENV === 'development') {
  console.log('🚀 API Request START:', { url, method, ... });
}
```

**Actions Requises:**
- [ ] Conditionner TOUS les logs de debug
- [ ] Logger service centralisé
- [ ] Configuration niveaux de log
- [ ] Nettoyage logs sensibles

---

## ⚡ BUGS CRITIQUES SYSTÈME

### 🔥 4. Timeout AbortController Inapproprié
**Fichier:** `dashboard/src/lib/api.ts:147`  
**Statut:** ⚠️ FIX PARTIEL

```typescript
// ⚠️ ACTUEL: Timeout réduit mais non optimal
private timeout: number = 30000; // 30 seconds

// ✅ SOLUTION: Timeouts configurables par endpoint
private getTimeout(endpoint: string): number {
  const timeouts = {
    '/auth/login': 10000,     // 10s pour auth
    '/services': 20000,       // 20s pour services
    '/system': 30000,         // 30s pour system
    default: 15000            // 15s par défaut
  };
  return timeouts[endpoint] || timeouts.default;
}
```

**Actions Requises:**
- [ ] Timeouts configurables par type d'endpoint
- [ ] Retry strategies intelligentes  
- [ ] Monitoring temps de réponse
- [ ] Fallback graceful degradation

---

### 🔥 5. Gestion d'Erreur Network Incomplète
**Fichier:** `dashboard/src/lib/api.ts:323-367`  
**Statut:** ❌ PARTIEL

**Actions Requises:**
- [ ] Différencier erreurs network vs API
- [ ] Offline detection et cache
- [ ] User feedback précis sur erreurs
- [ ] Retry exponential backoff
- [ ] Circuit breaker pattern

---

## 📝 CODE TEMPORAIRE À NETTOYER

### 🧹 6. Code TEMPORARY/FIXME/TODO
**Identifiés:** 47 occurrences frontend + 22 backend

**Frontend Critiques:**
```typescript
// dashboard/src/lib/stores/auth.ts:146,152
refreshToken: null, // TODO: récupérer depuis localStorage si disponible
sessionExpiry: null, // TODO: calculer à partir du token
```

**Backend Critiques:**
```python
# src/wakedock/plugins/base.py
# TODO: Implement JSON schema validation

# src/wakedock/cli/commands.py  
# TODO: Add proper validation using Pydantic model
```

**Actions Requises:**
- [ ] Audit complet des TODOs
- [ ] Priorisation par impact sécurité
- [ ] Implémentation manquante
- [ ] Documentation des décisions

---

## 🔧 FICHIERS MONOLITHIQUES CRITIQUES

### 📁 7. Backend - Refactoring Urgent
**Fichiers problématiques:**
- `src/wakedock/core/caddy.py` - **879 lignes** 🚨
- `src/wakedock/api/routes/websocket.py` - **774 lignes** 🚨  
- `src/wakedock/security/validation.py` - **677 lignes**

**Actions Requises:**
- [ ] Split caddy.py en modules (CaddyConfig, CaddyAPI, CaddyManager)
- [ ] Séparer websocket.py par domaines (auth, services, system)
- [ ] Extraction classes validation spécialisées
- [ ] Tests unitaires pour chaque module

---

### 📁 8. Frontend - Composants Géants
**Fichiers problématiques:**
- `dashboard/src/routes/register/+page.svelte` - **1,343 lignes** 🚨
- `dashboard/src/lib/components/Header.svelte` - **1,163 lignes** 🚨
- `dashboard/src/routes/+page.svelte` - **1,056 lignes** 🚨

**Actions Requises:**
- [ ] Split register page en composants form
- [ ] Header en composants Navigation, UserMenu, Search
- [ ] Dashboard principal en widgets modulaires
- [ ] Shared components library

---

## ⚠️ CONFIGURATIONS INSÉCURISÉES

### 🔐 9. Secrets et Configuration
**Issues identifiées:**
- Variables d'environnement hardcodées
- Pas de secrets management
- Configuration IP publique en dur

**Actions Requises:**
- [ ] Docker secrets ou K8s secrets
- [ ] Configuration via ConfigMaps
- [ ] Vault integration pour secrets
- [ ] Rotation automatique des clés

---

## 📊 CHECKLIST DE VALIDATION

### ✅ Critères de Succès Immédiat
- [ ] **Sécurité:** Aucun log sensible en production
- [ ] **Performance:** Login < 2 secondes
- [ ] **Stabilité:** Aucun timeout non géré
- [ ] **Code:** Aucun TEMPORARY/FIXME critique
- [ ] **Tests:** 90%+ coverage sur auth flow

### 📈 Métriques de Monitoring
```yaml
Métriques Critiques:
  - Login Success Rate: >99%
  - API Response Time: <500ms P95
  - Error Rate: <0.1%
  - Security Incidents: 0
  - Code Quality Score: >8.5/10
```

---

## 🚀 PLAN D'EXÉCUTION

### Phase 1 - Sécurité (Jour 1-3)
1. Fix logs debug production 
2. Configuration CSP dynamique
3. Secrets management basique
4. Tests sécurité automatisés

### Phase 2 - Stabilité (Jour 4-7)
1. Timeouts configurables
2. Error handling robuste  
3. Retry strategies
4. Monitoring alertes

### Phase 3 - Code Quality (Jour 8-14)
1. Refactoring fichiers monolithiques
2. Nettoyage TODOs critiques
3. Tests unitaires manquants
4. Documentation sécurité

---

## 🔗 Ressources

- **Outils:** SonarQube, OWASP ZAP, Lighthouse
- **Standards:** OWASP Top 10, NIST Cybersecurity Framework
- **Monitoring:** Grafana, Prometheus, ELK Stack
- **Tests:** Jest, Playwright, pytest

---

**📞 Contact:** Dev Lead Team  
**📅 Review:** Daily standup tracking  
**🚨 Escalation:** Security incidents → CISO immediate notification