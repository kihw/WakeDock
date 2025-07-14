# Scripts de Versioning WakeDock

Ce dossier contient les scripts pour gérer les versions des repositories WakeDock.

## Scripts Disponibles

### 1. `release-version.sh` - Release Complète
Script principal pour créer une nouvelle release sur tous les repositories.

**Fonctionnalités:**
- Demande la nouvelle version à l'utilisateur
- Met à jour automatiquement tous les fichiers de configuration
- Crée des branches de release `release/vX.Y.Z`
- Fait des commits avec des messages standardisés
- Crée et pousse les tags `vX.Y.Z`
- Gère les 3 repositories: WakeDock principal, backend, et frontend

**Usage:**
```bash
./scripts/release-version.sh
```

**Via VS Code:**
- Utiliser la tâche: `Release Version - All Repositories`

### 2. `update-single-version.sh` - Mise à Jour Individuelle
Script pour mettre à jour la version d'un seul repository.

**Usage:**
```bash
# Mode interactif
./scripts/update-single-version.sh

# Mode direct
./scripts/update-single-version.sh [backend|frontend|main] [version]
```

**Exemples:**
```bash
./scripts/update-single-version.sh backend 1.2.3
./scripts/update-single-version.sh frontend 1.2.3
./scripts/update-single-version.sh main 1.2.3
```

**Via VS Code:**
- `Update Version - Main Repository`
- `Update Version - Backend`
- `Update Version - Frontend`

### 3. `validate-versions.sh` - Validation des Versions
Script pour vérifier la cohérence des versions entre tous les repositories.

**Fonctionnalités:**
- Vérifie la cohérence entre repositories standalone et sous-projets
- Contrôle les versions dans le code (frontend)
- Détecte les incohérences et propose des solutions

**Usage:**
```bash
./scripts/validate-versions.sh
```

**Via VS Code:**
- Utiliser la tâche: `Validate Versions`

## Tâches VS Code

Les tâches suivantes sont disponibles via `Ctrl+Shift+P` > `Tasks: Run Task`:

1. **Release Version - All Repositories**: Lance une release complète
2. **Update Version - Main Repository**: Met à jour le repo principal
3. **Update Version - Backend**: Met à jour le backend
4. **Update Version - Frontend**: Met à jour le frontend
5. **Validate Versions**: Valide la cohérence des versions

## Workflow Recommandé

### Release Complète
1. Vérifier que tous les repositories sont propres (pas de changements non commités)
2. Être sur la branche `main` de tous les repositories
3. Exécuter `./scripts/release-version.sh`
4. Suivre les instructions interactives
5. Créer les Pull Requests pour merger les branches de release
6. Tester et déployer

### Mise à Jour Individuelle
1. Se placer dans le repository concerné
2. Exécuter `./scripts/update-single-version.sh [type] [version]`
3. Pousser les changements et créer le tag

### Validation
```bash
# Avant une release
./scripts/validate-versions.sh

# Après des modifications manuelles
./scripts/validate-versions.sh
```

## Fichiers Mis à Jour

### Repository Principal (WakeDock)
- `package.json`
- `Dockerfile`
- `wakedock-backend/pyproject.toml` (si présent)
- `wakedock-frontend/package.json` (si présent)
- Références de version dans le code frontend

### Backend (wakedock-backend)
- `pyproject.toml`

### Frontend (wakedock-frontend)
- `package.json`
- `src/lib/utils/storage.ts`
- `src/lib/components/sidebar/SidebarFooter.svelte`
- `src/lib/components/auth/login/LoginFooter.svelte`

## Format de Version

Les scripts utilisent le format de versioning sémantique: `X.Y.Z`

Exemple: `1.2.3`

## Prérequis

- Git installé et configuré
- Bash shell
- `jq` (optionnel, mais recommandé pour une meilleure gestion JSON)
- Accès en écriture aux repositories

## Dépannage

### Erreur: "Repository a des changements non commités"
```bash
git status
git add .
git commit -m "description des changements"
```

### Erreur: "Format de version invalide"
Utilisez le format `X.Y.Z` (exemple: `1.2.3`)

### Erreur: "Pas sur la branche main"
```bash
git checkout main
git pull origin main
```

### Incohérences de versions détectées
Utilisez `./scripts/validate-versions.sh` pour identifier les problèmes, puis:
1. Utilisez `release-version.sh` pour synchroniser tout
2. Ou corrigez manuellement avec `update-single-version.sh`

## Structure des Branches

- `main`: Branche principale
- `release/vX.Y.Z`: Branches de release temporaires
- Tags: `vX.Y.Z` pour chaque version

## Bonnes Pratiques

1. **Toujours valider** avant de faire une release
2. **Tester** les builds après mise à jour de version
3. **Documenter** les changements dans les CHANGELOG
4. **Synchroniser** les versions entre tous les repositories
5. **Utiliser les tâches VS Code** pour une meilleure expérience

