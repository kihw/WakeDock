"""
Caddy Manager Facade

Façade pour maintenir la compatibilité avec l'ancienne classe CaddyManager
tout en utilisant la nouvelle architecture modulaire.
"""

import logging
from typing import List, Dict, Optional, Any

from wakedock.database.models import Service
from .config import CaddyConfigManager
from .api import CaddyApiClient
from .routes import RoutesManager
from .monitoring import CaddyHealthMonitor
from .types import HealthStatus, CaddyMetrics, DiagnosticReport

logger = logging.getLogger(__name__)


class CaddyManager:
    """
    Gestionnaire Caddy unifié - Façade pour les modules refactorisés.
    
    Maintient la compatibilité avec l'ancienne interface tout en
    utilisant la nouvelle architecture modulaire.
    """
    
    def __init__(self):
        """Initialiser le gestionnaire Caddy avec tous les modules"""
        
        # Initialiser les modules
        self.config_manager = CaddyConfigManager()
        self.api_client = CaddyApiClient()
        self.routes_manager = RoutesManager(self.api_client)
        self.health_monitor = CaddyHealthMonitor(self.api_client)
        self._initialized = False
        
        logger.info("Caddy Manager initialized with modular architecture")
    
    async def initialize(self):
        """Initialize the Caddy manager asynchronously"""
        if self._initialized:
            return
        
        try:
            # Initialize components that might need async setup
            await self.api_client.initialize()
            self._initialized = True
            logger.info("Caddy Manager async initialization completed")
        except Exception as e:
            logger.error(f"Failed to initialize Caddy Manager: {e}")
            raise
    
    # === Configuration Methods ===
    
    async def generate_config(self, services: List[Service]) -> str:
        """Générer la configuration pour les services"""
        return await self.config_manager.generate_config(services)
    
    async def reload_config(self) -> bool:
        """Recharger la configuration Caddy"""
        result = await self.api_client.reload_config()
        return result.success
    
    async def validate_config(self, config: str) -> Dict[str, Any]:
        """Valider une configuration"""
        validation = await self.config_manager.validate_config(config)
        return {
            "valid": validation.is_valid,
            "errors": validation.errors,
            "warnings": validation.warnings
        }
    
    async def backup_config(self) -> str:
        """Sauvegarder la configuration actuelle"""
        result = await self.config_manager.backup_config()
        return result.backup_id if result.success else ""
    
    async def restore_config(self, backup_id: str) -> bool:
        """Restaurer une configuration"""
        result = await self.config_manager.restore_config(backup_id)
        return result.success
    
    def get_current_config(self) -> Optional[str]:
        """Récupérer la configuration actuelle"""
        return self.config_manager.get_current_config()
    
    # === Routes Methods ===
    
    async def add_service(self, service: Service) -> bool:
        """Ajouter un service (créer sa route)"""
        return await self.routes_manager.add_service_route(service)
    
    async def remove_service(self, service_id: str) -> bool:
        """Supprimer un service (sa route)"""
        return await self.routes_manager.remove_service_route(service_id)
    
    async def update_service(self, service: Service) -> bool:
        """Mettre à jour un service"""
        return await self.routes_manager.update_service_route(service)
    
    async def update_service_config(self, services: List[Service]) -> bool:
        """Mettre à jour la configuration avec tous les services"""
        return await self.routes_manager.sync_routes_with_services(services)
    
    async def sync_services(self, services: List[Service]) -> Dict[str, bool]:
        """Synchroniser toutes les routes avec la liste des services"""
        return await self.routes_manager.sync_routes_with_services(services)
    
    async def validate_domain(self, domain: str) -> Dict[str, Any]:
        """Valider un domaine"""
        validation = await self.routes_manager.validate_domain(domain)
        return {
            "valid": validation.is_valid,
            "domain": validation.domain,
            "errors": validation.errors,
            "warnings": validation.warnings
        }
    
    def get_route_by_domain(self, domain: str) -> Optional[Dict]:
        """Récupérer une route par domaine"""
        route = self.routes_manager.get_route_by_domain(domain)
        if route:
            return {
                "id": route.id,
                "host": route.host,
                "upstream": route.upstream,
                "port": route.port,
                "path": route.path,
                "tls": route.tls,
                "headers": route.headers
            }
        return None
    
    def list_routes(self) -> List[Dict]:
        """Lister toutes les routes"""
        routes = self.routes_manager.list_all_routes()
        return [
            {
                "id": route.id,
                "host": route.host,
                "upstream": route.upstream,
                "port": route.port,
                "path": route.path,
                "tls": route.tls,
                "headers": route.headers
            }
            for route in routes
        ]
    
    # === Health & Monitoring Methods ===
    
    async def check_health(self) -> HealthStatus:
        """Vérifier la santé de Caddy"""
        return await self.health_monitor.check_health()
    
    async def get_status(self) -> Dict[str, Any]:
        """Récupérer le statut (compatibilité)"""
        health = await self.health_monitor.check_health()
        return {
            "status": health.status.value,
            "version": health.version,
            "uptime": health.uptime,
            "active_routes": health.active_routes,
            "errors": health.errors,
            "warnings": health.warnings
        }
    
    async def get_metrics(self) -> CaddyMetrics:
        """Récupérer les métriques"""
        return await self.health_monitor.get_metrics()
    
    async def diagnose(self) -> DiagnosticReport:
        """Effectuer un diagnostic complet"""
        return await self.health_monitor.diagnose_issues()
    
    def get_health_trend(self, hours: int = 24) -> Dict:
        """Récupérer la tendance de santé"""
        return self.health_monitor.get_health_trend(hours)
    
    async def is_healthy(self) -> bool:
        """Vérification rapide de santé"""
        return await self.api_client.is_healthy()
    
    # === Legacy Methods (pour compatibilité) ===
    
    async def ensure_service_route(self, service: Service) -> bool:
        """
        Méthode legacy - s'assurer qu'une route existe pour le service.
        Redirige vers add_service_route.
        """
        logger.warning("ensure_service_route is deprecated, use add_service instead")
        return await self.add_service(service)
    
    async def remove_service_route(self, service: Service) -> bool:
        """
        Méthode legacy - supprimer la route d'un service.
        Redirige vers remove_service.
        """
        logger.warning("remove_service_route is deprecated, use remove_service instead")
        return await self.remove_service(service.id)
    
    async def update_all_services(self, services: List[Service]) -> bool:
        """
        Méthode legacy - mettre à jour toutes les routes.
        Redirige vers sync_services.
        """
        logger.warning("update_all_services is deprecated, use sync_services instead")
        results = await self.sync_services(services)
        return all(results.values())
    
    # === Utility Methods ===
    
    def get_config_manager(self) -> CaddyConfigManager:
        """Accès direct au gestionnaire de configuration"""
        return self.config_manager
    
    def get_api_client(self) -> CaddyApiClient:
        """Accès direct au client API"""
        return self.api_client
    
    def get_routes_manager(self) -> RoutesManager:
        """Accès direct au gestionnaire de routes"""
        return self.routes_manager
    
    def get_health_monitor(self) -> CaddyHealthMonitor:
        """Accès direct au monitor de santé"""
        return self.health_monitor
    
    async def start_monitoring(self, interval: int = 30) -> None:
        """Démarrer le monitoring continu"""
        await self.health_monitor.start_continuous_monitoring(interval)
    
    def __repr__(self) -> str:
        return f"<CaddyManager(modular_architecture=True)>"


# Instance globale pour compatibilité avec l'ancien code
caddy_manager = CaddyManager()