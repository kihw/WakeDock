"""
Middleware de Détection d'Intrusion
Intègre le système IDS dans l'application FastAPI
"""

from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import json
from urllib.parse import unquote
import asyncio

from .intrusion_detection import (
    IntrusionDetectionSystem, 
    SecurityEvent, 
    ThreatLevel, 
    AttackType,
    get_intrusion_detection_system
)

logger = logging.getLogger(__name__)

class IntrusionDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware pour la détection d'intrusion en temps réel"""
    
    def __init__(self, 
                 app: ASGIApp, 
                 ids: Optional[IntrusionDetectionSystem] = None,
                 block_on_threat: bool = True,
                 log_all_events: bool = True):
        super().__init__(app)
        self.ids = ids or get_intrusion_detection_system()
        self.block_on_threat = block_on_threat
        self.log_all_events = log_all_events
        
        # Endpoints exemptés de la détection
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico"
        }
        
        # Endpoints sensibles nécessitant une surveillance renforcée
        self.sensitive_endpoints = {
            "/auth/login",
            "/auth/register",
            "/admin",
            "/api/users",
            "/api/services",
            "/api/system"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Analyse chaque requête pour détecter les menaces"""
        
        # Ignorer les endpoints exclus
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extraire les informations de la requête
        ip_address = self._extract_ip_address(request)
        user_agent = request.headers.get("User-Agent", "")
        endpoint = request.url.path
        method = request.method
        
        # Vérifier si l'IP est bloquée
        if self.ids.is_ip_blocked(ip_address):
            logger.warning(f"Requête bloquée depuis IP bloquée: {ip_address}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "access_denied",
                    "message": "Votre adresse IP a été bloquée pour activité suspecte.",
                    "ip": ip_address
                }
            )
        
        # Ignorer les IP en whitelist
        if self.ids.is_ip_whitelisted(ip_address):
            return await call_next(request)
        
        # Extraire le payload de la requête
        payload = await self._extract_payload(request)
        
        # Extraire l'ID utilisateur si disponible
        user_id = self._extract_user_id(request)
        
        # Analyser la requête
        try:
            security_events = self.ids.analyze_request(
                ip_address=ip_address,
                endpoint=endpoint,
                method=method,
                user_agent=user_agent,
                payload=payload,
                user_id=user_id,
                headers=dict(request.headers)
            )
            
            # Traiter les événements de sécurité
            blocked_event = await self._handle_security_events(security_events, request)
            
            if blocked_event and self.block_on_threat:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "security_threat_detected",
                        "message": "Activité suspecte détectée. Accès refusé.",
                        "threat_type": blocked_event.attack_type.value,
                        "threat_level": blocked_event.threat_level.value,
                        "ip": ip_address
                    }
                )
            
            # Continuer avec la requête
            response = await call_next(request)
            
            # Analyser la réponse pour détecter d'éventuels problèmes
            await self._analyze_response(request, response, security_events)
            
            # Ajouter des headers de sécurité
            self._add_security_headers(response, security_events)
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur dans le middleware IDS: {e}")
            # En cas d'erreur, laisser passer la requête
            return await call_next(request)
    
    def _extract_ip_address(self, request: Request) -> str:
        """Extrait l'adresse IP réelle de la requête"""
        
        # Vérifier les headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Prendre la première IP de la liste
            ip = forwarded_for.split(",")[0].strip()
            return ip
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback sur l'IP du client
        return request.client.host if request.client else "unknown"
    
    async def _extract_payload(self, request: Request) -> Optional[str]:
        """Extrait le payload de la requête pour analyse"""
        
        try:
            # Analyser les paramètres de query
            query_params = str(request.url.query) if request.url.query else ""
            
            # Analyser le path pour les paramètres
            path = unquote(request.url.path)
            
            # Tenter d'extraire le body pour les requêtes POST/PUT
            body = ""
            if request.method in ["POST", "PUT", "PATCH"]:
                # Créer une copie du body pour éviter de le consommer
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        body = body_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        body = str(body_bytes)
            
            # Combiner tous les éléments
            payload_parts = [path, query_params, body]
            payload = " ".join(filter(None, payload_parts))
            
            return payload if payload.strip() else None
            
        except Exception as e:
            logger.debug(f"Erreur lors de l'extraction du payload: {e}")
            return None
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extrait l'ID utilisateur depuis la requête"""
        
        try:
            # Essayer d'extraire depuis les headers d'authentification
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Dans une implémentation réelle, décoder le JWT
                # et extraire l'ID utilisateur
                pass
            
            # Essayer d'extraire depuis les cookies de session
            session_cookie = request.cookies.get("session_id")
            if session_cookie:
                # Décoder le cookie de session pour obtenir l'ID utilisateur
                pass
            
            # Pour l'instant, retourner None
            return None
            
        except Exception as e:
            logger.debug(f"Erreur lors de l'extraction de l'ID utilisateur: {e}")
            return None
    
    async def _handle_security_events(self, 
                                    events: list[SecurityEvent], 
                                    request: Request) -> Optional[SecurityEvent]:
        """Traite les événements de sécurité détectés"""
        
        blocked_event = None
        
        for event in events:
            # Logger l'événement
            if self.log_all_events or event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                logger.warning(
                    f"Événement sécurité détecté: {event.attack_type.value} "
                    f"depuis {event.ip_address} - Niveau: {event.threat_level.value} "
                    f"- Confiance: {event.confidence:.2f}"
                )
            
            # Bloquer pour les menaces critiques
            if event.threat_level == ThreatLevel.CRITICAL:
                blocked_event = event
                logger.critical(
                    f"Menace critique détectée: {event.attack_type.value} "
                    f"depuis {event.ip_address} - Blocage automatique"
                )
            
            # Bloquer pour les menaces hautes répétées
            elif event.threat_level == ThreatLevel.HIGH and event.confidence > 0.8:
                # Vérifier si c'est une attaque répétée
                recent_events = self.ids.get_security_events(
                    limit=10,
                    ip_address=event.ip_address,
                    threat_level=ThreatLevel.HIGH
                )
                
                if len(recent_events) >= 3:  # 3 événements HIGH dans l'historique récent
                    blocked_event = event
                    logger.warning(
                        f"Attaques répétées détectées depuis {event.ip_address} - Blocage"
                    )
            
            # Envoyer des alertes pour les menaces importantes
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                await self._send_security_alert(event)
        
        return blocked_event
    
    async def _analyze_response(self, 
                               request: Request, 
                               response: Response, 
                               events: list[SecurityEvent]) -> None:
        """Analyse la réponse pour détecter d'éventuels problèmes"""
        
        # Analyser le code de statut
        if response.status_code == 401:
            # Tentative d'authentification échouée
            ip_address = self._extract_ip_address(request)
            profile = self.ids.get_ip_profile(ip_address)
            if profile:
                profile.update_activity(request.url.path, 
                                      request.headers.get("User-Agent", ""), 
                                      success=False)
        
        elif response.status_code == 403:
            # Accès interdit - potentielle escalade de privilèges
            pass
        
        elif response.status_code >= 500:
            # Erreur serveur - potentielle exploitation
            pass
    
    def _add_security_headers(self, response: Response, events: list[SecurityEvent]) -> None:
        """Ajoute des headers de sécurité à la réponse"""
        
        # Ajouter le nombre d'événements de sécurité détectés
        response.headers["X-Security-Events"] = str(len(events))
        
        # Ajouter le niveau de menace le plus élevé
        if events:
            max_threat_level = max(event.threat_level for event in events)
            response.headers["X-Threat-Level"] = max_threat_level.value
        
        # Headers de sécurité standard
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    async def _send_security_alert(self, event: SecurityEvent) -> None:
        """Envoie une alerte de sécurité"""
        
        try:
            # Ici, vous pourriez envoyer des notifications via:
            # - Email
            # - Slack
            # - Webhook
            # - Système de monitoring
            
            alert_data = {
                "timestamp": event.timestamp.isoformat(),
                "threat_type": event.attack_type.value,
                "threat_level": event.threat_level.value,
                "ip_address": event.ip_address,
                "endpoint": event.endpoint,
                "confidence": event.confidence,
                "details": event.details
            }
            
            # Log l'alerte pour l'instant
            logger.critical(f"SECURITY ALERT: {json.dumps(alert_data, indent=2)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'alerte de sécurité: {e}")


class SecurityDashboardEndpoints:
    """Endpoints pour le tableau de bord de sécurité"""
    
    def __init__(self, ids: IntrusionDetectionSystem):
        self.ids = ids
    
    def get_security_events(self, 
                           limit: int = 100,
                           threat_level: Optional[str] = None,
                           attack_type: Optional[str] = None,
                           ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Récupère les événements de sécurité"""
        
        threat_level_enum = ThreatLevel(threat_level) if threat_level else None
        attack_type_enum = AttackType(attack_type) if attack_type else None
        
        events = self.ids.get_security_events(
            limit=limit,
            threat_level=threat_level_enum,
            attack_type=attack_type_enum,
            ip_address=ip_address
        )
        
        return {
            "events": [event.to_dict() for event in events],
            "total": len(events),
            "filters": {
                "threat_level": threat_level,
                "attack_type": attack_type,
                "ip_address": ip_address
            }
        }
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de sécurité"""
        return self.ids.get_statistics()
    
    def get_ip_profile(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Récupère le profil d'une IP"""
        
        profile = self.ids.get_ip_profile(ip_address)
        if not profile:
            return None
        
        return {
            "ip_address": profile.ip_address,
            "first_seen": profile.first_seen.isoformat(),
            "last_seen": profile.last_seen.isoformat(),
            "request_count": profile.request_count,
            "failed_auth_count": profile.failed_auth_count,
            "successful_auth_count": profile.successful_auth_count,
            "endpoints_accessed": list(profile.endpoints_accessed),
            "user_agents": list(profile.user_agents),
            "suspicious_score": profile.suspicious_score,
            "is_blacklisted": profile.is_blacklisted,
            "is_whitelisted": profile.is_whitelisted
        }
    
    def block_ip(self, ip_address: str) -> Dict[str, Any]:
        """Bloque une adresse IP"""
        
        self.ids.block_ip(ip_address)
        return {"message": f"IP {ip_address} bloquée avec succès"}
    
    def unblock_ip(self, ip_address: str) -> Dict[str, Any]:
        """Débloque une adresse IP"""
        
        self.ids.unblock_ip(ip_address)
        return {"message": f"IP {ip_address} débloquée avec succès"}
    
    def whitelist_ip(self, ip_address: str) -> Dict[str, Any]:
        """Ajoute une IP à la whitelist"""
        
        self.ids.whitelist_ip(ip_address)
        return {"message": f"IP {ip_address} ajoutée à la whitelist"}
    
    def get_top_threats(self, limit: int = 10) -> Dict[str, Any]:
        """Récupère les principales menaces"""
        
        threats = self.ids.get_top_threats(limit)
        return {
            "threats": [
                {"ip_address": ip, "suspicious_score": score}
                for ip, score in threats
            ]
        }


# Instances globales
ids_middleware = None
security_dashboard = None

def get_ids_middleware(app: ASGIApp) -> IntrusionDetectionMiddleware:
    """Obtient l'instance du middleware IDS"""
    global ids_middleware
    if ids_middleware is None:
        ids_middleware = IntrusionDetectionMiddleware(app)
    return ids_middleware

def get_security_dashboard() -> SecurityDashboardEndpoints:
    """Obtient l'instance du tableau de bord de sécurité"""
    global security_dashboard
    if security_dashboard is None:
        security_dashboard = SecurityDashboardEndpoints(get_intrusion_detection_system())
    return security_dashboard
