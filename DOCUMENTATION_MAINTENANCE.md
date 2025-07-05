# 📚 DOCUMENTATION & MAINTENANCE - WakeDock

**Priorité: 🟢 FAIBLE**  
**Timeline: 1-2 semaines**  
**Équipe: Tech Writer + DevOps + Lead Dev + Product Owner**

## 📋 Vue d'Ensemble

Ce document détaille la stratégie complète de documentation et de maintenance pour WakeDock. L'audit révèle une documentation fragmentée, des procédures de maintenance manuelles, et un manque de guides opérationnels nécessitant une standardisation complète pour assurer la maintenabilité long terme du projet.

---

## 🎯 OBJECTIFS DOCUMENTATION

### 📊 Standards de Documentation

```yaml
Documentation Coverage:
  - API Documentation: 100% endpoints documentés
  - User Guides: Tous les workflows couverts
  - Developer Docs: Setup à déploiement complet
  - Operations Runbooks: Tous les incidents types
  - Architecture Docs: Diagrammes à jour

Quality Standards:
  - Accuracy: 100% information vérifiée
  - Completeness: Aucun gap dans les workflows
  - Accessibility: Documentation multilingue
  - Maintenance: Mise à jour automatique
  - Searchability: Index complet et tags
```

---

## 📖 ARCHITECTURE DOCUMENTATION

### 1. Documentation as Code

```yaml
# .github/workflows/docs.yml
name: Documentation Build & Deploy

on:
  push:
    branches: [main]
    paths: ['docs/**', 'src/**/*.py', 'dashboard/src/**/*.ts']
  pull_request:
    branches: [main]
    paths: ['docs/**']

jobs:
  build-docs:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git info
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install documentation dependencies
        run: |
          pip install mkdocs-material mkdocs-mermaid2-plugin
          pip install mkdocstrings[python] mkdocs-swagger-ui-tag
          pip install -e .  # Install project for API docs generation
      
      - name: Setup Node.js for frontend docs
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Generate API documentation
        run: |
          # Backend API docs avec OpenAPI
          python scripts/generate_api_docs.py
          
          # Frontend component docs avec Storybook
          cd dashboard && npm ci && npm run build-storybook
      
      - name: Build documentation
        run: |
          mkdocs build --clean --strict
      
      - name: Deploy to GitHub Pages
        if: github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
          cname: docs.wakedock.io
```

### 2. Structure Documentation

```
docs/
├── index.md                           # Page d'accueil
├── getting-started/
│   ├── installation.md               # Installation rapide
│   ├── quick-start.md                # Guide démarrage
│   ├── docker-setup.md               # Setup Docker
│   └── development-setup.md          # Setup développement
├── user-guide/
│   ├── dashboard.md                  # Guide dashboard
│   ├── service-management.md         # Gestion services
│   ├── user-management.md            # Gestion utilisateurs
│   ├── monitoring.md                 # Monitoring
│   └── troubleshooting.md            # Dépannage utilisateur
├── developer-guide/
│   ├── architecture/
│   │   ├── overview.md               # Vue d'ensemble
│   │   ├── backend-architecture.md   # Architecture backend
│   │   ├── frontend-architecture.md  # Architecture frontend
│   │   └── database-schema.md        # Schéma base de données
│   ├── api/
│   │   ├── authentication.md         # API authentification
│   │   ├── services.md               # API services
│   │   ├── users.md                  # API utilisateurs
│   │   └── webhooks.md               # Webhooks
│   ├── contributing/
│   │   ├── guidelines.md             # Guidelines contribution
│   │   ├── code-style.md             # Style de code
│   │   ├── testing.md                # Guide testing
│   │   └── pull-requests.md          # Process PR
│   └── deployment/
│       ├── docker-compose.md         # Déploiement Docker
│       ├── kubernetes.md             # Déploiement K8s
│       ├── production.md             # Production setup
│       └── scaling.md                # Guide scaling
├── operations/
│   ├── runbooks/
│   │   ├── incident-response.md      # Réponse incidents
│   │   ├── backup-restore.md         # Sauvegarde/restauration
│   │   ├── performance-tuning.md     # Optimisation performance
│   │   └── security-hardening.md     # Durcissement sécurité
│   ├── monitoring/
│   │   ├── metrics.md                # Métriques système
│   │   ├── alerts.md                 # Configuration alertes
│   │   ├── logging.md                # Logging centralisé
│   │   └── dashboards.md             # Dashboards monitoring
│   └── maintenance/
│       ├── database-maintenance.md   # Maintenance DB
│       ├── updates.md                # Procédure mises à jour
│       ├── cleanup.md                # Nettoyage système
│       └── backup-strategy.md        # Stratégie sauvegarde
├── security/
│   ├── authentication.md             # Guide authentification
│   ├── authorization.md              # Guide autorisation
│   ├── data-protection.md            # Protection données
│   ├── vulnerability-management.md   # Gestion vulnérabilités
│   └── compliance.md                 # Conformité sécurité
├── reference/
│   ├── api-reference.md              # Référence API complète
│   ├── configuration.md              # Configuration système
│   ├── environment-variables.md      # Variables environnement
│   ├── docker-compose-reference.md   # Référence Docker Compose
│   └── cli-reference.md              # Référence CLI
└── changelog/
    ├── changelog.md                  # Changelog principal
    ├── migration-guides.md           # Guides migration
    └── breaking-changes.md           # Breaking changes
```

