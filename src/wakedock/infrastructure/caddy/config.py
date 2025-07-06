"""
Caddy Configuration Manager

Gestion configuration Caddyfile et templates.
Extrait de la classe monolithique CaddyManager.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from datetime import datetime

from wakedock.config import get_settings
from wakedock.database.models import Service, ServiceStatus
from .types import ConfigValidation, BackupResult, RestoreResult

logger = logging.getLogger(__name__)


class CaddyConfigManager:
    """Gestionnaire de configuration Caddy"""
    
    def __init__(self):
        """Initialiser le gestionnaire de configuration"""
        self.settings = get_settings()
        
        # Déterminer le répertoire de configuration approprié
        self.config_path = self._get_config_path()
        self.templates_path = self.config_path.parent / "templates"
        self.backups_path = self.config_path.parent / "backups"
        
        # Créer les répertoires nécessaires
        self._ensure_directories()
        
        # Initialiser Jinja2
        self._setup_jinja()
        
        # S'assurer que le Caddyfile initial existe
        self._ensure_initial_caddyfile()
    
    def _get_config_path(self) -> Path:
        """Déterminer le chemin de configuration Caddy approprié"""
        # Ordre de priorité pour les répertoires de configuration
        potential_paths = [
            Path("/etc/caddy/Caddyfile"),  # Standard Docker location
            Path("/app/config/caddy/Caddyfile"),  # Application config
            Path("/tmp/caddy/Caddyfile"),  # Fallback temporaire
        ]
        
        for path in potential_paths:
            try:
                # Tester la création du répertoire
                path.parent.mkdir(parents=True, exist_ok=True)
                # Tester l'écriture
                test_file = path.parent / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                
                logger.info(f"Using Caddy config path: {path}")
                return path
                
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot use {path.parent}: {e}")
                continue
        
        # Si tous échouent, utiliser le répertoire temporaire 
        fallback_path = Path("/tmp/wakedock/caddy/Caddyfile")
        logger.warning(f"Using fallback config path: {fallback_path}")
        return fallback_path
    
    def _ensure_directories(self) -> None:
        """Créer les répertoires nécessaires"""
        for path in [self.config_path.parent, self.templates_path, self.backups_path]:
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {path}")
            except (PermissionError, OSError) as e:
                logger.warning(f"Could not create directory {path}: {e}")
                # Les répertoires seront créés lors de l'accès si possible
    
    def _setup_jinja(self) -> None:
        """Configurer l'environnement Jinja2"""
        if self.templates_path.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_path)),
                autoescape=False,  # Caddy config n'est pas HTML
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            # Environnement de base
            self.jinja_env = Environment(loader=FileSystemLoader("."))
            
        # Ajouter des fonctions utiles aux templates
        self.jinja_env.globals.update({
            'now': datetime.now,
            'env': os.environ.get
        })
    
    def _ensure_initial_caddyfile(self) -> None:
        """S'assurer que le Caddyfile initial existe"""
        try:
            # Vérifier si le chemin est un répertoire (erreur commune)
            if self.config_path.exists() and self.config_path.is_dir():
                logger.warning(f"Caddyfile path is a directory, removing: {self.config_path}")
                self.config_path.rmdir()
            
            # Créer le Caddyfile de base s'il n'existe pas
            if not self.config_path.exists():
                initial_config = self._generate_base_config()
                self.config_path.write_text(initial_config)
                logger.info(f"Created initial Caddyfile at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Failed to ensure initial Caddyfile: {e}")
            raise
    
    def _generate_base_config(self) -> str:
        """Générer la configuration Caddy de base"""
        return """# WakeDock Caddy Configuration
# Auto-generated base configuration

# Global options
{
    admin 0.0.0.0:2019
    auto_https off
}

# Default site - WakeDock dashboard
:80 {
    # Health check endpoint
    handle /health {
        respond "OK" 200
    }
    
    # Default fallback
    handle {
        respond "WakeDock - Service not found or not configured" 404
    }
}

# Import dynamic service configurations
import /etc/caddy/services/*.caddy
"""
    
    async def generate_config(self, services: List[Service]) -> str:
        """Générer la configuration complète pour les services"""
        try:
            # Charger le template principal
            template = self._get_main_template()
            
            # Préparer les données pour le template
            template_data = {
                'services': [self._service_to_dict(service) for service in services],
                'settings': self.settings,
                'timestamp': datetime.now().isoformat(),
                'admin_port': getattr(self.settings.caddy, 'admin_port', 2019)
            }
            
            # Générer la configuration
            config = template.render(**template_data)
            
            logger.info(f"Generated Caddy config for {len(services)} services")
            return config
            
        except Exception as e:
            logger.error(f"Failed to generate Caddy config: {e}")
            raise
    
    def _get_main_template(self) -> Template:
        """Récupérer le template principal"""
        template_file = "Caddyfile.j2"
        
        try:
            # Essayer de charger depuis le répertoire templates
            return self.jinja_env.get_template(template_file)
        except:
            # Fallback vers template intégré
            return self.jinja_env.from_string(self._get_default_template())
    
    def _get_default_template(self) -> str:
        """Template par défaut intégré"""
        return """# WakeDock Caddy Configuration
# Generated: {{ timestamp }}

# Global options
{
    admin 0.0.0.0:{{ admin_port }}
    auto_https off
}

# Health check and default
:80 {
    handle /health {
        respond "OK" 200
    }
    
    handle {
        respond "WakeDock - Service not found" 404
    }
}

{% for service in services %}
{% if service.domain and service.status == 'running' %}
# Service: {{ service.name }}
{{ service.domain }} {
    reverse_proxy {{ service.upstream }}
    
    # Headers sécurité
    header {
        X-Frame-Options DENY
        X-Content-Type-Options nosniff
        X-XSS-Protection "1; mode=block"
    }
    
    {% if service.tls %}
    tls internal
    {% endif %}
}
{% endif %}
{% endfor %}
"""
    
    def _service_to_dict(self, service: Service) -> Dict:
        """Convertir un service en dictionnaire pour template"""
        return {
            'name': service.name,
            'domain': getattr(service, 'domain', None),
            'upstream': f"http://wakedock-{service.name}:8000",  # Convention WakeDock
            'status': service.status.value if hasattr(service.status, 'value') else str(service.status),
            'tls': True,
            'headers': {
                'X-Forwarded-For': '{remote}',
                'X-Forwarded-Proto': '{scheme}'
            }
        }
    
    async def validate_config(self, config: str) -> ConfigValidation:
        """Valider une configuration Caddy"""
        errors = []
        warnings = []
        
        try:
            # Validation basique de syntaxe
            if not config.strip():
                errors.append("Configuration is empty")
                return ConfigValidation(False, errors, warnings)
            
            # Vérifier les accolades
            open_braces = config.count('{')
            close_braces = config.count('}')
            if open_braces != close_braces:
                errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
            
            # Vérifier les directives obligatoires
            if 'admin' not in config:
                warnings.append("No admin directive found")
            
            # Vérifier les ports en conflit
            if config.count(':80') > 1:
                errors.append("Multiple listeners on port 80")
            
            is_valid = len(errors) == 0
            
            logger.info(f"Config validation: {'valid' if is_valid else 'invalid'}, "
                       f"{len(errors)} errors, {len(warnings)} warnings")
            
            return ConfigValidation(is_valid, errors, warnings)
            
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            errors.append(f"Validation error: {str(e)}")
            return ConfigValidation(False, errors, warnings)
    
    async def backup_config(self) -> BackupResult:
        """Sauvegarder la configuration actuelle"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"caddyfile_backup_{timestamp}"
            backup_path = self.backups_path / f"{backup_id}.bak"
            
            # Lire la configuration actuelle
            if not self.config_path.exists():
                raise FileNotFoundError(f"Caddyfile not found: {self.config_path}")
            
            current_config = self.config_path.read_text()
            
            # Sauvegarder
            backup_path.write_text(current_config)
            
            logger.info(f"Backed up Caddyfile to {backup_path}")
            
            return BackupResult(
                backup_id=backup_id,
                backup_path=str(backup_path),
                timestamp=timestamp,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to backup config: {e}")
            return BackupResult(
                backup_id="",
                backup_path="",
                timestamp="",
                success=False,
                error=str(e)
            )
    
    async def restore_config(self, backup_id: str) -> RestoreResult:
        """Restaurer une configuration depuis une sauvegarde"""
        try:
            backup_path = self.backups_path / f"{backup_id}.bak"
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")
            
            # Lire la sauvegarde
            backup_config = backup_path.read_text()
            
            # Valider avant restauration
            validation = await self.validate_config(backup_config)
            if not validation.is_valid:
                raise ValueError(f"Backup config is invalid: {validation.errors}")
            
            # Sauvegarder la config actuelle avant restauration
            await self.backup_config()
            
            # Restaurer
            self.config_path.write_text(backup_config)
            
            logger.info(f"Restored config from backup {backup_id}")
            
            return RestoreResult(
                success=True,
                backup_id=backup_id
            )
            
        except Exception as e:
            logger.error(f"Failed to restore config from {backup_id}: {e}")
            return RestoreResult(
                success=False,
                backup_id=backup_id,
                error=str(e)
            )
    
    async def save_config(self, config: str, validate: bool = True) -> bool:
        """Sauvegarder une nouvelle configuration"""
        try:
            if validate:
                validation = await self.validate_config(config)
                if not validation.is_valid:
                    raise ValueError(f"Invalid config: {validation.errors}")
            
            # Backup avant modification
            await self.backup_config()
            
            # Sauvegarder la nouvelle config
            self.config_path.write_text(config)
            
            logger.info("Saved new Caddy configuration")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get_current_config(self) -> Optional[str]:
        """Récupérer la configuration actuelle"""
        try:
            if self.config_path.exists():
                return self.config_path.read_text()
            return None
        except Exception as e:
            logger.error(f"Failed to read current config: {e}")
            return None
    
    def list_backups(self) -> List[Dict]:
        """Lister les sauvegardes disponibles"""
        try:
            backups = []
            for backup_file in self.backups_path.glob("*.bak"):
                stat = backup_file.stat()
                backups.append({
                    'id': backup_file.stem,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            
            # Trier par date de création (plus récent en premier)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []