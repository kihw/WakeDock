#!/usr/bin/env python3
"""
WakeDock Configuration Validator and Fixer
Validates and fixes common configuration issues in WakeDock deployments.
"""

import argparse
import json
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates and fixes WakeDock configuration."""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.issues = []
        self.fixes_applied = []
        
    def validate_all(self, fix: bool = False) -> Tuple[bool, List[str], List[str]]:
        """Validate all configuration files."""
        logger.info(f"Validating WakeDock configuration in: {self.project_dir}")
        
        # Run all validation checks
        self._validate_docker_compose(fix)
        self._validate_dockerfile(fix)
        self._validate_environment_file(fix)
        self._validate_config_files(fix)
        self._validate_directory_structure(fix)
        self._validate_permissions(fix)
        self._validate_network_configuration(fix)
        self._validate_security_settings(fix)
        
        # Summary
        has_issues = len(self.issues) > 0
        logger.info(f"Validation complete. Found {len(self.issues)} issues.")
        if fix and self.fixes_applied:
            logger.info(f"Applied {len(self.fixes_applied)} fixes.")
        
        return not has_issues, self.issues, self.fixes_applied
    
    def _add_issue(self, issue: str):
        """Add a validation issue."""
        self.issues.append(issue)
        logger.warning(f"ISSUE: {issue}")
    
    def _add_fix(self, fix: str):
        """Add a fix that was applied."""
        self.fixes_applied.append(fix)
        logger.info(f"FIXED: {fix}")
    
    def _validate_docker_compose(self, fix: bool = False):
        """Validate docker-compose.yml configuration."""
        compose_file = self.project_dir / "docker-compose.yml"
        
        if not compose_file.exists():
            self._add_issue("docker-compose.yml file is missing")
            if fix:
                self._create_default_docker_compose()
            return
        
        try:
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self._add_issue(f"docker-compose.yml has invalid YAML syntax: {e}")
            return
        except Exception as e:
            self._add_issue(f"Cannot read docker-compose.yml: {e}")
            return
        
        # Check version
        if 'version' not in compose_config:
            self._add_issue("docker-compose.yml missing version specification")
            if fix:
                compose_config['version'] = '3.8'
                self._write_compose_file(compose_file, compose_config)
                self._add_fix("Added version '3.8' to docker-compose.yml")
        
        # Check services
        if 'services' not in compose_config:
            self._add_issue("docker-compose.yml missing services section")
            return
        
        services = compose_config['services']
        
        # Check for WakeDock service
        if 'wakedock' not in services:
            self._add_issue("WakeDock service not defined in docker-compose.yml")
        else:
            self._validate_wakedock_service(services['wakedock'], fix, compose_file, compose_config)
        
        # Check for Caddy service
        if 'caddy' not in services:
            self._add_issue("Caddy service not defined in docker-compose.yml")
        else:
            self._validate_caddy_service(services['caddy'], fix, compose_file, compose_config)
        
        # Check networks
        self._validate_compose_networks(compose_config, fix, compose_file)
        
        # Check volumes
        self._validate_compose_volumes(compose_config, fix, compose_file)
    
    def _validate_wakedock_service(self, service: Dict, fix: bool, compose_file: Path, compose_config: Dict):
        """Validate WakeDock service configuration."""
        # Check required fields
        required_fields = ['build', 'ports', 'volumes', 'environment']
        for field in required_fields:
            if field not in service:
                self._add_issue(f"WakeDock service missing required field: {field}")
                if fix and field == 'ports':
                    service['ports'] = ['8000:8000']
                    self._write_compose_file(compose_file, compose_config)
                    self._add_fix("Added default ports to WakeDock service")
        
        # Check Docker socket mount
        volumes = service.get('volumes', [])
        has_docker_socket = any('/var/run/docker.sock' in str(vol) for vol in volumes)
        if not has_docker_socket:
            self._add_issue("WakeDock service missing Docker socket mount")
            if fix:
                if 'volumes' not in service:
                    service['volumes'] = []
                service['volumes'].append('/var/run/docker.sock:/var/run/docker.sock')
                self._write_compose_file(compose_file, compose_config)
                self._add_fix("Added Docker socket mount to WakeDock service")
        
        # Check restart policy
        if 'restart' not in service:
            self._add_issue("WakeDock service missing restart policy")
            if fix:
                service['restart'] = 'unless-stopped'
                self._write_compose_file(compose_file, compose_config)
                self._add_fix("Added restart policy to WakeDock service")
    
    def _validate_caddy_service(self, service: Dict, fix: bool, compose_file: Path, compose_config: Dict):
        """Validate Caddy service configuration."""
        # Check ports
        ports = service.get('ports', [])
        expected_ports = ['80:80', '443:443', '2019:2019']
        
        for expected_port in expected_ports:
            if not any(expected_port in str(port) for port in ports):
                self._add_issue(f"Caddy service missing port mapping: {expected_port}")
                if fix:
                    if 'ports' not in service:
                        service['ports'] = []
                    service['ports'].append(expected_port)
                    self._write_compose_file(compose_file, compose_config)
                    self._add_fix(f"Added port mapping {expected_port} to Caddy service")
        
        # Check volumes
        volumes = service.get('volumes', [])
        required_volumes = [
            ('caddy_data', '/data'),
            ('caddy_config', '/config'),
            ('./caddy/Caddyfile', '/etc/caddy/Caddyfile')
        ]
        
        for vol_source, vol_target in required_volumes:
            if not any(vol_target in str(vol) for vol in volumes):
                self._add_issue(f"Caddy service missing volume mount: {vol_target}")
                if fix:
                    if 'volumes' not in service:
                        service['volumes'] = []
                    service['volumes'].append(f"{vol_source}:{vol_target}")
                    self._write_compose_file(compose_file, compose_config)
                    self._add_fix(f"Added volume mount {vol_source}:{vol_target} to Caddy service")
    
    def _validate_compose_networks(self, compose_config: Dict, fix: bool, compose_file: Path):
        """Validate networks configuration."""
        if 'networks' not in compose_config:
            self._add_issue("docker-compose.yml missing networks section")
            if fix:
                compose_config['networks'] = {
                    'wakedock_network': {
                        'driver': 'bridge'
                    }
                }
                self._write_compose_file(compose_file, compose_config)
                self._add_fix("Added default network configuration")
    
    def _validate_compose_volumes(self, compose_config: Dict, fix: bool, compose_file: Path):
        """Validate volumes configuration."""
        if 'volumes' not in compose_config:
            self._add_issue("docker-compose.yml missing volumes section")
            if fix:
                compose_config['volumes'] = {
                    'caddy_data': {},
                    'caddy_config': {},
                    'wakedock_data': {}
                }
                self._write_compose_file(compose_file, compose_config)
                self._add_fix("Added default volume definitions")
    
    def _validate_dockerfile(self, fix: bool = False):
        """Validate Dockerfile."""
        dockerfile_path = self.project_dir / "Dockerfile"
        
        if not dockerfile_path.exists():
            self._add_issue("Dockerfile is missing")
            if fix:
                self._create_default_dockerfile()
            return
        
        try:
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
        except Exception as e:
            self._add_issue(f"Cannot read Dockerfile: {e}")
            return
        
        # Check for required instructions
        required_instructions = ['FROM', 'WORKDIR', 'COPY', 'RUN', 'EXPOSE', 'CMD']
        for instruction in required_instructions:
            if instruction not in dockerfile_content:
                self._add_issue(f"Dockerfile missing {instruction} instruction")
        
        # Check for Python base image
        if 'FROM python:' not in dockerfile_content:
            self._add_issue("Dockerfile should use Python base image")
        
        # Check for port exposure
        if 'EXPOSE 8000' not in dockerfile_content:
            self._add_issue("Dockerfile should expose port 8000")
    
    def _validate_environment_file(self, fix: bool = False):
        """Validate environment configuration."""
        env_file = self.project_dir / ".env"
        env_example = self.project_dir / ".env.example"
        
        if not env_example.exists():
            self._add_issue(".env.example file is missing")
        
        if not env_file.exists():
            self._add_issue(".env file is missing")
            if fix and env_example.exists():
                # Copy from example
                import shutil
                shutil.copy2(env_example, env_file)
                self._add_fix("Created .env file from .env.example")
        
        if env_file.exists():
            self._validate_env_variables(env_file)
    
    def _validate_env_variables(self, env_file: Path):
        """Validate environment variables."""
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
        except Exception as e:
            self._add_issue(f"Cannot read .env file: {e}")
            return
        
        # Required environment variables
        required_vars = [
            'WAKEDOCK_SECRET_KEY',
            'WAKEDOCK_DEBUG',
            'WAKEDOCK_DATA_DIR',
            'CADDY_DOMAIN'
        ]
        
        for var in required_vars:
            if f"{var}=" not in env_content:
                self._add_issue(f"Missing required environment variable: {var}")
        
        # Check for sensitive defaults
        if 'WAKEDOCK_SECRET_KEY=your-secret-key-here' in env_content:
            self._add_issue("WAKEDOCK_SECRET_KEY is using default value - should be changed")
        
        if 'CADDY_DOMAIN=localhost' in env_content:
            self._add_issue("CADDY_DOMAIN is set to localhost - should be changed for production")
    
    def _validate_config_files(self, fix: bool = False):
        """Validate configuration files."""
        config_dir = self.project_dir / "config"
        
        if not config_dir.exists():
            self._add_issue("config directory is missing")
            if fix:
                config_dir.mkdir(parents=True, exist_ok=True)
                self._add_fix("Created config directory")
        
        # Check config.yml
        config_file = config_dir / "config.yml"
        if not config_file.exists():
            self._add_issue("config/config.yml is missing")
            if fix:
                self._create_default_config(config_file)
        
        # Check Caddy configuration
        caddy_dir = self.project_dir / "caddy"
        if not caddy_dir.exists():
            self._add_issue("caddy directory is missing")
            if fix:
                caddy_dir.mkdir(parents=True, exist_ok=True)
                self._add_fix("Created caddy directory")
        
        caddyfile = caddy_dir / "Caddyfile"
        if not caddyfile.exists():
            self._add_issue("caddy/Caddyfile is missing")
            if fix:
                self._create_default_caddyfile(caddyfile)
    
    def _validate_directory_structure(self, fix: bool = False):
        """Validate required directory structure."""
        required_dirs = [
            "src/wakedock",
            "tests",
            "scripts",
            "docs",
            "caddy",
            "config"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_dir / dir_path
            if not full_path.exists():
                self._add_issue(f"Required directory missing: {dir_path}")
                if fix:
                    full_path.mkdir(parents=True, exist_ok=True)
                    self._add_fix(f"Created directory: {dir_path}")
    
    def _validate_permissions(self, fix: bool = False):
        """Validate file permissions."""
        # Check script files
        script_files = [
            "init.sh",
            "scripts/health-check.sh",
            "scripts/backup.sh",
            "scripts/cleanup.sh",
            "scripts/status.sh"
        ]
        
        for script_file in script_files:
            script_path = self.project_dir / script_file
            if script_path.exists():
                if not os.access(script_path, os.X_OK):
                    self._add_issue(f"Script file not executable: {script_file}")
                    if fix:
                        os.chmod(script_path, 0o755)
                        self._add_fix(f"Made script executable: {script_file}")
    
    def _validate_network_configuration(self, fix: bool = False):
        """Validate network configuration."""
        # Check if required ports are documented
        compose_file = self.project_dir / "docker-compose.yml"
        if compose_file.exists():
            try:
                with open(compose_file, 'r') as f:
                    compose_config = yaml.safe_load(f)
                
                # Check for port conflicts
                used_ports = set()
                services = compose_config.get('services', {})
                
                for service_name, service_config in services.items():
                    ports = service_config.get('ports', [])
                    for port_mapping in ports:
                        if ':' in str(port_mapping):
                            host_port = str(port_mapping).split(':')[0]
                            if host_port in used_ports:
                                self._add_issue(f"Port conflict detected: {host_port} used by multiple services")
                            used_ports.add(host_port)
                            
            except Exception as e:
                logger.warning(f"Could not validate network configuration: {e}")
    
    def _validate_security_settings(self, fix: bool = False):
        """Validate security settings."""
        # Check for secrets in version control
        gitignore_file = self.project_dir / ".gitignore"
        
        if gitignore_file.exists():
            try:
                with open(gitignore_file, 'r') as f:
                    gitignore_content = f.read()
                
                required_patterns = ['.env', '*.key', '*.pem', '__pycache__', '*.pyc']
                for pattern in required_patterns:
                    if pattern not in gitignore_content:
                        self._add_issue(f"Sensitive pattern not in .gitignore: {pattern}")
                        
            except Exception as e:
                logger.warning(f"Could not validate .gitignore: {e}")
        else:
            self._add_issue(".gitignore file is missing")
            if fix:
                self._create_default_gitignore()
    
    def _create_default_docker_compose(self):
        """Create a default docker-compose.yml file."""
        default_compose = {
            'version': '3.8',
            'services': {
                'wakedock': {
                    'build': '.',
                    'ports': ['8000:8000'],
                    'volumes': [
                        '/var/run/docker.sock:/var/run/docker.sock',
                        'wakedock_data:/app/data',
                        './config:/app/config'
                    ],
                    'environment': [
                        'WAKEDOCK_DEBUG=${WAKEDOCK_DEBUG:-false}',
                        'WAKEDOCK_DATA_DIR=/app/data'
                    ],
                    'restart': 'unless-stopped',
                    'networks': ['wakedock_network']
                },
                'caddy': {
                    'image': 'caddy:2-alpine',
                    'ports': ['80:80', '443:443', '2019:2019'],
                    'volumes': [
                        './caddy/Caddyfile:/etc/caddy/Caddyfile',
                        'caddy_data:/data',
                        'caddy_config:/config'
                    ],
                    'restart': 'unless-stopped',
                    'networks': ['wakedock_network']
                }
            },
            'networks': {
                'wakedock_network': {
                    'driver': 'bridge'
                }
            },
            'volumes': {
                'wakedock_data': {},
                'caddy_data': {},
                'caddy_config': {}
            }
        }
        
        compose_file = self.project_dir / "docker-compose.yml"
        self._write_compose_file(compose_file, default_compose)
        self._add_fix("Created default docker-compose.yml")
    
    def _create_default_dockerfile(self):
        """Create a default Dockerfile."""
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "wakedock.main"]
"""
        
        dockerfile_path = self.project_dir / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        self._add_fix("Created default Dockerfile")
    
    def _create_default_config(self, config_file: Path):
        """Create a default config.yml file."""
        default_config = {
            'app': {
                'name': 'WakeDock',
                'version': '2.0.0',
                'debug': False
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'cors_origins': ['*']
            },
            'database': {
                'url': 'sqlite:///data/wakedock.db'
            },
            'security': {
                'secret_key': '${WAKEDOCK_SECRET_KEY}',
                'token_expire_hours': 24
            },
            'docker': {
                'socket_path': '/var/run/docker.sock'
            },
            'caddy': {
                'admin_endpoint': 'http://caddy:2019',
                'config_path': '/etc/caddy/Caddyfile'
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        self._add_fix("Created default config.yml")
    
    def _create_default_caddyfile(self, caddyfile: Path):
        """Create a default Caddyfile."""
        caddyfile_content = """{$CADDY_DOMAIN:localhost} {
    reverse_proxy wakedock:8000
    
    handle_path /dashboard/* {
        reverse_proxy dashboard:3000
    }
    
    encode gzip
    
    log {
        output file /data/access.log
    }
}

# Admin API
:2019 {
    respond /config/* 200
    respond 404
}
"""
        
        with open(caddyfile, 'w') as f:
            f.write(caddyfile_content)
        
        self._add_fix("Created default Caddyfile")
    
    def _create_default_gitignore(self):
        """Create a default .gitignore file."""
        gitignore_content = """# Environment files
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Data
data/
*.db
*.sqlite

# Secrets
*.key
*.pem
*.crt
secrets/

# Temporary files
tmp/
temp/

# Docker
.docker/
"""
        
        gitignore_file = self.project_dir / ".gitignore"
        with open(gitignore_file, 'w') as f:
            f.write(gitignore_content)
        
        self._add_fix("Created default .gitignore")
    
    def _write_compose_file(self, compose_file: Path, compose_config: Dict):
        """Write docker-compose configuration to file."""
        with open(compose_file, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Validate and fix WakeDock configuration')
    parser.add_argument('--fix', action='store_true', help='Automatically fix issues where possible')
    parser.add_argument('--project-dir', default='.', help='Project directory path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = ConfigValidator(args.project_dir)
    is_valid, issues, fixes = validator.validate_all(fix=args.fix)
    
    print("\n" + "="*60)
    print("WAKEDOCK CONFIGURATION VALIDATION REPORT")
    print("="*60)
    
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    
    if fixes:
        print(f"\n✅ Applied {len(fixes)} fixes:")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix}")
    
    if is_valid:
        print(f"\n🎉 Configuration is valid!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Configuration has issues that need attention.")
        if not args.fix:
            print("Run with --fix to automatically fix issues where possible.")
        sys.exit(1)


if __name__ == "__main__":
    main()
