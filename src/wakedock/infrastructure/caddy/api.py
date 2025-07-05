"""
Caddy API Client

Communication avec l'API admin Caddy.
Extrait de la classe monolithique CaddyManager.
"""

import httpx
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from wakedock.config import get_settings
from .types import CaddyStatus, ReloadResult, HealthStatus

logger = logging.getLogger(__name__)


class CaddyApiClient:
    """Client API pour communiquer avec Caddy Admin"""
    
    def __init__(self):
        """Initialiser le client API"""
        self.settings = get_settings()
        self.admin_host = getattr(self.settings.caddy, 'admin_host', 'caddy')
        self.admin_port = getattr(self.settings.caddy, 'admin_port', 2019)
        self.base_url = f"http://{self.admin_host}:{self.admin_port}"
        
        # Configuration client HTTP
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.retry_attempts = 3
        self.retry_delay = 1.0
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        **kwargs
    ) -> httpx.Response:
        """Faire une requête HTTP avec retry automatique"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data,
                        **kwargs
                    )
                    
                    # Log de la requête
                    logger.debug(f"Caddy API {method} {endpoint}: {response.status_code}")
                    
                    return response
                    
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Caddy API request failed (attempt {attempt + 1}), retrying: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"Caddy API request failed after {self.retry_attempts} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error in Caddy API request: {e}")
                raise
    
    async def reload_config(self) -> ReloadResult:
        """Recharger la configuration Caddy"""
        start_time = datetime.now()
        
        try:
            response = await self._make_request("POST", "/load")
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                logger.info(f"Caddy config reloaded successfully in {duration_ms:.2f}ms")
                return ReloadResult(
                    success=True,
                    duration_ms=duration_ms
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to reload Caddy config: {error_msg}")
                return ReloadResult(
                    success=False,
                    duration_ms=duration_ms,
                    error=error_msg
                )
                
        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Exception during reload: {str(e)}"
            logger.error(error_msg)
            return ReloadResult(
                success=False,
                duration_ms=duration_ms,
                error=error_msg
            )
    
    async def get_status(self) -> HealthStatus:
        """Récupérer le statut de santé de Caddy"""
        try:
            # Récupérer les informations de base
            config_response = await self._make_request("GET", "/config/")
            
            if config_response.status_code != 200:
                return HealthStatus(
                    status=CaddyStatus.UNHEALTHY,
                    version="unknown",
                    uptime=0.0,
                    active_routes=0,
                    errors=[f"Config API error: HTTP {config_response.status_code}"],
                    warnings=[]
                )
            
            # Compter les routes actives
            try:
                config_data = config_response.json()
                active_routes = self._count_active_routes(config_data)
            except:
                active_routes = 0
            
            # Récupérer la version via metrics
            version = await self._get_caddy_version()
            
            return HealthStatus(
                status=CaddyStatus.HEALTHY,
                version=version,
                uptime=0.0,  # TODO: Récupérer uptime réel si disponible
                active_routes=active_routes,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to get Caddy status: {e}")
            return HealthStatus(
                status=CaddyStatus.UNKNOWN,
                version="unknown",
                uptime=0.0,
                active_routes=0,
                errors=[str(e)],
                warnings=[]
            )
    
    def _count_active_routes(self, config_data: Dict) -> int:
        """Compter les routes actives dans la configuration"""
        try:
            routes_count = 0
            
            # Parcourir la configuration pour compter les sites
            if isinstance(config_data, dict):
                apps = config_data.get("apps", {})
                http_app = apps.get("http", {})
                servers = http_app.get("servers", {})
                
                for server_name, server_config in servers.items():
                    routes = server_config.get("routes", [])
                    routes_count += len(routes)
            
            return routes_count
            
        except Exception as e:
            logger.error(f"Failed to count active routes: {e}")
            return 0
    
    async def _get_caddy_version(self) -> str:
        """Récupérer la version de Caddy"""
        try:
            response = await self._make_request("GET", "/reverse_proxy/upstreams")
            
            # La version peut être dans les headers ou via un autre endpoint
            version_header = response.headers.get("Server", "")
            if "Caddy" in version_header:
                return version_header
            
            return "unknown"
            
        except:
            return "unknown"
    
    async def add_route(self, route_config: Dict) -> bool:
        """Ajouter une route dynamiquement"""
        try:
            endpoint = "/config/apps/http/servers/srv0/routes"
            response = await self._make_request("POST", endpoint, data=route_config)
            
            if response.status_code in [200, 201]:
                logger.info("Route added successfully")
                return True
            else:
                logger.error(f"Failed to add route: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception adding route: {e}")
            return False
    
    async def remove_route(self, route_id: str) -> bool:
        """Supprimer une route par ID"""
        try:
            endpoint = f"/config/apps/http/servers/srv0/routes/{route_id}"
            response = await self._make_request("DELETE", endpoint)
            
            if response.status_code in [200, 204]:
                logger.info(f"Route {route_id} removed successfully")
                return True
            else:
                logger.error(f"Failed to remove route {route_id}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception removing route {route_id}: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques Caddy si disponibles"""
        try:
            response = await self._make_request("GET", "/metrics")
            
            if response.status_code == 200:
                # Caddy peut exposer des métriques Prometheus
                return {"raw_metrics": response.text}
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"error": str(e)}
    
    async def validate_config_syntax(self, config: str) -> Dict[str, Any]:
        """Valider la syntaxe d'une configuration via l'API"""
        try:
            # Endpoint pour valider la configuration
            response = await self._make_request(
                "POST", 
                "/load",
                headers={"Content-Type": "application/json"},
                content=config
            )
            
            return {
                "valid": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def get_current_config(self) -> Optional[Dict]:
        """Récupérer la configuration actuelle via API"""
        try:
            response = await self._make_request("GET", "/config/")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get current config: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting current config: {e}")
            return None
    
    async def is_healthy(self) -> bool:
        """Vérification rapide de santé"""
        try:
            response = await self._make_request("GET", "/config/")
            return response.status_code == 200
        except:
            return False