### 3. Documentation Automatique

```python
# scripts/generate_api_docs.py
"""Génération automatique documentation API"""

import json
import inspect
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from wakedock.main import app

class APIDocumentationGenerator:
    """Générateur documentation API automatique"""
    
    def __init__(self, fastapi_app: FastAPI):
        self.app = fastapi_app
        self.docs_dir = Path("docs/api/generated")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Génération spécification OpenAPI"""
        
        openapi_schema = get_openapi(
            title="WakeDock API",
            version="1.0.0",
            description="API complète pour la gestion de services Docker avec WakeDock",
            routes=self.app.routes,
            tags=[
                {
                    "name": "Authentication",
                    "description": "Endpoints d'authentification et gestion des sessions"
                },
                {
                    "name": "Services",
                    "description": "Gestion des services Docker (CRUD, démarrage, arrêt)"
                },
                {
                    "name": "Users",
                    "description": "Gestion des utilisateurs et permissions"
                },
                {
                    "name": "System", 
                    "description": "Métriques système et monitoring"
                },
                {
                    "name": "WebSocket",
                    "description": "Connections temps réel pour monitoring"
                }
            ]
        )
        
        # Enrichissement avec exemples
        self._add_examples_to_schema(openapi_schema)
        
        return openapi_schema
    
    def _add_examples_to_schema(self, schema: Dict[str, Any]):
        """Ajout exemples dans le schéma OpenAPI"""
        
        examples = {
            "Service": {
                "id": "srv_123456",
                "name": "nginx-app",
                "image": "nginx:latest",
                "status": "running",
                "ports": [{"host": 8080, "container": 80}],
                "environment": {"ENV": "production"},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T12:15:30Z"
            },
            "User": {
                "id": 1,
                "username": "admin",
                "email": "admin@wakedock.io",
                "full_name": "Administrator",
                "role": "admin",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "SystemOverview": {
                "services": {"total": 10, "running": 8, "stopped": 2},
                "system": {"cpu_usage": 45.2, "memory_usage": 68.1, "disk_usage": 35.7},
                "docker": {"version": "24.0.7", "status": "healthy"},
                "uptime": 86400
            }
        }
        
        # Injection exemples dans les schémas
        if "components" in schema and "schemas" in schema["components"]:
            for schema_name, example_data in examples.items():
                if schema_name in schema["components"]["schemas"]:
                    schema["components"]["schemas"][schema_name]["example"] = example_data
    
    def generate_markdown_docs(self):
        """Génération documentation Markdown depuis OpenAPI"""
        
        openapi_spec = self.generate_openapi_spec()
        
        # Grouper endpoints par tags
        endpoints_by_tag = {}
        
        for path, path_data in openapi_spec.get("paths", {}).items():
            for method, method_data in path_data.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    tags = method_data.get("tags", ["Untagged"])
                    tag = tags[0] if tags else "Untagged"
                    
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "summary": method_data.get("summary", ""),
                        "description": method_data.get("description", ""),
                        "parameters": method_data.get("parameters", []),
                        "requestBody": method_data.get("requestBody"),
                        "responses": method_data.get("responses", {}),
                        "security": method_data.get("security", [])
                    })
        
        # Génération fichiers Markdown par tag
        for tag, endpoints in endpoints_by_tag.items():
            self._generate_tag_documentation(tag, endpoints)
        
        # Génération index
        self._generate_api_index(endpoints_by_tag)
    
    def _generate_tag_documentation(self, tag: str, endpoints: List[Dict]):
        """Génération documentation pour un tag"""
        
        tag_file = self.docs_dir / f"{tag.lower().replace(' ', '-')}.md"
        
        content = [
            f"# {tag} API",
            "",
            f"Documentation des endpoints {tag.lower()}.",
            "",
        ]
        
        for endpoint in endpoints:
            content.extend([
                f"## {endpoint['method']} {endpoint['path']}",
                "",
                endpoint['summary'],
                "",
                endpoint['description'],
                "",
            ])
            
            # Paramètres
            if endpoint['parameters']:
                content.extend([
                    "### Paramètres",
                    "",
                    "| Nom | Type | Requis | Description |",
                    "|-----|------|--------|-------------|"
                ])
                
                for param in endpoint['parameters']:
                    name = param.get('name', '')
                    param_type = param.get('schema', {}).get('type', 'string')
                    required = "✓" if param.get('required', False) else ""
                    description = param.get('description', '')
                    
                    content.append(f"| {name} | {param_type} | {required} | {description} |")
                
                content.append("")
            
            # Request Body
            if endpoint['requestBody']:
                content.extend([
                    "### Corps de la requête",
                    "",
                    "```json"
                ])
                
                # Extraction exemple du schéma
                req_body = endpoint['requestBody']
                if 'content' in req_body:
                    for content_type, content_data in req_body['content'].items():
                        if 'example' in content_data:
                            content.append(json.dumps(content_data['example'], indent=2))
                            break
                
                content.extend(["```", ""])
            
            # Réponses
            content.extend([
                "### Réponses",
                "",
                "| Code | Description |",
                "|------|-------------|"
            ])
            
            for status_code, response_data in endpoint['responses'].items():
                description = response_data.get('description', '')
                content.append(f"| {status_code} | {description} |")
            
            content.extend(["", "---", ""])
        
        # Écriture fichier
        with open(tag_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def _generate_api_index(self, endpoints_by_tag: Dict[str, List]):
        """Génération index API"""
        
        index_file = self.docs_dir / "index.md"
        
        content = [
            "# API Reference",
            "",
            "Documentation complète de l'API WakeDock.",
            "",
            "## Authentification",
            "",
            "L'API utilise l'authentification Bearer Token (JWT):",
            "",
            "```bash",
            "curl -H 'Authorization: Bearer YOUR_TOKEN' https://api.wakedock.io/v1/services",
            "```",
            "",
            "## Endpoints par catégorie",
            ""
        ]
        
        for tag, endpoints in endpoints_by_tag.items():
            content.extend([
                f"### {tag}",
                "",
                f"[Documentation détaillée](./{tag.lower().replace(' ', '-')}.md)",
                "",
                "| Endpoint | Méthode | Description |",
                "|----------|---------|-------------|"
            ])
            
            for endpoint in endpoints:
                path = endpoint['path']
                method = endpoint['method']
                summary = endpoint['summary']
                content.append(f"| `{path}` | {method} | {summary} |")
            
            content.append("")
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    
    def save_openapi_spec(self):
        """Sauvegarde spécification OpenAPI"""
        
        spec = self.generate_openapi_spec()
        
        # JSON pour tools
        with open(self.docs_dir / "openapi.json", 'w') as f:
            json.dump(spec, f, indent=2)
        
        # YAML pour lecture humaine
        import yaml
        with open(self.docs_dir / "openapi.yaml", 'w') as f:
            yaml.dump(spec, f, default_flow_style=False)

if __name__ == "__main__":
    generator = APIDocumentationGenerator(app)
    generator.generate_markdown_docs()
    generator.save_openapi_spec()
    print("✅ Documentation API générée avec succès")
```

---

## 🔧 PROCÉDURES MAINTENANCE

### 1. Maintenance Automatisée

```python
# scripts/maintenance/automated_maintenance.py
"""Scripts de maintenance automatisée WakeDock"""

import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import asyncpg
import aioredis
import psutil

class MaintenanceScheduler:
    """Planificateur maintenance automatique"""
    
    def __init__(self):
        self.maintenance_log = Path("logs/maintenance.log")
        self.maintenance_log.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=self.maintenance_log,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def daily_maintenance(self):
        """Maintenance quotidienne"""
        
        self.logger.info("🔧 Starting daily maintenance")
        
        tasks = [
            self.cleanup_old_logs(),
            self.optimize_database(),
            self.clear_cache(),
            self.check_disk_space(),
            self.update_system_metrics(),
            self.backup_configuration()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Rapport de maintenance
        self._generate_maintenance_report("daily", results)
    
    async def weekly_maintenance(self):
        """Maintenance hebdomadaire"""
        
        self.logger.info("🔧 Starting weekly maintenance")
        
        tasks = [
            self.vacuum_database(),
            self.rotate_logs(),
            self.cleanup_docker_images(),
            self.security_scan(),
            self.performance_analysis(),
            self.backup_database()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self._generate_maintenance_report("weekly", results)
    
    async def monthly_maintenance(self):
        """Maintenance mensuelle"""
        
        self.logger.info("🔧 Starting monthly maintenance")
        
        tasks = [
            self.full_database_backup(),
            self.security_audit(),
            self.dependency_updates_check(),
            self.capacity_planning_analysis(),
            self.documentation_review()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self._generate_maintenance_report("monthly", results)
    
    async def cleanup_old_logs(self) -> Dict[str, Any]:
        """Nettoyage anciens logs"""
        
        try:
            log_dirs = [Path("logs"), Path("var/log")]
            total_cleaned = 0
            
            for log_dir in log_dirs:
                if log_dir.exists():
                    cutoff_date = datetime.now() - timedelta(days=30)
                    
                    for log_file in log_dir.glob("*.log*"):
                        if log_file.stat().st_mtime < cutoff_date.timestamp():
                            file_size = log_file.stat().st_size
                            log_file.unlink()
                            total_cleaned += file_size
            
            return {
                "task": "cleanup_old_logs",
                "status": "success",
                "cleaned_bytes": total_cleaned,
                "cleaned_mb": round(total_cleaned / 1024 / 1024, 2)
            }
            
        except Exception as e:
            return {"task": "cleanup_old_logs", "status": "error", "error": str(e)}
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Optimisation base de données"""
        
        try:
            conn = await asyncpg.connect("postgresql://user:pass@localhost/wakedock")
            
            # Analyse et vacuum léger
            await conn.execute("ANALYZE;")
            
            # Stats avant optimisation
            stats_before = await conn.fetchrow("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
            """)
            
            # Réindexation si nécessaire
            await conn.execute("REINDEX INDEX CONCURRENTLY IF EXISTS idx_services_status_created;")
            
            # Stats après
            stats_after = await conn.fetchrow("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
            """)
            
            await conn.close()
            
            return {
                "task": "optimize_database",
                "status": "success",
                "stats_before": dict(stats_before),
                "stats_after": dict(stats_after)
            }
            
        except Exception as e:
            return {"task": "optimize_database", "status": "error", "error": str(e)}
    
    async def clear_cache(self) -> Dict[str, Any]:
        """Nettoyage cache Redis"""
        
        try:
            redis = await aioredis.from_url("redis://localhost:6379")
            
            # Statistiques avant
            info_before = await redis.info('memory')
            
            # Nettoyage clés expirées et pattern temporaires
            temp_keys = await redis.keys("temp:*")
            expired_keys = await redis.keys("cache:*:expired")
            
            if temp_keys:
                await redis.delete(*temp_keys)
            if expired_keys:
                await redis.delete(*expired_keys)
            
            # Force garbage collection
            await redis.execute_command("MEMORY PURGE")
            
            # Statistiques après
            info_after = await redis.info('memory')
            
            await redis.close()
            
            return {
                "task": "clear_cache",
                "status": "success",
                "memory_before_mb": round(info_before['used_memory'] / 1024 / 1024, 2),
                "memory_after_mb": round(info_after['used_memory'] / 1024 / 1024, 2),
                "keys_cleaned": len(temp_keys) + len(expired_keys)
            }
            
        except Exception as e:
            return {"task": "clear_cache", "status": "error", "error": str(e)}
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Vérification espace disque"""
        
        try:
            disk_usage = psutil.disk_usage('/')
            
            total_gb = round(disk_usage.total / 1024**3, 2)
            free_gb = round(disk_usage.free / 1024**3, 2)
            used_gb = round(disk_usage.used / 1024**3, 2)
            usage_percent = round((disk_usage.used / disk_usage.total) * 100, 1)
            
            # Alerte si >85% utilisé
            alert_level = "critical" if usage_percent > 85 else "warning" if usage_percent > 70 else "ok"
            
            return {
                "task": "check_disk_space",
                "status": "success",
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "usage_percent": usage_percent,
                "alert_level": alert_level
            }
            
        except Exception as e:
            return {"task": "check_disk_space", "status": "error", "error": str(e)}
    
    async def cleanup_docker_images(self) -> Dict[str, Any]:
        """Nettoyage images Docker inutilisées"""
        
        try:
            # Nettoyage images danglingte, unused networks, build cache
            result = subprocess.run([
                "docker", "system", "prune", "-f", "--volumes"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parser la sortie pour extraire l'espace libéré
                output = result.stdout
                return {
                    "task": "cleanup_docker_images",
                    "status": "success",
                    "output": output,
                    "space_reclaimed": self._parse_docker_prune_output(output)
                }
            else:
                return {
                    "task": "cleanup_docker_images",
                    "status": "error",
                    "error": result.stderr
                }
                
        except Exception as e:
            return {"task": "cleanup_docker_images", "status": "error", "error": str(e)}
    
    def _parse_docker_prune_output(self, output: str) -> str:
        """Parser sortie docker prune"""
        
        lines = output.strip().split('\n')
        for line in lines:
            if "Total reclaimed space:" in line:
                return line.split(":")[-1].strip()
        return "Unknown"
    
    async def backup_configuration(self) -> Dict[str, Any]:
        """Sauvegarde configuration"""
        
        try:
            backup_dir = Path("backups/config")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"config_backup_{timestamp}.tar.gz"
            
            # Sauvegarde fichiers configuration
            config_files = [
                "docker-compose.yml",
                "docker-compose.override.yml", 
                ".env",
                "caddy/Caddyfile",
                "nginx/nginx.conf"
            ]
            
            existing_files = [f for f in config_files if Path(f).exists()]
            
            if existing_files:
                subprocess.run([
                    "tar", "-czf", str(backup_file)
                ] + existing_files, check=True)
                
                file_size = backup_file.stat().st_size
                
                return {
                    "task": "backup_configuration",
                    "status": "success",
                    "backup_file": str(backup_file),
                    "files_backed_up": len(existing_files),
                    "backup_size_bytes": file_size
                }
            else:
                return {
                    "task": "backup_configuration",
                    "status": "warning",
                    "message": "No configuration files found to backup"
                }
                
        except Exception as e:
            return {"task": "backup_configuration", "status": "error", "error": str(e)}
    
    def _generate_maintenance_report(self, maintenance_type: str, results: List[Any]):
        """Génération rapport maintenance"""
        
        report_file = Path(f"reports/maintenance_{maintenance_type}_{datetime.now().strftime('%Y%m%d')}.md")
        report_file.parent.mkdir(exist_ok=True)
        
        successful_tasks = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        failed_tasks = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]
        warning_tasks = [r for r in results if isinstance(r, dict) and r.get("status") == "warning"]
        
        content = [
            f"# Rapport Maintenance {maintenance_type.title()}",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Résumé",
            f"- ✅ Tâches réussies: {len(successful_tasks)}",
            f"- ⚠️ Tâches avec avertissement: {len(warning_tasks)}", 
            f"- ❌ Tâches échouées: {len(failed_tasks)}",
            "",
            "## Détails des tâches",
            ""
        ]
        
        for result in results:
            if isinstance(result, dict):
                task_name = result.get("task", "Unknown")
                status = result.get("status", "unknown")
                
                status_emoji = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(status, "❓")
                
                content.extend([
                    f"### {status_emoji} {task_name}",
                    f"**Statut:** {status}",
                    ""
                ])
                
                if status == "success":
                    # Détails spécifiques selon la tâche
                    if task_name == "cleanup_old_logs":
                        content.append(f"**Espace libéré:** {result.get('cleaned_mb', 0)} MB")
                    elif task_name == "check_disk_space":
                        content.extend([
                            f"**Utilisation disque:** {result.get('usage_percent')}%",
                            f"**Espace libre:** {result.get('free_gb')} GB",
                            f"**Niveau d'alerte:** {result.get('alert_level')}"
                        ])
                    elif task_name == "clear_cache":
                        content.extend([
                            f"**Mémoire avant:** {result.get('memory_before_mb')} MB",
                            f"**Mémoire après:** {result.get('memory_after_mb')} MB",
                            f"**Clés nettoyées:** {result.get('keys_cleaned')}"
                        ])
                
                elif status == "error":
                    content.append(f"**Erreur:** {result.get('error', 'Unknown error')}")
                
                content.append("")
        
        # Écriture rapport
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        self.logger.info(f"📊 Rapport de maintenance généré: {report_file}")

# Cron job configuration
# /etc/cron.d/wakedock-maintenance

# Daily maintenance at 2 AM
0 2 * * * wakedock cd /opt/wakedock && python scripts/maintenance/automated_maintenance.py daily

# Weekly maintenance on Sunday at 3 AM  
0 3 * * 0 wakedock cd /opt/wakedock && python scripts/maintenance/automated_maintenance.py weekly

# Monthly maintenance on 1st day at 4 AM
0 4 1 * * wakedock cd /opt/wakedock && python scripts/maintenance/automated_maintenance.py monthly
```

---

### 2. Runbooks Opérationnels

```markdown
# docs/operations/runbooks/incident-response.md

# 🚨 Guide de Réponse aux Incidents

## Processus de Réponse

### Étape 1: Détection et Évaluation (0-5 minutes)

1. **Réception alerte**
   - Source: Monitoring, utilisateur, système
   - Vérifier authenticité de l'alerte
   - Évaluer gravité initiale

2. **Classification gravité**
   - **P0 (Critique):** Service complètement indisponible
   - **P1 (Haute):** Fonctionnalité majeure indisponible  
   - **P2 (Moyenne):** Dégradation performance
   - **P3 (Faible):** Problème mineur

### Étape 2: Réponse Immédiate (5-15 minutes)

#### Pour P0/P1 - Escalade immédiate
```bash
# 1. Notification équipe
curl -X POST "$SLACK_WEBHOOK" -d '{
  "text": "🚨 INCIDENT P0: WakeDock service down",
  "channel": "#incidents",
  "username": "AlertBot"
}'

# 2. Status page update
curl -X POST "https://api.statuspage.io/v1/pages/$PAGE_ID/incidents" \
  -H "Authorization: OAuth $STATUS_PAGE_TOKEN" \
  -d '{
    "incident": {
      "name": "Service Unavailability",
      "status": "investigating",
      "impact_override": "major"
    }
  }'
```

#### Vérifications initiales
```bash
# Statut services
docker-compose ps

# Logs récents  
docker-compose logs --tail=100 wakedock
docker-compose logs --tail=100 postgres
docker-compose logs --tail=100 redis

# Métriques système
top
df -h
free -m
```

### Étape 3: Investigation (15-30 minutes)

#### Check-list investigation

- [ ] **Services Docker**
  ```bash
  docker ps -a
  docker-compose ps
  docker stats
  ```

- [ ] **Base de données**
  ```bash
  # Connexion DB
  docker-compose exec postgres psql -U postgres -d wakedock
  
  # Vérifier connexions actives
  SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
  
  # Vérifier locks
  SELECT * FROM pg_locks WHERE NOT granted;
  ```

- [ ] **Réseau et connectivité**
  ```bash
  # Test connectivité interne
  docker-compose exec wakedock ping postgres
  docker-compose exec wakedock ping redis
  
  # Test endpoints
  curl -f http://localhost:8000/health
  curl -f http://localhost:3000/health
  ```

- [ ] **Ressources système**
  ```bash
  # CPU et mémoire
  htop
  
  # Espace disque
  df -h
  lsof | grep docker
  
  # Logs système
  journalctl -u docker --since "1 hour ago"
  ```

### Étape 4: Résolution (Variables selon incident)

#### Problèmes courants et solutions

##### Service WakeDock ne démarre pas
```bash
# 1. Vérifier logs détaillés
docker-compose logs wakedock

# 2. Variables d'environnement
docker-compose config

# 3. Redémarrage propre
docker-compose down
docker-compose up -d

# 4. Si échec persistant - rebuild
docker-compose down
docker-compose build --no-cache wakedock
docker-compose up -d
```

##### Base de données corrompue/lente
```bash
# 1. Vérifier intégrité
docker-compose exec postgres pg_dump --schema-only wakedock > schema_backup.sql

# 2. Vérifier performances
docker-compose exec postgres psql -U postgres -d wakedock -c "
  SELECT query, calls, total_time, mean_time 
  FROM pg_stat_statements 
  ORDER BY total_time DESC LIMIT 10;
"

# 3. Vacuum si nécessaire
docker-compose exec postgres psql -U postgres -d wakedock -c "VACUUM ANALYZE;"

# 4. Redémarrage si nécessaire
docker-compose restart postgres
```

##### Problème réseau/proxy
```bash
# 1. Vérifier configuration Caddy
docker-compose exec caddy cat /etc/caddy/Caddyfile

# 2. Test configuration
docker-compose exec caddy caddy validate --config /etc/caddy/Caddyfile

# 3. Reload configuration
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile

# 4. Redémarrage si nécessaire
docker-compose restart caddy
```

### Étape 5: Communication (Continu)

#### Templates communication

**Début incident:**
```
🚨 INCIDENT EN COURS
Nous enquêtons actuellement sur un problème affectant [service].
Temps de résolution estimé: [X] minutes
Prochaine mise à jour dans 15 minutes.
```

**Mise à jour:**
```
📊 MISE À JOUR INCIDENT
Cause identifiée: [description]
Action en cours: [action]
Progression: [%]
Prochaine mise à jour dans 15 minutes.
```

**Résolution:**
```
✅ INCIDENT RÉSOLU
Le problème a été résolu à [heure].
Cause: [description]
Actions prises: [description]
Post-mortem disponible dans 24h.
```

### Étape 6: Post-Incident (24-48h après)

#### Post-mortem obligatoire pour P0/P1

1. **Timeline détaillée**
2. **Cause racine**
3. **Impact utilisateurs**
4. **Actions correctives**
5. **Prévention futures**

#### Template post-mortem
```markdown
# Post-Mortem: [Titre incident]

## Résumé
- **Date:** [Date]
- **Durée:** [X] heures [Y] minutes
- **Impact:** [Description]
- **Gravité:** P[X]

## Timeline
| Heure | Événement |
|-------|-----------|
| XX:XX | Incident détecté |
| XX:XX | Équipe notifiée |
| XX:XX | Investigation débutée |
| XX:XX | Cause identifiée |
| XX:XX | Résolution appliquée |
| XX:XX | Service restauré |

## Cause Racine
[Description détaillée]

## Impact
- **Utilisateurs affectés:** [nombre]
- **Services impactés:** [liste]
- **Perte estimée:** [métrique business]

## Actions Immédiates Prises
1. [Action 1]
2. [Action 2]
3. [Action 3]

## Actions Préventives
| Action | Propriétaire | Échéance | Statut |
|--------|--------------|----------|---------|
| [Action] | [Nom] | [Date] | [ ] |

## Leçons Apprises
1. [Leçon 1]
2. [Leçon 2]
3. [Leçon 3]
```

---

## 📈 Métriques et Monitoring Documentation

### Dashboard Performance Documentation
```bash
# Métriques à surveiller quotidiennement
watch -n 30 'echo "=== SYSTEM OVERVIEW ==="; \
docker stats --no-stream; \
echo -e "\n=== DISK USAGE ==="; \
df -h; \
echo -e "\n=== DATABASE CONNECTIONS ==="; \
docker-compose exec postgres psql -U postgres -d wakedock -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = '\''active'\'';"'
```

### Alerting Configuration
```yaml
# prometheus/alerts.yml
groups:
  - name: wakedock.alerts
    rules:
      - alert: ServiceDown
        expr: up{job="wakedock"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "WakeDock service is down"
          description: "WakeDock service has been down for more than 1 minute"
      
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 90% for more than 5 minutes"
      
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count{state="active"} > 50
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"
          description: "More than 50 active database connections detected"
```
```

---

## 🚀 PLAN D'EXÉCUTION DOCUMENTATION

### Phase 1 - Documentation Core (Semaine 1)
- [ ] Setup infrastructure docs (MkDocs, automation)
- [ ] Documentation API automatique complète
- [ ] Guides utilisateur essentiels
- [ ] Runbooks incidents critiques

### Phase 2 - Procédures Maintenance (Semaine 1-2)
- [ ] Scripts maintenance automatisée
- [ ] Cron jobs et scheduling
- [ ] Monitoring et alerting documentation
- [ ] Procédures backup/restore

### Phase 3 - Documentation Développeur (Semaine 2)
- [ ] Guides contribution et développement
- [ ] Architecture et design docs
- [ ] Documentation déploiement
- [ ] Guidelines code et testing

### Phase 4 - Finalisation (Semaine 2)
- [ ] Review et validation documentation
- [ ] Traduction éléments critiques
- [ ] Formation équipe sur procédures
- [ ] Mise en place processus maintenance continue

---

## 📊 MÉTRIQUES SUCCÈS DOCUMENTATION

```yaml
Documentation Quality:
  - Coverage: 100% workflows documentés
  - Accuracy: Validation mensuelle
  - Accessibility: Score accessibilité >95%
  - Usage: Analytics documentation active
  - Maintenance: Mise à jour automatique

Operational Excellence:
  - MTTR (Mean Time To Repair): <30 minutes
  - Incident Response Time: <5 minutes
  - Documentation Coverage: 100% procédures
  - Team Training: 100% équipe formée
  - Process Compliance: >95% procédures suivies
```

---

**📞 Contact:** Documentation Team  
**📅 Review:** Quarterly documentation review  
**🚨 Escalation:** Tech Lead pour gaps documentation critiques**