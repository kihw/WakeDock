# Scripts WakeDock

Ce dossier contient les scripts essentiels pour le fonctionnement, la maintenance et le déploiement de WakeDock.

## 🗂️ Structure Optimisée

### 🚀 Scripts de Démarrage et Configuration
- **`setup.sh`** - Configuration initiale complète du projet
- **`start.sh`** - Démarrage de l'application avec options
- **`validate-config.py`** - Validation de la configuration

### 🗄️ Scripts de Base de Données  
- **`init-db.sh`** - Initialisation de la base de données
- **`init-db.sql`** - Script SQL d'initialisation
- **`migrate.sh`** - Gestion des migrations de schéma

### 🔧 Scripts de Maintenance
- **`backup.sh`** - Sauvegarde complète des données
- **`restore.sh`** - Restauration des sauvegardes
- **`health-check.sh`** - Monitoring et vérification de santé
- **`status.sh`** - Vérification du statut des services

### 🆕 Scripts d'Automatisation (2025)
- **`cleanup-project.sh`** - Nettoyage automatisé complet
- **`manage-dependencies.sh`** - Gestion des dépendances et audit de sécurité
- **`analyze-docker-compose.sh`** - Analyse et optimisation Docker Compose

# Mode automatique
./scripts/cleanup.sh --auto
```

## Types de Fichiers Nettoyés

### 🐍 Python
- `__pycache__/` - Caches de bytecode Python
- `*.pyc`, `*.pyo` - Fichiers bytecode compilés
- `.pytest_cache/` - Cache des tests pytest
- `.mypy_cache/` - Cache du vérificateur de types
- `.tox/` - Cache de l'outil de test tox
- `.coverage`, `htmlcov/` - Rapports de couverture de code

### 🟢 Node.js/JavaScript
- `node_modules/` - Dépendances Node.js (confirmation requise)
- `.svelte-kit/` - Cache de build SvelteKit
- `build/`, `dist/` - Dossiers de build
- `.vite/` - Cache Vite

### 📁 Fichiers Temporaires
- `*.tmp`, `*.temp` - Fichiers temporaires
- `*.bak` - Fichiers de sauvegarde
- `*.log` (anciens) - Logs datés
- Dossiers `tmp/`, `.tmp/`

### 🗃️ Environnements
- `.venv/` - Environnement virtuel Python (confirmation requise)
- `venv/`, `env/` - Autres environnements virtuels

## Configuration

### Rétention des Fichiers
- **Logs:** Conservés 7 jours par défaut
- **Sauvegardes:** Conservées 30 jours par défaut

Ces valeurs peuvent être modifiées dans les scripts.

### Fichiers Protégés
Les scripts évitent de supprimer:
- Fichiers de configuration actifs
- Données utilisateur importantes
- Certificats et clés de sécurité
- Fichiers Git

## Sécurité

- Les scripts incluent une gestion d'erreur pour éviter les suppressions accidentelles
- Mode confirmation pour les opérations sensibles
- Logs des opérations pour traçabilité
- Respect du `.gitignore` du projet

## Automatisation

### Tâche Programmée (Windows)
Pour automatiser le nettoyage quotidien:

```powershell
# Créer une tâche programmée
schtasks /create /tn "WakeDock-Cleanup" /tr "powershell.exe -File 'C:\path\to\WakeDock\scripts\quick-clean.ps1'" /sc daily /st 02:00
```

### Cron (Linux/macOS)
```bash
# Ajouter à crontab pour exécution quotidienne à 2h00
0 2 * * * /path/to/WakeDock/scripts/cleanup.sh --auto
```

## Résolution de Problèmes

### Permission Denied
- **Windows:** Exécuter PowerShell en tant qu'administrateur
- **Linux/macOS:** Vérifier les permissions avec `chmod +x`

### Environnement Virtuel Actif
Si un environnement virtuel est actif, désactivez-le avant le nettoyage:
```bash
deactivate
```

### Node_modules Volumineux
Le nettoyage de `node_modules` peut prendre du temps. Soyez patient lors de cette opération.

## Contribution

Pour améliorer ces scripts:
1. Testez sur votre environnement
2. Proposez des améliorations via pull request
3. Documentez les nouveaux types de fichiers à nettoyer

---

💡 **Conseil:** Exécutez `quick-clean.ps1` régulièrement pour maintenir un environnement de développement propre.

## 📖 Guide d'Utilisation

### Configuration Initiale
```bash
# Configuration complète du projet
./scripts/setup.sh

# Validation de la configuration
python scripts/validate-config.py
```

### Démarrage de l'Application
```bash
# Démarrage normal
./scripts/start.sh

# Démarrage avec options spécifiques
./scripts/start.sh --env=production --logs
```

### Base de Données
```bash
# Initialisation de la base
./scripts/init-db.sh

# Migration de schéma
./scripts/migrate.sh
```

### Maintenance
```bash
# Vérification de santé
./scripts/health-check.sh

# Statut des services
./scripts/status.sh

# Sauvegarde
./scripts/backup.sh

# Restauration
./scripts/restore.sh [backup_file]
```

### Nettoyage et Optimisation
```bash
# Nettoyage complet
./scripts/cleanup-project.sh

# Gestion des dépendances
./scripts/manage-dependencies.sh

# Analyse Docker
./scripts/analyze-docker-compose.sh
```

## 🔧 Scripts Supprimés (Juillet 2025)

Les scripts suivants ont été supprimés car ils étaient redondants ou non essentiels :
- ~~`code-cleanup.sh`~~ - Remplacé par `cleanup-project.sh`
- ~~`cleanup.sh`~~ - Remplacé par `cleanup-project.sh`  
- ~~`quick-clean.ps1`~~ - Fonctionnalité intégrée dans `cleanup-project.sh`
- ~~`cleanup-windows.ps1`~~ - Fonctionnalité intégrée dans `cleanup-project.sh`
- ~~`setup.bat`~~ - Version Windows non nécessaire
- ~~`update.sh`~~ - Intégré dans `manage-dependencies.sh`
- ~~`setup-caddy.sh`~~ - Configuration spécifique non critique

## 🎯 Workflow Recommandé

### Développement Quotidien
```bash
./scripts/status.sh           # Vérifier l'état
./scripts/start.sh           # Démarrer l'application
```

### Maintenance Hebdomadaire  
```bash
./scripts/cleanup-project.sh      # Nettoyage
./scripts/manage-dependencies.sh  # Audit des dépendances
./scripts/backup.sh               # Sauvegarde
```

### Maintenance Mensuelle
```bash
./scripts/analyze-docker-compose.sh  # Analyse Docker
./scripts/health-check.sh           # Vérification complète
```

### Déploiement
```bash
./scripts/setup.sh                  # Configuration
./scripts/init-db.sh               # Base de données  
./scripts/migrate.sh               # Migrations
./scripts/start.sh --env=production # Démarrage
```

---

**✨ Structure optimisée avec 14 scripts essentiels (7 scripts supprimés)**
