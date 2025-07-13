# WakeDock Scripts Integration Tasks

## Phase 1 - Backend Extensions (2-3 jours)

### 1.1 Maintenance API Endpoints
- [ ] Créer `src/wakedock/api/routes/maintenance.py`
- [ ] Endpoint `POST /api/v1/maintenance/backup` (body: `{"type": "full|database|config"}`)
- [ ] Endpoint `POST /api/v1/maintenance/restore` (multipart upload + options)
- [ ] Endpoint `GET /api/v1/maintenance/backups` (liste backups disponibles)
- [ ] Endpoint `DELETE /api/v1/maintenance/backups/{id}` (suppression backup)

### 1.2 Backup Service
- [ ] Créer `src/wakedock/services/backup_service.py`
- [ ] Méthode `create_backup(backup_type, include_volumes=True)`
- [ ] Méthode `restore_backup(file_path, options)`
- [ ] Méthode `list_backups()` avec métadonnées
- [ ] Méthode `cleanup_old_backups(retain_days=7)`

### 1.3 Dependencies Management Service
- [ ] Créer `src/wakedock/services/dependencies_service.py`
- [ ] Méthode `check_dependencies()` (Docker, Python packages)
- [ ] Méthode `update_dependencies(component)`
- [ ] Méthode `get_dependency_status()`

### 1.4 Project Cleanup Service
- [ ] Créer `src/wakedock/services/cleanup_service.py`
- [ ] Méthode `cleanup_docker_resources()`
- [ ] Méthode `cleanup_logs(max_age_days)`
- [ ] Méthode `cleanup_temp_files()`
- [ ] Méthode `get_cleanup_report()`

### 1.5 Configuration Validation
- [ ] Étendre `src/wakedock/services/config_service.py`
- [ ] Méthode `validate_full_config()`
- [ ] Méthode `fix_config_issues(auto_fix=True)`
- [ ] Méthode `export_config_backup()`

## Phase 2 - Frontend Extensions (2-3 jours)

### 2.1 Maintenance API Client
- [ ] Créer `dashboard/src/lib/api/maintenance-api.ts`
- [ ] Interface `BackupRequest`, `RestoreOptions`, `BackupInfo`
- [ ] Méthodes API client pour tous les endpoints maintenance

### 2.2 Maintenance Page Layout
- [ ] Créer `dashboard/src/routes/maintenance/+layout.svelte`
- [ ] Navigation tabs: Backup, Cleanup, Dependencies, Config
- [ ] Breadcrumb et état global maintenance

### 2.3 Backup Management
- [ ] Créer `dashboard/src/routes/maintenance/backup/+page.svelte`
- [ ] Formulaire création backup (type, options)
- [ ] Liste backups existants avec actions (download, restore, delete)
- [ ] Progress bar pour opérations longues
- [ ] Restauration avec upload file + options

### 2.4 System Cleanup Interface
- [ ] Créer `dashboard/src/routes/maintenance/cleanup/+page.svelte`
- [ ] Sélection catégories à nettoyer (Docker, logs, temp)
- [ ] Aperçu espace libéré avant nettoyage
- [ ] Rapport post-nettoyage avec détails

### 2.5 Dependencies Manager
- [ ] Créer `dashboard/src/routes/maintenance/dependencies/+page.svelte`
- [ ] Table status dépendances (version actuelle, disponible)
- [ ] Actions update par composant
- [ ] Logs mise à jour en temps réel

### 2.6 Configuration Validator
- [ ] Créer `dashboard/src/routes/maintenance/config/+page.svelte`
- [ ] Validation complète configuration
- [ ] Liste erreurs/warnings avec auto-fix
- [ ] Export/import configuration

## Phase 3 - CLI Tool (1-2 jours)

### 3.1 CLI Core
- [ ] Créer `src/wakedock/cli/main.py`
- [ ] Parser commandes avec `click` ou `typer`
- [ ] Configuration client API (base_url, auth)
- [ ] Gestion erreurs et output formaté

### 3.2 CLI Commands
- [ ] Commande `wakedock-cli health` (remplace health-check.sh)
- [ ] Commande `wakedock-cli status` (remplace status.sh)
- [ ] Commande `wakedock-cli backup create [options]`
- [ ] Commande `wakedock-cli backup restore <file>`
- [ ] Commande `wakedock-cli cleanup [--docker] [--logs]`
- [ ] Commande `wakedock-cli deps check|update`

### 3.3 CLI Installation
- [ ] Script `scripts/install-cli.sh`
- [ ] Symlink `/usr/local/bin/wakedock-cli`
- [ ] Autocompletion bash/zsh
- [ ] Page man `wakedock-cli(1)`

### 3.4 Legacy Compatibility
- [ ] Wrapper scripts dans `scripts/legacy/`
- [ ] `legacy/health-check.sh` → `wakedock-cli health`
- [ ] `legacy/status.sh` → `wakedock-cli status`
- [ ] Migration guide mise à jour

## Tests & Documentation

### Tests Backend
- [ ] Tests unitaires `BackupService`
- [ ] Tests intégration endpoints `/api/v1/maintenance/`
- [ ] Tests E2E backup/restore workflow

### Tests Frontend
- [ ] Tests composants maintenance
- [ ] Tests intégration API calls
- [ ] Tests E2E workflow complet

### Documentation
- [ ] API docs endpoints maintenance
- [ ] Guide utilisateur section maintenance
- [ ] CLI reference documentation
- [ ] Migration guide scripts → app
