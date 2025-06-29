# Scripts de Nettoyage WakeDock

Ce dossier contient des scripts pour nettoyer automatiquement les fichiers temporaires et inutiles du projet WakeDock.

## Scripts Disponibles

### 🪟 Windows

#### `quick-clean.ps1`
Script de nettoyage rapide et automatique.

**Utilisation:**
```powershell
.\scripts\quick-clean.ps1
```

**Ce qu'il nettoie:**
- Dossiers `__pycache__` et fichiers `.pyc/.pyo`
- Dossiers de build (`.svelte-kit`, `build`, `dist`, `.vite`)
- Caches de test (`.pytest_cache`, `.mypy_cache`, `.tox`)
- Fichiers temporaires (`.tmp`, `.temp`, `.bak`)
- Anciens logs (> 7 jours)

#### `cleanup-windows.ps1`
Script de nettoyage complet avec options interactives.

**Utilisation:**
```powershell
# Mode interactif
.\scripts\cleanup-windows.ps1

# Mode automatique (sans confirmations)
.\scripts\cleanup-windows.ps1 -Auto
```

**Fonctionnalités:**
- Nettoyage automatique des fichiers temporaires
- Options interactives pour supprimer `node_modules` et `.venv`
- Nettoyage des anciennes sauvegardes
- Logs détaillés des opérations

### 🐧 Linux/macOS

#### `cleanup.sh`
Script de nettoyage pour les systèmes Unix (déjà existant).

**Utilisation:**
```bash
# Mode interactif
./scripts/cleanup.sh

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
