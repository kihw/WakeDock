"""
Caddy Routes Manager

Gestion dynamique des routes services.
Extrait de la classe monolithique CaddyManager.
"""

import re
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from wakedock.database.models import Service, ServiceStatus
from .types import Route, RouteResult, RouteStatus, DomainValidation
from .api import CaddyApiClient

logger = logging.getLogger(__name__)


class RoutesManager:
    """Gestionnaire des routes dynamiques Caddy"""
    
    def __init__(self, api_client: CaddyApiClient):
        """Initialiser le gestionnaire de routes"""
        self.api = api_client
        self.active_routes: Dict[str, Route] = {}
        
        # Patterns de validation
        self.domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        
        # Domaines réservés
        self.reserved_domains = {
            'localhost', 'wakedock', 'caddy', 'postgres', 'redis',
            'admin', 'api', 'www', 'mail', 'ftp'
        }
    
    async def add_service_route(self, service: Service) -> bool:
        """Ajouter une route pour un service"""
        try:
            # Validation du service
            if not self._can_create_route(service):
                logger.warning(f"Cannot create route for service {service.name}")
                return False
            
            # Créer la route
            route = self._create_route_from_service(service)
            
            # Valider le domaine
            domain_validation = await self.validate_domain(route.host)
            if not domain_validation.is_valid:
                logger.error(f"Invalid domain {route.host}: {domain_validation.errors}")
                return False
            
            # Configuration Caddy pour la route
            route_config = self._build_caddy_route_config(route)
            
            # Ajouter via API
            success = await self.api.add_route(route_config)
            
            if success:
                self.active_routes[route.id] = route
                logger.info(f"Added route for service {service.name}: {route.host}")
                return True
            else:
                logger.error(f"Failed to add route for service {service.name}")
                return False
                
        except Exception as e:
            logger.error(f"Exception adding service route for {service.name}: {e}")
            return False
    
    async def remove_service_route(self, service_id: str) -> bool:
        """Supprimer une route de service"""
        try:
            route_id = f"service_{service_id}"
            
            if route_id not in self.active_routes:
                logger.warning(f"Route {route_id} not found in active routes")
                return True  # Déjà supprimée
            
            # Supprimer via API
            success = await self.api.remove_route(route_id)
            
            if success:
                del self.active_routes[route_id]
                logger.info(f"Removed route for service {service_id}")
                return True
            else:
                logger.error(f"Failed to remove route for service {service_id}")
                return False
                
        except Exception as e:
            logger.error(f"Exception removing service route {service_id}: {e}")
            return False
    
    async def update_service_route(self, service: Service) -> bool:
        """Mettre à jour une route de service"""
        try:
            # Supprimer l'ancienne route
            await self.remove_service_route(service.id)
            
            # Ajouter la nouvelle route
            return await self.add_service_route(service)
            
        except Exception as e:
            logger.error(f"Exception updating service route for {service.name}: {e}")
            return False
    
    def _can_create_route(self, service: Service) -> bool:
        """Vérifier si une route peut être créée pour le service"""
        # Le service doit être en cours d'exécution
        if service.status != ServiceStatus.RUNNING:
            return False
        
        # Le service doit avoir un domaine configuré
        domain = getattr(service, 'domain', None)
        if not domain:
            return False
        
        # Le domaine ne doit pas être réservé
        if domain.lower() in self.reserved_domains:
            return False
        
        return True
    
    def _create_route_from_service(self, service: Service) -> Route:
        """Créer un objet Route depuis un Service"""
        domain = getattr(service, 'domain', f"{service.name}.wakedock.local")
        port = getattr(service, 'port', 8000)
        
        # Déterminer l'upstream
        upstream = f"http://wakedock-{service.name}:{port}"
        
        return Route(
            id=f"service_{service.id}",
            host=domain,
            upstream=upstream,
            port=port,
            path="/",
            tls=True,
            headers={
                'X-Forwarded-For': '{remote}',
                'X-Forwarded-Proto': '{scheme}',
                'X-Service-Name': service.name
            }
        )
    
    def _build_caddy_route_config(self, route: Route) -> Dict:
        """Construire la configuration Caddy pour une route"""
        return {
            "@id": route.id,
            "match": [
                {
                    "host": [route.host]
                }
            ],
            "handle": [
                {
                    "handler": "reverse_proxy",
                    "upstreams": [
                        {
                            "dial": route.upstream.replace("http://", "")
                        }
                    ],
                    "headers": {
                        "request": {
                            "set": route.headers
                        },
                        "response": {
                            "set": {
                                "X-Frame-Options": ["DENY"],
                                "X-Content-Type-Options": ["nosniff"],
                                "X-XSS-Protection": ["1; mode=block"]
                            }
                        }
                    }
                }
            ]
        }
    
    async def validate_domain(self, domain: str) -> DomainValidation:
        """Valider un nom de domaine"""
        errors = []
        warnings = []
        
        try:
            # Validation basique
            if not domain:
                errors.append("Domain cannot be empty")
                return DomainValidation(False, domain, errors, warnings)
            
            # Longueur maximale
            if len(domain) > 253:
                errors.append("Domain too long (max 253 characters)")
            
            # Pattern de validation
            if not self.domain_pattern.match(domain):
                errors.append("Invalid domain format")
            
            # Domaines réservés
            if domain.lower() in self.reserved_domains:
                errors.append(f"Domain '{domain}' is reserved")
            
            # Vérification de conflit avec routes existantes
            if self._domain_conflicts_with_existing(domain):
                errors.append(f"Domain '{domain}' conflicts with existing route")
            
            # Labels trop longs
            for label in domain.split('.'):
                if len(label) > 63:
                    errors.append(f"Domain label '{label}' too long (max 63 characters)")
                if label.startswith('-') or label.endswith('-'):
                    errors.append(f"Domain label '{label}' cannot start or end with hyphen")
            
            # Avertissements
            if domain.count('.') == 0:
                warnings.append("Single-label domain (consider using subdomain)")
            
            if domain.startswith('www.'):
                warnings.append("WWW prefix detected (consider root domain)")
            
            is_valid = len(errors) == 0
            
            return DomainValidation(is_valid, domain, errors, warnings)
            
        except Exception as e:
            logger.error(f"Domain validation error: {e}")
            errors.append(f"Validation error: {str(e)}")
            return DomainValidation(False, domain, errors, warnings)
    
    def _domain_conflicts_with_existing(self, domain: str) -> bool:
        """Vérifier les conflits avec les routes existantes"""
        for route in self.active_routes.values():
            if route.host.lower() == domain.lower():
                return True
        return False
    
    async def get_routes_status(self) -> Dict[str, RouteStatus]:
        """Récupérer le statut de toutes les routes"""
        status_map = {}
        
        try:
            # Récupérer la config actuelle via API
            current_config = await self.api.get_current_config()
            
            if current_config:
                active_hosts = self._extract_hosts_from_config(current_config)
                
                for route_id, route in self.active_routes.items():
                    if route.host in active_hosts:
                        status_map[route_id] = RouteStatus.ACTIVE
                    else:
                        status_map[route_id] = RouteStatus.INACTIVE
            else:
                # Fallback: marquer toutes comme inconnues
                for route_id in self.active_routes:
                    status_map[route_id] = RouteStatus.ERROR
                    
        except Exception as e:
            logger.error(f"Failed to get routes status: {e}")
            # Marquer toutes comme erreur
            for route_id in self.active_routes:
                status_map[route_id] = RouteStatus.ERROR
        
        return status_map
    
    def _extract_hosts_from_config(self, config: Dict) -> Set[str]:
        """Extraire les hosts depuis la configuration Caddy"""
        hosts = set()
        
        try:
            apps = config.get("apps", {})
            http_app = apps.get("http", {})
            servers = http_app.get("servers", {})
            
            for server in servers.values():
                routes = server.get("routes", [])
                for route in routes:
                    matches = route.get("match", [])
                    for match in matches:
                        host_list = match.get("host", [])
                        hosts.update(host_list)
                        
        except Exception as e:
            logger.error(f"Failed to extract hosts from config: {e}")
        
        return hosts
    
    def get_route_by_domain(self, domain: str) -> Optional[Route]:
        """Trouver une route par domaine"""
        for route in self.active_routes.values():
            if route.host.lower() == domain.lower():
                return route
        return None
    
    def get_routes_by_service(self, service_id: str) -> List[Route]:
        """Récupérer toutes les routes d'un service"""
        routes = []
        route_id = f"service_{service_id}"
        
        if route_id in self.active_routes:
            routes.append(self.active_routes[route_id])
        
        return routes
    
    def list_all_routes(self) -> List[Route]:
        """Lister toutes les routes actives"""
        return list(self.active_routes.values())
    
    async def sync_routes_with_services(self, services: List[Service]) -> Dict[str, bool]:
        """Synchroniser les routes avec la liste des services"""
        results = {}
        
        try:
            # Services qui devraient avoir des routes
            expected_routes = set()
            for service in services:
                if self._can_create_route(service):
                    expected_routes.add(f"service_{service.id}")
            
            # Routes actuellement actives
            current_routes = set(self.active_routes.keys())
            
            # Routes à ajouter
            to_add = expected_routes - current_routes
            for route_id in to_add:
                service_id = route_id.replace("service_", "")
                service = next((s for s in services if s.id == service_id), None)
                if service:
                    results[route_id] = await self.add_service_route(service)
            
            # Routes à supprimer
            to_remove = current_routes - expected_routes
            for route_id in to_remove:
                service_id = route_id.replace("service_", "")
                results[route_id] = await self.remove_service_route(service_id)
            
            logger.info(f"Route sync completed: {len(to_add)} added, {len(to_remove)} removed")
            
        except Exception as e:
            logger.error(f"Failed to sync routes with services: {e}")
        
        return results