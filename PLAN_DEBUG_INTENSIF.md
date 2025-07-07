# 🚨 Plan de Débogage Intensif - Problèmes de CORS et Login

## 🔍 Analyse du Problème Actuel

D'après les logs de la console, nous avons plusieurs problèmes critiques :

1. **Configuration Runtime vs Build-time** : L'endpoint `/api/config` retourne encore les URLs externes au lieu des URLs relatives
2. **CORS Errors** : `Access to fetch at 'https://api.mtool.ovh/api/v1/auth/login' from origin 'https://admin.mtool.ovh' has been blocked by CORS policy`
3. **500 Internal Server Error** : Le backend retourne des erreurs 500 pour les requêtes de login

## 🎯 Root Causes Identifiées

### 1. Configuration Environment Override
- Le fichier `environment.ts` charge d'abord `loadConfig()` qui utilise les variables d'environnement build-time
- Ensuite `updateConfigFromRuntime()` est censé les remplacer, mais il ne fonctionne qu'en mode browser
- Le client API initialise avec la config build-time avant que la config runtime soit chargée

### 2. Build-time Environment Variables
- Le Dockerfile a des variables d'environnement qui sont bakées dans le build
- Ces variables prennent le dessus sur la config runtime

### 3. Client API Initialization Order
- L'ApiClient s'initialise avec `config.apiUrl` au moment de l'import
- `updateConfigFromRuntime()` n'est appelé qu'après l'initialisation
- Le `baseUrl` n'est jamais mis à jour

## 🛠️ Plan de Résolution Intensif

### Phase 1: Diagnostic Complet
1. **Vérifier la configuration runtime actuelle**
   - Tester l'endpoint `/api/config` en direct
   - Vérifier les variables d'environnement dans le container dashboard
   - Vérifier les logs de démarrage du dashboard

2. **Analyser l'ordre d'initialisation**
   - Ajouter des logs détaillés dans `environment.ts` et `api.ts`
   - Tracer l'ordre d'exécution des fonctions de configuration

### Phase 2: Corrections Configuration
1. **Forcer les URLs relatives au build-time**
   - Supprimer complètement les variables d'environnement du Dockerfile
   - S'assurer que les defaultConfig utilisent toujours des URLs relatives
   - Éliminer complètement `loadConfig()` en faveur de `loadRuntimeConfig()`

2. **Réorganiser l'ordre d'initialisation**
   - Déplacer `updateConfigFromRuntime()` avant l'initialisation de l'ApiClient
   - Utiliser un pattern de lazy initialization pour l'ApiClient
   - Implémenter un mécanisme de réinitialisation du baseUrl

### Phase 3: Corrections CORS Backend
1. **Vérifier la configuration CORS du backend**
   - S'assurer que le backend accepte les requêtes de `https://admin.mtool.ovh`
   - Vérifier les headers CORS dans les réponses du backend
   - Tester directement l'endpoint de login du backend

2. **Analyser la configuration Caddy**
   - Vérifier que les routes /api/* pointent vers le bon service
   - S'assurer qu'il n'y a pas de conflits de headers CORS

### Phase 4: Test et Validation
1. **Tests de configuration**
   - Valider que `/api/config` retourne bien des URLs relatives
   - Vérifier que l'ApiClient utilise bien ces URLs relatives
   - Tester les requêtes en mode développement avec logs détaillés

2. **Tests d'authentification**
   - Tester le login avec des credentials valides
   - Vérifier les headers de la requête de login
   - Analyser les réponses du backend

## 📋 Actions Spécifiques à Exécuter

### 1. Correction du Dockerfile Dashboard
```dockerfile
# Supprimer complètement ces lignes:
# ARG WAKEDOCK_API_URL=...
# ENV VITE_API_BASE_URL=...
# ENV PUBLIC_API_URL=...
# ENV PUBLIC_WS_URL=...
```

### 2. Modification de environment.ts
```typescript
// Supprimer loadConfig() et utiliser uniquement loadRuntimeConfig()
// Initialiser avec des defaultConfig qui utilisent TOUJOURS des URLs relatives
// Ne plus utiliser les variables d'environnement build-time
```

### 3. Réorganisation de api.ts
```typescript
// Pattern de lazy initialization
// Attendre que la configuration runtime soit chargée avant d'initialiser baseUrl
// Implémenter une méthode de reconfiguration dynamique
```

### 4. Tests Backend Direct
```bash
# Tester directement l'endpoint backend
curl -X POST https://api.mtool.ovh/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Origin: https://admin.mtool.ovh" \
  -d "username=test&password=test"
```

### 5. Logs de Débogage
```typescript
// Ajouter des logs détaillés partout:
// - Dans updateConfigFromRuntime()
// - Dans l'initialisation de ApiClient
// - Dans les requêtes de login
// - Dans les réponses du serveur
```

## 🚨 Points Critiques à Surveiller

1. **Timing Issues** : L'ordre d'exécution des fonctions de configuration
2. **Browser vs Server Rendering** : Les différences entre SSR et client-side
3. **Cache Issues** : S'assurer que les nouvelles images Docker sont bien utilisées
4. **Service Discovery** : Vérifier que Caddy route bien vers les bons services
5. **CORS Headers** : S'assurer qu'il n'y a qu'une seule source de headers CORS

## 🎯 Objectifs de Réussite

1. ✅ L'endpoint `/api/config` retourne `{"apiUrl": "/api/v1", "wsUrl": "/ws"}`
2. ✅ Les requêtes de login vont vers `/api/v1/auth/login` (relatif)
3. ✅ Aucune erreur CORS dans la console
4. ✅ Le login fonctionne avec des credentials valides
5. ✅ La redirection après login fonctionne correctement

## 🔄 Workflow de Test

1. **Rebuild complet** : `docker-compose build --no-cache dashboard`
2. **Redéploiement** : `docker service update --force wakedock_dashboard`
3. **Test config** : `curl https://admin.mtool.ovh/api/config`
4. **Test login frontend** : Utiliser l'interface web
5. **Analyse logs** : Vérifier les logs du dashboard et du backend
6. **Test login direct** : Curl direct vers le backend

Ce plan couvre tous les aspects du problème et devrait permettre de résoudre définitivement les problèmes de CORS et de login.