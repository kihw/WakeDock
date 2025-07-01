"""Caddy integration for WakeDock dynamic reverse proxy management."""

import os
import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

from wakedock.config import get_settings
from wakedock.database.models import Service, ServiceStatus

logger = logging.getLogger(__name__)


class CaddyManager:
    """Manages Caddy configuration and API interactions."""
    
    def __init__(self):
        """Initialize Caddy manager with settings."""
        self.settings = get_settings()
        
        # Use /etc/caddy inside the container (this is where the volume is mounted)
        # The CADDY_CONFIG_VOLUME_PATH env var is for the host, not the container
        self.config_path = Path("/etc/caddy/Caddyfile")
        
        self.reload_endpoint = self.settings.caddy.reload_endpoint
        self.admin_port = getattr(self.settings.caddy, 'admin_port', 2019)
        self.admin_host = getattr(self.settings.caddy, 'admin_host', 'caddy')
        
        # Initialize Jinja2 environment for templates
        template_dir = self.config_path.parent / "templates"
        if template_dir.exists():
            self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        else:
            # Create basic template environment
            self.jinja_env = Environment(loader=FileSystemLoader("."))
        
        # Ensure initial Caddyfile exists
        self._ensure_initial_caddyfile()
    
    def _ensure_initial_caddyfile(self) -> None:
        """Ensure Caddyfile exists and is properly configured for WakeDock."""
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if a directory with the name "Caddyfile" exists (common mistake)
            if self.config_path.exists() and self.config_path.is_dir():
                logger.warning(f"Found directory named 'Caddyfile' at {self.config_path}, removing it...")
                import shutil
                shutil.rmtree(self.config_path)
                logger.info("Removed incorrect Caddyfile directory")
            
            # Check if Caddyfile exists and has WakeDock markers
            if self.config_path.exists() and self.config_path.is_file():
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if it has WakeDock markers
                    if "=== WAKEDOCK MANAGED SERVICES START ===" in content:
                        logger.info(f"✅ WakeDock Caddyfile found at {self.config_path}")
                        return
                    else:
                        logger.info("Existing Caddyfile found but missing WakeDock markers, updating...")
                        # Add WakeDock markers to existing file
                        updated_content = content + "\n\n# === WAKEDOCK MANAGED SERVICES START ===\n"
                        updated_content += "# Cette section est automatiquement gérée par WakeDock\n"
                        updated_content += "# Ne pas modifier manuellement\n"
                        updated_content += "# === WAKEDOCK MANAGED SERVICES END ===\n"
                        
                        with open(self.config_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        logger.info("✅ Added WakeDock markers to existing Caddyfile")
                        
                except Exception as e:
                    logger.error(f"Error reading existing Caddyfile: {e}")
                    # Fall through to create new file
            
            # If no valid Caddyfile exists, create the default one
            if not self.config_path.exists() or not self.config_path.is_file():
                initial_config = self._get_default_caddyfile()
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    f.write(initial_config)
                logger.info(f"✅ Created WakeDock Caddyfile at {self.config_path}")
                
        except Exception as e:
            logger.error(f"❌ Error ensuring Caddyfile: {e}")
    
    def _generate_initial_caddyfile(self) -> str:
        """Generate initial Caddyfile configuration."""
        return """# WakeDock Auto-Generated Caddyfile
# This file is managed by WakeDock application

{
    admin 0.0.0.0:2019
    auto_https off
    
    # Global options
    servers {
        timeouts {
            read_body   10s
            read_header 10s
            write       10s
            idle        2m
        }
    }
}

# Main HTTP port - serves as proxy when app is ready, fallback when not
:80 {
    # Try to proxy to dashboard first
    @dashboard_ready {
        path /*
        header_regexp Host "^(localhost|.*)"
    }
    
    # Try dashboard with fallback
    handle @dashboard_ready {
        reverse_proxy dashboard:3000 {
            header_up Host {upstream_hostport}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
            
            # Fallback to loading page if dashboard not ready
            @error status 502 503 504
            handle_response @error {
                respond "WakeDock is starting... Dashboard will be available shortly." 503 {
                    body "WakeDock Dashboard is initializing. Please wait a moment and refresh."
                }
            }
        }
    }
    
    # API routes
    handle /api/* {
        reverse_proxy wakedock:8000 {
            header_up Host {upstream_hostport}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
            
            # Fallback if API not ready
            @error status 502 503 504
            handle_response @error {
                respond "WakeDock API is starting..." 503 {
                    body "WakeDock API is initializing. Please wait a moment and try again."
                }
            }
        }
    }
    
    # Health check endpoint
    handle /health {
        respond "WakeDock Caddy OK" 200
    }
    
    # Fallback for any unmatched requests
    handle {
        respond "WakeDock is starting... Please wait for all services to initialize." 503 {
            body "WakeDock is initializing. All services will be available shortly."
        }
    }
    
    log {
        output stdout
        format console
    }
}

# Admin API port
:2019 {
    respond /config* "WakeDock Caddy Admin API" 200
    
    # Allow all admin operations
    handle {
        reverse_proxy localhost:2019
    }
    
    log {
        output stdout
        format console
    }
}

# Dynamic service configurations will be appended below
# --- WAKEDOCK MANAGED SERVICES ---
"""
    
    async def reload_caddy(self) -> bool:
        """Reload Caddy configuration via API."""
        try:
            # First, check if Caddy is reachable
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to get current config first to check if Caddy is running
                try:
                    health_response = await client.get(f"http://{self.admin_host}:{self.admin_port}/config/")
                    if health_response.status_code != 200:
                        logger.warning(f"Caddy admin API not responding properly: {health_response.status_code}")
                        return False
                except httpx.ConnectError:
                    logger.warning("Caddy admin API not reachable, skipping reload")
                    return False
                
                # If we have a Caddyfile, use it to reload
                if self.config_path.exists():
                    # Use the reload endpoint with the file content
                    response = await client.post(
                        f"http://{self.admin_host}:{self.admin_port}/load",
                        headers={"Content-Type": "text/caddyfile"},
                        content=self.config_path.read_text()
                    )
                else:
                    logger.warning("No Caddyfile found, cannot reload")
                    return False
                
                if response.status_code == 200:
                    logger.info("✅ Caddy configuration reloaded successfully")
                    return True
                else:
                    logger.error(f"❌ Failed to reload Caddy: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error reloading Caddy: {e}")
            return False
    
    def _get_caddy_config(self) -> Dict[str, Any]:
        """Generate Caddy configuration from current services."""
        try:
            # Read current Caddyfile and convert to JSON config
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    caddyfile_content = f.read()
                return self._caddyfile_to_json(caddyfile_content)
            return {}
        except Exception as e:
            logger.error(f"Error reading Caddy config: {e}")
            return {}
    
    def _caddyfile_to_json(self, caddyfile: str) -> Dict[str, Any]:
        """Convert Caddyfile to JSON config (simplified version)."""
        # This is a simplified converter - in production you'd use Caddy's adapter
        config = {
            "apps": {
                "http": {
                    "servers": {
                        "srv0": {
                            "listen": [":80", ":443"],
                            "routes": []
                        }
                    }
                }
            }
        }
        return config
    
    def generate_service_config(self, service: Service) -> str:
        """Generate Caddy configuration for a service."""
        if not service.domain:
            return ""
        
        # Build upstream URL
        upstream_url = f"http://localhost:{self._get_service_port(service)}"
        
        # Generate configuration block
        config_lines = [
            f"{service.domain} {{",
            f"    reverse_proxy {upstream_url}",
        ]
        
        # Add SSL configuration
        if service.enable_ssl:
            config_lines.extend([
                "    tls {",
                "        on_demand",
                "    }"
            ])
        
        # Add authentication if enabled
        if service.enable_auth:
            config_lines.extend([
                "    basicauth {",
                "        admin $2a$14$hashed_password_here",
                "    }"
            ])
        
        # Add health check
        config_lines.extend([
            "    health_uri /health",
            "    health_interval 30s",
        ])
        
        config_lines.append("}")
        
        return "\n".join(config_lines)
    
    def _get_service_port(self, service: Service) -> int:
        """Extract the main port from service configuration."""
        if service.ports and isinstance(service.ports, list) and len(service.ports) > 0:
            port_mapping = service.ports[0]
            if isinstance(port_mapping, dict) and 'host' in port_mapping:
                return port_mapping['host']
        
        # Default port if not configured
        return 8080
    
    async def update_service_config(self, services: List[Service]) -> bool:
        """Update only the WakeDock-managed sections of the Caddyfile."""
        try:
            logger.info(f"Updating WakeDock-managed sections with {len(services)} services...")
            
            # Read current Caddyfile
            current_content = await self._read_current_caddyfile()
            
            # Generate configuration for running services only
            services_config = []
            for service in services:
                if service.status == ServiceStatus.RUNNING and service.domain:
                    config_block = self.generate_service_config(service)
                    if config_block:
                        services_config.append(config_block)
                        logger.info(f"Added config for service: {service.name} -> {service.domain}")
            
            # Update only the WakeDock-managed sections
            updated_content = self._update_wakedock_sections(current_content, services_config)
            
            # Write updated configuration
            await self._write_caddyfile(updated_content)
            
            # Reload Caddy
            reload_success = await self.reload_caddy()
            
            if reload_success:
                logger.info("WakeDock sections updated and Caddy reloaded successfully!")
            else:
                logger.error("WakeDock sections updated but Caddy reload failed")
            
            return reload_success
            
        except Exception as e:
            logger.error(f"Error updating WakeDock sections: {e}")
            return False
    
    async def _read_current_caddyfile(self) -> str:
        """Read the current Caddyfile content."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.debug(f"Read existing Caddyfile: {len(content)} characters")
                return content
            else:
                logger.info("No existing Caddyfile, using default")
                return self._get_default_caddyfile()
        except Exception as e:
            logger.error(f"Error reading Caddyfile: {e}")
            return self._get_default_caddyfile()
    
    def _get_default_caddyfile(self) -> str:
        """Get the default Caddyfile content."""
        return """# WakeDock Caddyfile
{
    admin 0.0.0.0:2019
    auto_https off
    log default {
        output stdout
        format console
    }
}

:80 {
    log {
        output stdout
        format console
    }

    # API routes pour WakeDock
    handle_path /api/* {
        reverse_proxy wakedock:8000 {
            header_up Host {upstream_hostport}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }
    
    # Health check
    handle /health {
        respond "WakeDock Proxy OK" 200
    }

    # Dashboard WakeDock
    handle {
        reverse_proxy dashboard:3000 {
            header_up Host {upstream_hostport}
            header_up X-Real-IP {remote_host}
            header_up X-Forwarded-For {remote_host}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}

:2019 {
    respond "Caddy Admin API Active" 200
}

# === WAKEDOCK MANAGED SERVICES START ===
# Cette section est automatiquement gérée par WakeDock
# Ne pas modifier manuellement
# === WAKEDOCK MANAGED SERVICES END ==="""

    def _update_wakedock_sections(self, current_content: str, services_config: List[str]) -> str:
        """Update only the WakeDock-managed sections in the Caddyfile."""
        try:
            start_marker = "# === WAKEDOCK MANAGED SERVICES START ==="
            end_marker = "# === WAKEDOCK MANAGED SERVICES END ==="
            
            # Find the markers
            start_pos = current_content.find(start_marker)
            end_pos = current_content.find(end_marker)
            
            if start_pos == -1 or end_pos == -1:
                logger.warning("WakeDock markers not found, appending services at the end")
                # Add markers and services at the end
                services_section = f"\n\n{start_marker}\n"
                services_section += "# Cette section est automatiquement gérée par WakeDock\n"
                services_section += "# Ne pas modifier manuellement\n\n"
                if services_config:
                    services_section += "\n\n".join(services_config) + "\n"
                services_section += f"\n{end_marker}"
                
                return current_content + services_section
            
            # Replace content between markers
            before_section = current_content[:start_pos]
            after_section = current_content[end_pos + len(end_marker):]
            
            # Build new services section
            services_section = f"{start_marker}\n"
            services_section += "# Cette section est automatiquement gérée par WakeDock\n"
            services_section += "# Ne pas modifier manuellement\n"
            
            if services_config:
                services_section += "\n" + "\n\n".join(services_config) + "\n"
            
            services_section += f"\n{end_marker}"
            
            updated_content = before_section + services_section + after_section
            
            logger.info(f"Updated WakeDock section with {len(services_config)} services")
            return updated_content
            
        except Exception as e:
            logger.error(f"Error updating WakeDock sections: {e}")
            return current_content
    
    async def _write_caddyfile(self, content: str) -> None:
        """Write content to Caddyfile, preserving the base configuration."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to the directory
            config_dir = self.config_path.parent
            if not os.access(config_dir, os.W_OK):
                logger.error(f"❌ No write permission to directory: {config_dir}")
                logger.info("💡 This might be a volume permission issue.")
                logger.info("💡 Try running: docker-compose down && docker-compose up -d")
                raise PermissionError(f"Cannot write to Caddy config directory: {config_dir}")
            
            # Check if file exists and is writable
            if self.config_path.exists() and not os.access(self.config_path, os.W_OK):
                logger.error(f"❌ No write permission to file: {self.config_path}")
                logger.info("💡 File permissions issue. Trying to fix...")
                
                # Try to fix permissions if we can
                try:
                    os.chmod(self.config_path, 0o666)
                    logger.info("✅ Fixed file permissions")
                except Exception as chmod_error:
                    logger.error(f"❌ Could not fix file permissions: {chmod_error}")
                    raise PermissionError(f"Cannot write to Caddyfile: {self.config_path}")
            
            # Write updated configuration
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify the file was written
            if self.config_path.exists():
                file_size = self.config_path.stat().st_size
                logger.info(f"✅ Caddyfile updated (WakeDock sections only): {self.config_path} ({file_size} bytes)")
            else:
                logger.error(f"❌ Failed to write Caddyfile: {self.config_path}")
                
        except PermissionError:
            # Re-raise permission errors with context
            raise
        except Exception as e:
            logger.error(f"❌ Error writing Caddyfile: {e}")
            logger.info(f"💡 Path: {self.config_path}")
            logger.info(f"💡 Directory exists: {self.config_path.parent.exists()}")
            logger.info(f"💡 Directory writable: {os.access(self.config_path.parent, os.W_OK) if self.config_path.parent.exists() else 'N/A'}")
            if self.config_path.exists():
                logger.info(f"💡 File writable: {os.access(self.config_path, os.W_OK)}")
            raise
    
    async def add_service_route(self, service: Service) -> bool:
        """Add a route for a new service."""
        if service.status != ServiceStatus.RUNNING or not service.domain:
            return False
        
        try:
            # Use Caddy API to add route dynamically
            route_config = {
                "@id": f"wakedock-{service.name}",
                "match": [{"host": [service.domain]}],
                "handle": [{
                    "handler": "reverse_proxy",
                    "upstreams": [{
                        "dial": f"localhost:{self._get_service_port(service)}"
                    }]
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{self.admin_host}:{self.admin_port}/config/apps/http/servers/srv0/routes",
                    json=route_config
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Added route for service {service.name}")
                    # Automatically reload Caddy configuration
                    await self.reload_caddy()
                    return True
                else:
                    logger.error(f"Failed to add route: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error adding service route: {e}")
            return False
    
    async def remove_service_route(self, service: Service) -> bool:
        """Remove a route for a service."""
        try:
            route_id = f"wakedock-{service.name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"http://{self.admin_host}:{self.admin_port}/id/{route_id}"
                )
                
                if response.status_code == 200:
                    logger.info(f"Removed route for service {service.name}")
                    # Automatically reload Caddy configuration
                    await self.reload_caddy()
                    return True
                else:
                    logger.warning(f"Failed to remove route (may not exist): {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing service route: {e}")
            return False
    
    async def get_caddy_status(self) -> Dict[str, Any]:
        """Get Caddy server status."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.admin_host}:{self.admin_port}/config/"
                )
                
                if response.status_code == 200:
                    return {
                        "status": "running",
                        "config": response.json()
                    }
                else:
                    return {"status": "error", "message": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def validate_domain(self, domain: str) -> bool:
        """Validate if a domain is available for use."""
        try:
            # Check if domain is already in use
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.admin_host}:{self.admin_port}/config/apps/http/servers/srv0/routes"
                )
                
                if response.status_code == 200:
                    routes = response.json()
                    for route in routes:
                        for match in route.get("match", []):
                            if domain in match.get("host", []):
                                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating domain: {e}")
            return False
    
    def _schedule_reload(self) -> None:
        """Schedule a Caddy reload in a background task."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a task to reload in the background
                loop.create_task(self._delayed_reload())
            else:
                # If no loop is running, we'll skip the reload for now
                logger.warning("No event loop running, skipping Caddy reload")
        except Exception as e:
            logger.warning(f"Could not schedule Caddy reload: {e}")
    
    async def _delayed_reload(self) -> None:
        """Reload Caddy after a short delay to ensure file is written."""
        try:
            # Wait a bit to ensure the file is fully written
            await asyncio.sleep(1)
            await self.reload_caddy()
        except Exception as e:
            logger.error(f"Error in delayed reload: {e}")
    
    async def force_reload(self) -> bool:
        """Force a Caddy configuration reload."""
        logger.info("Forcing Caddy configuration reload...")
        return await self.reload_caddy()
    
    def write_caddyfile_sync(self, content: str) -> None:
        """Synchronous version of _write_caddyfile for non-async contexts."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to the directory
            config_dir = self.config_path.parent
            if not os.access(config_dir, os.W_OK):
                logger.error(f"❌ No write permission to directory: {config_dir}")
                logger.info("💡 This might be a volume permission issue.")
                logger.info("💡 Try running: docker-compose down && docker-compose up -d")
                raise PermissionError(f"Cannot write to Caddy config directory: {config_dir}")
            
            # Check if file exists and is writable
            if self.config_path.exists() and not os.access(self.config_path, os.W_OK):
                logger.error(f"❌ No write permission to file: {self.config_path}")
                logger.info("💡 File permissions issue. Trying to fix...")
                
                # Try to fix permissions if we can
                try:
                    os.chmod(self.config_path, 0o666)
                    logger.info("✅ Fixed file permissions")
                except Exception as chmod_error:
                    logger.error(f"❌ Could not fix file permissions: {chmod_error}")
                    raise PermissionError(f"Cannot write to Caddyfile: {self.config_path}")
            
            # Write configuration
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ Updated Caddyfile at {self.config_path}")
            
            # Schedule reload in background
            self._schedule_reload()
            
        except PermissionError:
            # Re-raise permission errors with context
            raise
        except Exception as e:
            logger.error(f"❌ Error writing Caddyfile: {e}")
            logger.info(f"💡 Path: {self.config_path}")
            logger.info(f"💡 Directory exists: {self.config_path.parent.exists()}")
            logger.info(f"💡 Directory writable: {os.access(self.config_path.parent, os.W_OK) if self.config_path.parent.exists() else 'N/A'}")
            if self.config_path.exists():
                logger.info(f"💡 File writable: {os.access(self.config_path, os.W_OK)}")
            raise
    
    def start_file_watcher(self):
        """Start watching the Caddyfile for changes and auto-reload."""
        try:
            import threading
            import time
            
            def watch_file():
                last_modified = None
                while True:
                    try:
                        if self.config_path.exists():
                            current_modified = self.config_path.stat().st_mtime
                            if last_modified is not None and current_modified != last_modified:
                                logger.info("Caddyfile changed, scheduling reload...")
                                self._schedule_reload()
                            last_modified = current_modified
                    except Exception as e:
                        logger.error(f"Error watching Caddyfile: {e}")
                    
                    time.sleep(2)  # Check every 2 seconds
            
            # Start the watcher in a background thread
            watcher_thread = threading.Thread(target=watch_file, daemon=True)
            watcher_thread.start()
            logger.info("Started Caddyfile watcher")
            
        except Exception as e:
            logger.warning(f"Could not start file watcher: {e}")
    
    async def ensure_wakedock_configuration(self) -> bool:
        """Force WakeDock configuration in Caddy, regardless of current state."""
        try:
            logger.info("🔧 Forcing WakeDock configuration in Caddy...")
            
            # Get or create WakeDock Caddyfile content
            wakedock_content = self._get_default_caddyfile()
            
            # Write it to Caddy
            await self._write_caddyfile(wakedock_content)
            
            # Force reload Caddy
            reload_success = await self.reload_caddy()
            
            if reload_success:
                logger.info("✅ WakeDock Caddy configuration forced successfully!")
                
                # Test if the configuration is working
                await self._test_wakedock_routes()
                
                return True
            else:
                logger.error("❌ Failed to reload Caddy after forcing configuration")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error forcing WakeDock configuration: {e}")
            return False
    
    async def _test_wakedock_routes(self) -> None:
        """Test if WakeDock routes are working correctly."""
        try:
            # Test health endpoint through Caddy
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ WakeDock health endpoint accessible through Caddy")
                    else:
                        logger.warning(f"⚠️ Health endpoint returned status {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not test health endpoint: {e}")
                    
                # Test API endpoint through Caddy
                try:
                    response = await client.get("http://localhost/api/v1/system/overview", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ WakeDock API accessible through Caddy")
                    else:
                        logger.warning(f"⚠️ API endpoint returned status {response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not test API endpoint: {e}")
                
                # Test dashboard through Caddy
                try:
                    response = await client.get("http://localhost/", timeout=10)
                    if response.status_code == 200 and "WakeDock" in response.text:
                        logger.info("✅ Dashboard accessible through Caddy")
                    elif response.status_code == 200:
                        logger.warning("⚠️ Got response but may not be WakeDock dashboard")
                        if "Congratulations" in response.text:
                            logger.warning("🎊 Still showing Caddy default page")
                    else:
                        logger.warning(f"⚠️ Dashboard returned status {response.status_code}")
                        # If dashboard fails, run diagnostics
                        await self.diagnose_dashboard_connection()
                except Exception as e:
                    logger.warning(f"⚠️ Could not test dashboard: {e}")
                    await self.diagnose_dashboard_connection()
                    
        except Exception as e:
            logger.warning(f"Could not test routes: {e}")
    
    async def detect_and_fix_default_page(self) -> bool:
        """Detect if Caddy is showing default page and fix it."""
        try:
            logger.info("🔍 Checking if Caddy is showing default page...")
            
            # Test if we get the default Caddy page
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost/", timeout=10)
                    
                    # Check if it's the default Caddy page
                    if (response.status_code == 200 and 
                        ("Congratulations" in response.text or 
                         "Caddy is ready" in response.text or
                         "make it work for you" in response.text)):
                        
                        logger.warning("⚠️ Detected Caddy default page! Fixing configuration...")
                        
                        # Force WakeDock configuration
                        success = await self.ensure_wakedock_configuration()
                        
                        if success:
                            logger.info("✅ Successfully replaced Caddy default page with WakeDock!")
                            return True
                        else:
                            logger.error("❌ Failed to replace Caddy default page")
                            return False
                            
                    else:
                        logger.info("✅ Caddy is not showing default page")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Could not check Caddy page: {e}")
                    # If we can't check, force configuration anyway
                    return await self.ensure_wakedock_configuration()
                    
        except Exception as e:
            logger.error(f"Error detecting/fixing default page: {e}")
            return False
    
    async def diagnose_dashboard_connection(self) -> bool:
        """Diagnose dashboard connection issues."""
        try:
            logger.info("🔍 Diagnosing dashboard connection...")
            
            # Test direct connection to dashboard
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://dashboard:3000/health", timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ Dashboard health endpoint accessible directly")
                        return True
                    else:
                        logger.warning(f"⚠️ Dashboard health returned status {response.status_code}")
                except Exception as e:
                    logger.warning(f"❌ Dashboard health endpoint failed: {e}")
                
                # Try root endpoint
                try:
                    response = await client.get("http://dashboard:3000/", timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ Dashboard root endpoint accessible")
                        return True
                    else:
                        logger.warning(f"⚠️ Dashboard root returned status {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ Dashboard root endpoint failed: {e}")
                    logger.error("💡 Dashboard container may not be running or build failed")
                    
                    # Additional diagnostics
                    await self._suggest_dashboard_fixes()
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error diagnosing dashboard: {e}")
            return False
    
    async def _suggest_dashboard_fixes(self) -> None:
        """Suggest fixes for dashboard issues."""
        logger.info("🔧 Dashboard troubleshooting suggestions:")
        logger.info("1. Check if dashboard container is running: docker ps | grep dashboard")
        logger.info("2. Check dashboard logs: docker logs wakedock-dashboard")
        logger.info("3. Verify SvelteKit build: docker exec wakedock-dashboard ls -la build/")
        logger.info("4. Test dashboard health: docker exec wakedock-dashboard curl -f http://localhost:3000/health")
        logger.info("5. Rebuild dashboard: docker-compose build dashboard")


# Global Caddy manager instance
caddy_manager = CaddyManager()