---

# 📁 Scripts WakeDock

> **🔄 Mise à jour importante** : Plusieurs scripts redondants ont été supprimés et leurs fonctionnalités intégrées dans l'application principale.

## 🗑️ Scripts Supprimés (Entièrement Redondants)

Les scripts suivants ont été **supprimés** car ils étaient 100% redondants avec l'API et le dashboard :

- ❌ `health_check.py` → Remplacé par `/api/v1/health`
- ❌ `health-check.sh` → Remplacé par `/api/v1/system/health`  
- ❌ `status.sh` → Remplacé par `/api/v1/system/overview`
- ❌ `validate-auth-fix.sh` → Tests intégrés dans l'application
- ❌ `test-api-enhancements.sh` → Tests intégrés dans l'application

**Migration** : Utilisez `./cleanup-migration-guide.sh` pour voir les alternatives API.

## 📁 Structure Actuelle

```
scripts/
├── 📋 CLEANUP_REPORT.md           # Rapport de nettoyage détaillé
├── 🔄 cleanup-migration-guide.sh  # Guide de migration
├── 📖 migration-helper.sh         # Assistant de migration structure
├── 🚀 start.sh                    # Script de démarrage rapide
│
├── 📁 setup/                      # Scripts d'installation
│   ├── setup.sh                   # Installation complète
│   └── validate-config.py         # Validation configuration
│
├── 📁 database/                   # Gestion base de données
│   ├── init-db.sh                 # Initialisation BDD
│   ├── init-db.sql                # Scripts SQL de base
│   └── migrate.sh                 # Migrations
│
├── 📁 maintenance/                # Maintenance système
│   ├── backup.sh                  # Sauvegarde (🟡 à intégrer API)
│   ├── restore.sh                 # Restauration (🟡 à intégrer API)
│   ├── cleanup-project.sh         # Nettoyage développement
│   ├── manage-dependencies.sh     # Gestion dépendances
│   └── manage-secrets.sh          # Gestion secrets
│
├── 📁 monitoring/                 # Surveillance avancée
│   ├── analyze-docker-compose.sh  # Analyse Docker Compose
│   └── performance_benchmark.py   # Benchmarks spécialisés
│
└── 📁 deprecated/                 # Scripts obsolètes archivés
    ├── debug-auth.sh
    ├── run_performance_migrations.py
    ├── test-api-enhancements.sh
    └── validate-auth-fix.sh
```

## 🚀 Usage Rapide

```bash
# Démarrage rapide
./start.sh

# Guide de migration après cleanup
./cleanup-migration-guide.sh

# Installation complète
./setup/setup.sh

# Initialisation base de données
./database/init-db.sh

# Sauvegarde système
./maintenance/backup.sh

# Analyse performance
python ./monitoring/performance_benchmark.py
```

## 🔄 Migration vers l'API

Les fonctionnalités de monitoring sont maintenant disponibles via :

### API Endpoints
- `GET /api/v1/health` - Vérification santé rapide
- `GET /api/v1/system/health` - Santé détaillée  
- `GET /api/v1/system/overview` - Vue d'ensemble système
- `GET /api/v1/services` - Gestion des services

### Dashboard Web
- **URL** : `http://localhost/`
- **Monitoring** : Temps réel avec graphiques
- **Services** : Gestion complète via interface
- **Health** : Visualisation des statuts

### CLI Alternatives
```bash
# Ancien : ./health-check.sh
curl -s http://localhost/api/v1/health | jq .

# Ancien : ./status.sh  
curl -s http://localhost/api/v1/system/overview | jq .

# Services
curl -s http://localhost/api/v1/services | jq .
```

## 📊 Statistiques Cleanup

- **✅ Supprimés** : 5 scripts (100% redondants)
- **🟡 À intégrer** : 2 scripts (backup/restore)  
- **✅ Conservés** : 10 scripts (utiles/nécessaires)
- **📉 Réduction** : 31% des scripts redondants

## 🎯 Prochaines Étapes

1. **Phase 1** : Intégrer backup/restore dans l'API
2. **Phase 2** : CLI tool optionnel pour compatibilité
3. **Phase 3** : Migration complète vers dashboard

## 📖 Documentation

- [`CLEANUP_REPORT.md`](CLEANUP_REPORT.md) - Rapport détaillé du nettoyage
- [`REORGANIZATION_REPORT.md`](REORGANIZATION_REPORT.md) - Rapport de réorganisation
- [`INTEGRATION_PLAN.md`](INTEGRATION_PLAN.md) - Plan d'intégration API

---

**💡 Astuce** : Utilisez `./cleanup-migration-guide.sh aliases` pour créer des alias de compatibilité
