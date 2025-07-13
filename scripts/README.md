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

**💡 Astuce** : Utilisez `./cleanup-migration-guide.sh aliases` pour créer des alias de compatibilité.
