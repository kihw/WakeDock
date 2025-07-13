"""
Configuration Service for WakeDock maintenance operations
"""

import json
import yaml
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from jsonschema import validate, ValidationError

from wakedock.config import get_settings
from wakedock.utils.formatting import FormattingUtils


class ConfigService:
    """Service for managing system configuration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.app_root = Path("/app")
        self.config_dir = self.app_root / "config"
        self.backup_dir = self.app_root / "config_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.schema_file = self.config_dir / "config.schema.json"
        self._last_validation = None
        self._last_status = "unknown"
    
    async def validate_configuration(self, config_type: str = "all") -> Dict[str, Any]:
        """Validate system configuration"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "validation_type": config_type,
            "overall_status": "valid",
            "validations": {},
            "errors": [],
            "warnings": []
        }
        
        if config_type in ["all", "main"]:
            main_config = await self._validate_main_config()
            results["validations"]["main_config"] = main_config
        
        if config_type in ["all", "docker"]:
            docker_config = await self._validate_docker_config()
            results["validations"]["docker_config"] = docker_config
        
        if config_type in ["all", "caddy"]:
            caddy_config = await self._validate_caddy_config()
            results["validations"]["caddy_config"] = caddy_config
        
        if config_type in ["all", "database"]:
            database_config = await self._validate_database_config()
            results["validations"]["database_config"] = database_config
        
        if config_type in ["all", "security"]:
            security_config = await self._validate_security_config()
            results["validations"]["security_config"] = security_config
        
        # Aggregate results
        all_errors = []
        all_warnings = []
        
        for validation in results["validations"].values():
            if validation.get("errors"):
                all_errors.extend(validation["errors"])
            if validation.get("warnings"):
                all_warnings.extend(validation["warnings"])
        
        results["errors"] = all_errors
        results["warnings"] = all_warnings
        
        if all_errors:
            results["overall_status"] = "invalid"
        elif all_warnings:
            results["overall_status"] = "valid_with_warnings"
        
        return results
    
    async def _validate_main_config(self) -> Dict[str, Any]:
        """Validate main configuration file"""
        
        config_file = self.config_dir / "config.yml"
        
        if not config_file.exists():
            return {
                "status": "error",
                "errors": ["Main configuration file config.yml not found"],
                "warnings": []
            }
        
        try:
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
            
            errors = []
            warnings = []
            
            # Validate schema if available
            if self.schema_file.exists():
                try:
                    with open(self.schema_file) as f:
                        schema = json.load(f)
                    
                    validate(instance=config_data, schema=schema)
                    
                except ValidationError as e:
                    errors.append(f"Schema validation failed: {e.message}")
                except Exception as e:
                    warnings.append(f"Could not validate schema: {str(e)}")
            
            # Validate required sections
            required_sections = ["api", "database", "docker", "security"]
            for section in required_sections:
                if section not in config_data:
                    errors.append(f"Missing required section: {section}")
            
            # Validate API configuration
            if "api" in config_data:
                api_config = config_data["api"]
                if "host" not in api_config:
                    warnings.append("API host not configured, using default")
                if "port" not in api_config:
                    warnings.append("API port not configured, using default")
            
            # Validate database configuration
            if "database" in config_data:
                db_config = config_data["database"]
                if "url" not in db_config and "host" not in db_config:
                    errors.append("Database URL or host must be configured")
            
            # Validate Docker configuration
            if "docker" in config_data:
                docker_config = config_data["docker"]
                if "socket_path" in docker_config:
                    socket_path = Path(docker_config["socket_path"])
                    if not socket_path.exists():
                        warnings.append(f"Docker socket path does not exist: {socket_path}")
            
            status = "error" if errors else ("warning" if warnings else "valid")
            
            return {
                "status": status,
                "config_file": str(config_file),
                "config_data": config_data,
                "errors": errors,
                "warnings": warnings
            }
            
        except yaml.YAMLError as e:
            return {
                "status": "error",
                "config_file": str(config_file),
                "errors": [f"YAML parsing error: {str(e)}"],
                "warnings": []
            }
        except Exception as e:
            return {
                "status": "error",
                "config_file": str(config_file),
                "errors": [f"Configuration validation failed: {str(e)}"],
                "warnings": []
            }
    
    async def _validate_docker_config(self) -> Dict[str, Any]:
        """Validate Docker Compose configuration"""
        
        compose_files = [
            self.app_root / "docker-compose.yml",
            self.app_root / "docker-compose.prod.yml",
            self.app_root / "docker-compose.dev.yml"
        ]
        
        results = {
            "status": "valid",
            "files": {},
            "errors": [],
            "warnings": []
        }
        
        for compose_file in compose_files:
            if not compose_file.exists():
                if compose_file.name == "docker-compose.yml":
                    results["errors"].append(f"Required file missing: {compose_file.name}")
                else:
                    results["warnings"].append(f"Optional file missing: {compose_file.name}")
                continue
            
            try:
                with open(compose_file) as f:
                    compose_data = yaml.safe_load(f)
                
                file_errors = []
                file_warnings = []
                
                # Validate Docker Compose version
                if "version" not in compose_data:
                    file_warnings.append("Docker Compose version not specified")
                elif compose_data["version"] < "3.0":
                    file_warnings.append("Old Docker Compose version, consider upgrading")
                
                # Validate services
                if "services" not in compose_data:
                    file_errors.append("No services defined in Docker Compose file")
                else:
                    services = compose_data["services"]
                    
                    # Check for required services
                    required_services = ["wakedock-core", "wakedock-postgres"]
                    for service in required_services:
                        if service not in services:
                            file_errors.append(f"Required service missing: {service}")
                    
                    # Validate service configurations
                    for service_name, service_config in services.items():
                        # Check for health checks
                        if "healthcheck" not in service_config:
                            file_warnings.append(f"Service {service_name} has no health check")
                        
                        # Check for restart policies
                        if "restart" not in service_config:
                            file_warnings.append(f"Service {service_name} has no restart policy")
                        
                        # Check for resource limits
                        if "deploy" not in service_config and "mem_limit" not in service_config:
                            file_warnings.append(f"Service {service_name} has no resource limits")
                
                # Validate networks
                if "networks" in compose_data:
                    networks = compose_data["networks"]
                    if not networks:
                        file_warnings.append("Networks section is empty")
                
                # Validate volumes
                if "volumes" in compose_data:
                    volumes = compose_data["volumes"]
                    for volume_name, volume_config in volumes.items():
                        if volume_config is None:
                            file_warnings.append(f"Volume {volume_name} has no configuration")
                
                results["files"][compose_file.name] = {
                    "status": "error" if file_errors else ("warning" if file_warnings else "valid"),
                    "path": str(compose_file),
                    "errors": file_errors,
                    "warnings": file_warnings
                }
                
                results["errors"].extend(file_errors)
                results["warnings"].extend(file_warnings)
                
            except yaml.YAMLError as e:
                error_msg = f"YAML parsing error in {compose_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                results["files"][compose_file.name] = {
                    "status": "error",
                    "path": str(compose_file),
                    "errors": [error_msg],
                    "warnings": []
                }
            except Exception as e:
                error_msg = f"Validation error in {compose_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                results["files"][compose_file.name] = {
                    "status": "error",
                    "path": str(compose_file),
                    "errors": [error_msg],
                    "warnings": []
                }
        
        if results["errors"]:
            results["status"] = "error"
        elif results["warnings"]:
            results["status"] = "warning"
        
        return results
    
    async def _validate_caddy_config(self) -> Dict[str, Any]:
        """Validate Caddy configuration"""
        
        caddy_files = [
            self.app_root / "caddy" / "Caddyfile.compose",
            self.app_root / "caddy" / "Caddyfile.prod"
        ]
        
        results = {
            "status": "valid",
            "files": {},
            "errors": [],
            "warnings": []
        }
        
        for caddy_file in caddy_files:
            if not caddy_file.exists():
                results["warnings"].append(f"Caddy file missing: {caddy_file.name}")
                continue
            
            try:
                with open(caddy_file) as f:
                    caddy_content = f.read()
                
                file_errors = []
                file_warnings = []
                
                # Basic Caddyfile validation
                lines = caddy_content.strip().split('\n')
                
                # Check for basic syntax
                brace_count = 0
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    brace_count += line.count('{')
                    brace_count -= line.count('}')
                    
                    # Check for common directives
                    if line.startswith('reverse_proxy'):
                        if 'localhost' in line:
                            file_warnings.append(f"Line {line_num}: Using localhost in reverse_proxy, consider using container names")
                
                if brace_count != 0:
                    file_errors.append("Mismatched braces in Caddyfile")
                
                # Check for HTTPS configuration
                if "tls" not in caddy_content and "https://" not in caddy_content:
                    file_warnings.append("No explicit TLS/HTTPS configuration found")
                
                # Check for security headers
                security_headers = ["Strict-Transport-Security", "X-Content-Type-Options", "X-Frame-Options"]
                missing_headers = []
                for header in security_headers:
                    if header not in caddy_content:
                        missing_headers.append(header)
                
                if missing_headers:
                    file_warnings.append(f"Missing security headers: {', '.join(missing_headers)}")
                
                results["files"][caddy_file.name] = {
                    "status": "error" if file_errors else ("warning" if file_warnings else "valid"),
                    "path": str(caddy_file),
                    "errors": file_errors,
                    "warnings": file_warnings
                }
                
                results["errors"].extend(file_errors)
                results["warnings"].extend(file_warnings)
                
            except Exception as e:
                error_msg = f"Validation error in {caddy_file.name}: {str(e)}"
                results["errors"].append(error_msg)
                results["files"][caddy_file.name] = {
                    "status": "error",
                    "path": str(caddy_file),
                    "errors": [error_msg],
                    "warnings": []
                }
        
        if results["errors"]:
            results["status"] = "error"
        elif results["warnings"]:
            results["status"] = "warning"
        
        return results
    
    async def _validate_database_config(self) -> Dict[str, Any]:
        """Validate database configuration"""
        
        results = {
            "status": "valid",
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check database connection settings
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                results["warnings"].append("DATABASE_URL environment variable not set")
            
            # Check for required database environment variables
            required_db_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
            for var in required_db_vars:
                if not os.getenv(var):
                    results["warnings"].append(f"Database environment variable not set: {var}")
            
            # Check database initialization scripts
            db_scripts_dir = self.app_root / "scripts"
            init_script = db_scripts_dir / "init-db.sql"
            
            if not init_script.exists():
                results["warnings"].append("Database initialization script not found")
            
            # Check Alembic configuration
            alembic_ini = self.app_root / "alembic.ini"
            if not alembic_ini.exists():
                results["warnings"].append("Alembic configuration file not found")
            else:
                try:
                    with open(alembic_ini) as f:
                        alembic_content = f.read()
                    
                    if "sqlalchemy.url" not in alembic_content:
                        results["warnings"].append("Alembic database URL not configured")
                except Exception as e:
                    results["warnings"].append(f"Could not read Alembic configuration: {str(e)}")
            
            # Check migrations directory
            migrations_dir = self.app_root / "alembic" / "versions"
            if migrations_dir.exists():
                migration_files = list(migrations_dir.glob("*.py"))
                if not migration_files:
                    results["warnings"].append("No database migrations found")
            else:
                results["warnings"].append("Database migrations directory not found")
            
        except Exception as e:
            results["errors"].append(f"Database configuration validation failed: {str(e)}")
        
        if results["errors"]:
            results["status"] = "error"
        elif results["warnings"]:
            results["status"] = "warning"
        
        return results
    
    async def _validate_security_config(self) -> Dict[str, Any]:
        """Validate security configuration"""
        
        results = {
            "status": "valid",
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check JWT configuration
            jwt_secret = os.getenv("JWT_SECRET_KEY")
            if not jwt_secret:
                results["errors"].append("JWT_SECRET_KEY environment variable not set")
            elif len(jwt_secret) < 32:
                results["warnings"].append("JWT secret key is too short (< 32 characters)")
            
            # Check encryption key
            encryption_key = os.getenv("ENCRYPTION_KEY")
            if not encryption_key:
                results["warnings"].append("ENCRYPTION_KEY environment variable not set")
            
            # Check CORS configuration
            cors_origins = os.getenv("CORS_ORIGINS")
            if not cors_origins:
                results["warnings"].append("CORS_ORIGINS not configured")
            elif "*" in cors_origins:
                results["warnings"].append("CORS allows all origins (*) - security risk")
            
            # Check SSL/TLS configuration
            ssl_cert = os.getenv("SSL_CERT_PATH")
            ssl_key = os.getenv("SSL_KEY_PATH")
            
            if ssl_cert and ssl_key:
                cert_path = Path(ssl_cert)
                key_path = Path(ssl_key)
                
                if not cert_path.exists():
                    results["errors"].append(f"SSL certificate file not found: {ssl_cert}")
                if not key_path.exists():
                    results["errors"].append(f"SSL key file not found: {ssl_key}")
            else:
                results["warnings"].append("SSL certificate/key not configured")
            
            # Check security headers configuration
            security_headers = [
                "SECURITY_HEADERS_ENABLED",
                "HSTS_MAX_AGE",
                "CSP_POLICY"
            ]
            
            for header in security_headers:
                if not os.getenv(header):
                    results["warnings"].append(f"Security header not configured: {header}")
            
            # Check rate limiting configuration
            rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED")
            if not rate_limit_enabled or rate_limit_enabled.lower() != "true":
                results["warnings"].append("Rate limiting not enabled")
            
            # Check session configuration
            session_timeout = os.getenv("SESSION_TIMEOUT_MINUTES")
            if not session_timeout:
                results["warnings"].append("Session timeout not configured")
            elif int(session_timeout) > 1440:  # 24 hours
                results["warnings"].append("Session timeout is very long (> 24 hours)")
            
        except Exception as e:
            results["errors"].append(f"Security configuration validation failed: {str(e)}")
        
        if results["errors"]:
            results["status"] = "error"
        elif results["warnings"]:
            results["status"] = "warning"
        
        return results
    
    async def backup_configuration(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a backup of all configuration files"""
        
        if not backup_name:
            backup_name = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.app_root / "backups" / "config" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            files_backed_up = []
            
            # Configuration files to backup
            config_files = [
                self.config_dir / "config.yml",
                self.config_dir / "config.dev.yml",
                self.config_dir / "config.prod.yml",
                self.config_dir / "logging.yml",
                self.config_dir / "secrets.yml",
                self.app_root / "docker-compose.yml",
                self.app_root / "docker-compose.prod.yml",
                self.app_root / "docker-compose.dev.yml",
                self.app_root / "alembic.ini",
                self.app_root / ".env"
            ]
            
            # Backup Caddy configuration
            caddy_dir = self.app_root / "caddy"
            if caddy_dir.exists():
                caddy_backup_dir = backup_dir / "caddy"
                shutil.copytree(caddy_dir, caddy_backup_dir, dirs_exist_ok=True)
                files_backed_up.append("caddy/")
            
            # Backup individual config files
            for config_file in config_files:
                if config_file.exists():
                    dest_file = backup_dir / config_file.name
                    shutil.copy2(config_file, dest_file)
                    files_backed_up.append(config_file.name)
            
            # Create backup metadata
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "files_backed_up": files_backed_up,
                "backup_type": "configuration"
            }
            
            metadata_file = backup_dir / "backup_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "backup_path": str(backup_dir),
                "files_backed_up": files_backed_up,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Configuration backup failed: {str(e)}"
            }
    
    async def restore_configuration(self, backup_name: str) -> Dict[str, Any]:
        """Restore configuration from backup"""
        
        backup_dir = self.app_root / "backups" / "config" / backup_name
        
        if not backup_dir.exists():
            return {
                "status": "error",
                "message": f"Backup not found: {backup_name}"
            }
        
        try:
            # Read backup metadata
            metadata_file = backup_dir / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            files_restored = []
            
            # Restore configuration files
            for item in backup_dir.iterdir():
                if item.name == "backup_metadata.json":
                    continue
                
                if item.is_file():
                    # Restore individual files
                    dest_path = self.app_root / item.name
                    
                    # Backup existing file
                    if dest_path.exists():
                        backup_path = Path(f"{dest_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copy2(dest_path, backup_path)
                    
                    shutil.copy2(item, dest_path)
                    files_restored.append(item.name)
                    
                elif item.is_dir() and item.name == "caddy":
                    # Restore Caddy directory
                    caddy_dir = self.app_root / "caddy"
                    
                    if caddy_dir.exists():
                        backup_path = Path(f"{caddy_dir}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copytree(caddy_dir, backup_path)
                        shutil.rmtree(caddy_dir)
                    
                    shutil.copytree(item, caddy_dir)
                    files_restored.append("caddy/")
            
            return {
                "status": "success",
                "backup_name": backup_name,
                "files_restored": files_restored,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Configuration restore failed: {str(e)}"
            }
    
    async def list_configuration_backups(self) -> Dict[str, Any]:
        """List all configuration backups"""
        
        backups_dir = self.app_root / "backups" / "config"
        
        if not backups_dir.exists():
            return {
                "backups": [],
                "count": 0
            }
        
        backups = []
        
        for backup_dir in backups_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "backup_metadata.json"
                
                try:
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                    else:
                        metadata = {
                            "backup_name": backup_dir.name,
                            "created_at": datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                            "files_backed_up": [],
                            "backup_type": "configuration"
                        }
                    
                    # Add size information
                    total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                    metadata["size"] = total_size
                    metadata["size_formatted"] = FormattingUtils.format_bytes(total_size)
                    
                    backups.append(metadata)
                    
                except Exception as e:
                    # Add minimal info for corrupted backups
                    backups.append({
                        "backup_name": backup_dir.name,
                        "created_at": datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                        "status": "corrupted",
                        "error": str(e)
                    })
        
        # Sort by creation date, newest first
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "backups": backups,
            "count": len(backups)
        }
    
    # Removed _format_bytes method - now using centralized FormattingUtils.format_bytes()
    
    async def get_status(self) -> str:
        """Get current configuration service status"""
        try:
            # Check if config directory exists and is accessible
            if not self.config_dir.exists():
                return "error"
            
            # Check for recent config backups (within last 7 days)
            recent_backups = []
            if self.backup_dir.exists():
                for backup_file in self.backup_dir.glob("*.json"):
                    stat = backup_file.stat()
                    if (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days < 7:
                        recent_backups.append(backup_file)
            
            # Check config file integrity
            try:
                main_config = self.config_dir / "config.yml"
                if main_config.exists():
                    with open(main_config, 'r') as f:
                        import yaml
                        yaml.safe_load(f)  # Test if valid YAML
                else:
                    return "warning"  # No main config file
            except Exception:
                return "error"  # Invalid config file
            
            # Determine status
            if recent_backups:
                return "healthy"
            else:
                return "warning"  # No recent backups
                
        except Exception:
            return "error"
