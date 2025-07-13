# Plan d'Intégration des Scripts dans WakeDock

## 🎯 Vision : Tool de Maintenance Unifié

### 📋 État Actuel des Fonctionnalités

#### ✅ **Déjà Disponibles dans l'Application**
- **Health Check** : `/api/v1/health` + `/api/v1/system/health`
- **System Overview** : Dashboard + API endpoints
- **Service Management** : CRUD complet via API + Dashboard
- **Monitoring** : Métriques intégrées + WebSocket temps réel
- **Authentication** : JWT + gestion utilisateurs
- **Database Management** : ORM + migrations automatiques

#### 🔄 **À Intégrer depuis les Scripts**
- **Backup/Restore** : Fonctionnalité partiellement présente
- **Dependencies Management** : Audit et mise à jour
- **Config Validation** : Contrôles avancés
- **Cleanup** : Nettoyage automatisé
- **Secrets Management** : Gestion sécurisée

## 🏗️ Architecture Proposée

### 1. **Backend Extensions (FastAPI)**

#### Nouveaux Endpoints API
```
/api/v1/maintenance/
  ├── backup/          # Sauvegarde/restauration
  ├── cleanup/         # Nettoyage système
  ├── dependencies/    # Gestion dépendances  
  ├── validation/      # Validation config
  └── secrets/         # Gestion secrets
```

#### Services Backend
```python
# src/wakedock/maintenance/
├── backup_service.py      # Backup/restore logic
├── cleanup_service.py     # Cleanup operations
├── dependency_service.py  # Dependencies audit
├── validation_service.py  # Config validation
└── secrets_service.py     # Secrets management
```

### 2. **Frontend Extensions (SvelteKit)**

#### Nouvelle Section Dashboard
```
/maintenance
  ├── backup          # Interface backup/restore
  ├── system-health   # Health monitoring avancé
  ├── dependencies    # Audit dépendances
  ├── cleanup         # Outils de nettoyage
  └── validation      # Validation configuration
```

#### Components React
```typescript
// dashboard/src/lib/components/maintenance/
├── BackupManager.svelte    # Gestion sauvegardes
├── HealthMonitor.svelte    # Monitoring santé
├── CleanupTools.svelte     # Outils nettoyage
├── DependencyAudit.svelte  # Audit dépendances
└── ConfigValidator.svelte  # Validation config
```

### 3. **CLI Tool Optionnel**

```bash
# Outil CLI pour administration locale
./wakedock-cli maintenance
  ├── backup [create|restore|list]
  ├── health [check|monitor]
  ├── cleanup [cache|logs|temp]
  ├── deps [audit|update|security]
  └── validate [config|setup]
```

## 🚀 Implémentation Progressive

### Phase 1 : Extensions Backend (2-3 jours)
1. **Health Monitoring** - Étendre l'API existante
2. **Backup Service** - Intégrer la logique des scripts
3. **Config Validation** - Service de validation

### Phase 2 : Interface Frontend (2-3 jours)  
1. **Maintenance Dashboard** - Nouvelle section
2. **Health Monitoring UI** - Interface temps réel
3. **Backup Manager UI** - Gestion graphique

### Phase 3 : CLI Tool (1-2 jours)
1. **CLI Interface** - Outil ligne de commande
2. **Script Migration** - Wrapper pour compatibilité
3. **Documentation** - Guide utilisateur

## 💰 Avantages vs Scripts Séparés

### ✅ **Avantages Intégration**
- **Consistency** : Interface unifiée
- **Real-time** : WebSocket pour mises à jour live
- **Security** : Authentication centralisée  
- **Maintenance** : Un seul codebase
- **User Experience** : Interface graphique moderne
- **Monitoring** : Historique et alertes intégrées

### ⚠️ **Inconvénients Scripts Séparés**
- **Duplication** : Logique en double
- **Maintenance** : 2 systèmes à maintenir
- **Inconsistency** : Interfaces différentes
- **Security** : Gestion auth séparée
- **User Experience** : CLI uniquement

## 🎯 Recommandation Finale

**Intégrer dans l'application** avec un **CLI companion tool** optionnel pour les administrateurs qui préfèrent la ligne de commande.

### Workflow Recommandé
1. **Utilisateurs normaux** → Dashboard Web
2. **Administrateurs** → CLI tool + Dashboard
3. **Automation** → API directe
4. **Scripts existants** → Wrapper CLI pour compatibilité

Cette approche offre le meilleur des deux mondes : interface moderne intégrée + outil CLI pour les power users.
