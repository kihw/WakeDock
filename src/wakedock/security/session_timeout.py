"""
Session Timeout Middleware
Implémente la gestion automatique des timeouts de session
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Informations de session utilisateur"""
    user_id: int
    session_id: str
    last_activity: datetime
    created_at: datetime
    ip_address: str
    user_agent: str
    is_authenticated: bool = True
    warning_sent: bool = False

class SessionTimeoutManager:
    """Gestionnaire des timeouts de session"""
    
    def __init__(self,
                 idle_timeout_minutes: int = 60,
                 warn_before_timeout_minutes: int = 5,
                 max_concurrent_sessions: int = 5,
                 cleanup_interval_minutes: int = 10):
        
        self.idle_timeout_minutes = idle_timeout_minutes
        self.warn_before_timeout_minutes = warn_before_timeout_minutes
        self.max_concurrent_sessions = max_concurrent_sessions
        self.cleanup_interval_minutes = cleanup_interval_minutes
        
        # Stockage des sessions actives
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.user_sessions: Dict[int, set] = {}  # user_id -> set of session_ids
        
        # Statistiques
        self.stats = {
            "total_sessions": 0,
            "expired_sessions": 0,
            "warned_sessions": 0,
            "concurrent_sessions_rejected": 0,
            "last_cleanup": None
        }
        
        # Tâche de nettoyage
        self._cleanup_task = None
    
    def create_session(self, 
                      user_id: int, 
                      session_id: str,
                      ip_address: str,
                      user_agent: str) -> bool:
        """Crée une nouvelle session"""
        
        try:
            # Vérifier la limite de sessions simultanées
            if not self._check_concurrent_sessions_limit(user_id):
                self.stats["concurrent_sessions_rejected"] += 1
                logger.warning(f"Limite de sessions simultanées atteinte pour l'utilisateur {user_id}")
                return False
            
            now = datetime.now(timezone.utc)
            
            session_info = SessionInfo(
                user_id=user_id,
                session_id=session_id,
                last_activity=now,
                created_at=now,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.active_sessions[session_id] = session_info
            
            # Ajouter à la liste des sessions utilisateur
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
            
            self.stats["total_sessions"] += 1
            logger.info(f"Session créée pour l'utilisateur {user_id}: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de session: {e}")
            return False
    
    def _check_concurrent_sessions_limit(self, user_id: int) -> bool:
        """Vérifie la limite de sessions simultanées"""
        
        user_session_ids = self.user_sessions.get(user_id, set())
        
        # Nettoyer les sessions expirées pour ce user
        expired_sessions = []
        for session_id in user_session_ids:
            if session_id in self.active_sessions:
                if self.is_session_expired(session_id):
                    expired_sessions.append(session_id)
        
        # Supprimer les sessions expirées
        for session_id in expired_sessions:
            self.remove_session(session_id)
        
        # Vérifier la limite après nettoyage
        current_sessions = len(self.user_sessions.get(user_id, set()))
        return current_sessions < self.max_concurrent_sessions
    
    def update_session_activity(self, session_id: str) -> bool:
        """Met à jour l'activité d'une session"""
        
        if session_id not in self.active_sessions:
            return False
        
        if self.is_session_expired(session_id):
            self.remove_session(session_id)
            return False
        
        self.active_sessions[session_id].last_activity = datetime.now(timezone.utc)
        self.active_sessions[session_id].warning_sent = False  # Reset warning flag
        
        return True
    
    def is_session_expired(self, session_id: str) -> bool:
        """Vérifie si une session est expirée"""
        
        if session_id not in self.active_sessions:
            return True
        
        session_info = self.active_sessions[session_id]
        now = datetime.now(timezone.utc)
        time_since_activity = now - session_info.last_activity
        
        return time_since_activity.total_seconds() > (self.idle_timeout_minutes * 60)
    
    def should_warn_user(self, session_id: str) -> bool:
        """Détermine si l'utilisateur doit être averti d'une expiration prochaine"""
        
        if session_id not in self.active_sessions:
            return False
        
        session_info = self.active_sessions[session_id]
        
        # Ne pas avertir si déjà fait
        if session_info.warning_sent:
            return False
        
        now = datetime.now(timezone.utc)
        time_since_activity = now - session_info.last_activity
        time_until_expiry = (self.idle_timeout_minutes * 60) - time_since_activity.total_seconds()
        
        return time_until_expiry <= (self.warn_before_timeout_minutes * 60)
    
    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Obtient les informations d'une session"""
        return self.active_sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> bool:
        """Supprime une session"""
        
        if session_id not in self.active_sessions:
            return False
        
        session_info = self.active_sessions[session_id]
        user_id = session_info.user_id
        
        # Supprimer de la liste des sessions actives
        del self.active_sessions[session_id]
        
        # Supprimer de la liste des sessions utilisateur
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        self.stats["expired_sessions"] += 1
        logger.info(f"Session supprimée: {session_id}")
        
        return True
    
    def remove_all_user_sessions(self, user_id: int) -> int:
        """Supprime toutes les sessions d'un utilisateur"""
        
        user_session_ids = self.user_sessions.get(user_id, set()).copy()
        removed_count = 0
        
        for session_id in user_session_ids:
            if self.remove_session(session_id):
                removed_count += 1
        
        logger.info(f"Suppression de {removed_count} sessions pour l'utilisateur {user_id}")
        return removed_count
    
    def cleanup_expired_sessions(self) -> int:
        """Nettoie les sessions expirées"""
        
        now = datetime.now(timezone.utc)
        expired_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            time_since_activity = now - session_info.last_activity
            if time_since_activity.total_seconds() > (self.idle_timeout_minutes * 60):
                expired_sessions.append(session_id)
        
        # Supprimer les sessions expirées
        for session_id in expired_sessions:
            self.remove_session(session_id)
        
        self.stats["last_cleanup"] = now
        
        if expired_sessions:
            logger.info(f"Nettoyage de {len(expired_sessions)} sessions expirées")
        
        return len(expired_sessions)
    
    def get_timeout_warnings(self) -> Dict[str, Dict[str, Any]]:
        """Obtient les avertissements de timeout à envoyer"""
        
        warnings = {}
        
        for session_id, session_info in self.active_sessions.items():
            if self.should_warn_user(session_id):
                now = datetime.now(timezone.utc)
                time_since_activity = now - session_info.last_activity
                time_until_expiry = (self.idle_timeout_minutes * 60) - time_since_activity.total_seconds()
                
                warnings[session_id] = {
                    "user_id": session_info.user_id,
                    "time_until_expiry_seconds": int(time_until_expiry),
                    "warning_message": f"Votre session expirera dans {int(time_until_expiry/60)} minutes"
                }
                
                # Marquer comme averti
                session_info.warning_sent = True
                self.stats["warned_sessions"] += 1
        
        return warnings
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des sessions"""
        
        return {
            **self.stats,
            "active_sessions_count": len(self.active_sessions),
            "users_with_sessions": len(self.user_sessions),
            "idle_timeout_minutes": self.idle_timeout_minutes,
            "warn_before_timeout_minutes": self.warn_before_timeout_minutes,
            "max_concurrent_sessions": self.max_concurrent_sessions
        }
    
    async def start_background_cleanup(self) -> None:
        """Démarre le nettoyage automatique en arrière-plan"""
        
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_minutes * 60)
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage automatique des sessions: {e}")


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware pour gérer les timeouts de session"""
    
    def __init__(self, app: ASGIApp, session_manager: SessionTimeoutManager):
        super().__init__(app)
        self.session_manager = session_manager
        
        # Endpoints qui ne nécessitent pas de session
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Traite les requêtes avec vérification de timeout"""
        
        # Ignorer les endpoints exclus
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Extraire les informations de session
        session_id = self._extract_session_id(request)
        
        if not session_id:
            # Pas de session, continuer normalement
            return await call_next(request)
        
        # Vérifier si la session est expirée
        if self.session_manager.is_session_expired(session_id):
            logger.info(f"Session expirée détectée: {session_id}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "session_expired",
                    "message": "Votre session a expiré. Veuillez vous reconnecter.",
                    "redirect": "/auth/login"
                }
            )
        
        # Mettre à jour l'activité de la session
        if not self.session_manager.update_session_activity(session_id):
            logger.warning(f"Impossible de mettre à jour l'activité de la session: {session_id}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_session",
                    "message": "Session invalide. Veuillez vous reconnecter.",
                    "redirect": "/auth/login"
                }
            )
        
        # Vérifier si un avertissement doit être envoyé
        response = await call_next(request)
        
        # Ajouter les headers de session timeout
        self._add_session_headers(response, session_id)
        
        return response
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """Extrait l'ID de session de la requête"""
        
        # Essayer d'extraire depuis les cookies
        session_id = request.cookies.get("session_id")
        
        if not session_id:
            # Essayer d'extraire depuis les headers
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Dans une implémentation réelle, vous pourriez décoder le JWT
                # et extraire l'ID de session
                session_id = auth_header.replace("Bearer ", "")
        
        return session_id
    
    def _add_session_headers(self, response: Response, session_id: str) -> None:
        """Ajoute les headers de session timeout à la réponse"""
        
        session_info = self.session_manager.get_session_info(session_id)
        if not session_info:
            return
        
        now = datetime.now(timezone.utc)
        time_since_activity = now - session_info.last_activity
        time_until_expiry = (self.session_manager.idle_timeout_minutes * 60) - time_since_activity.total_seconds()
        
        response.headers["X-Session-Timeout"] = str(int(time_until_expiry))
        response.headers["X-Session-Warning"] = str(self.session_manager.warn_before_timeout_minutes * 60)
        
        # Ajouter un avertissement si nécessaire
        if self.session_manager.should_warn_user(session_id):
            response.headers["X-Session-Warning-Active"] = "true"
            response.headers["X-Session-Warning-Message"] = f"Session expiring in {int(time_until_expiry/60)} minutes"


class SessionTimeoutService:
    """Service principal pour la gestion des timeouts de session"""
    
    def __init__(self, session_manager: SessionTimeoutManager):
        self.session_manager = session_manager
        self._background_task = None
        self._warning_task = None
    
    async def start(self) -> None:
        """Démarre le service de timeout de session"""
        
        if self._background_task is None:
            self._background_task = asyncio.create_task(
                self.session_manager.start_background_cleanup()
            )
            logger.info("Service de timeout de session démarré")
    
    async def stop(self) -> None:
        """Arrête le service de timeout de session"""
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None
            logger.info("Service de timeout de session arrêté")
    
    async def create_session(self, 
                           user_id: int, 
                           session_id: str,
                           ip_address: str,
                           user_agent: str) -> bool:
        """Crée une nouvelle session"""
        return self.session_manager.create_session(user_id, session_id, ip_address, user_agent)
    
    async def extend_session(self, session_id: str) -> bool:
        """Étend une session existante"""
        return self.session_manager.update_session_activity(session_id)
    
    async def terminate_session(self, session_id: str) -> bool:
        """Termine une session"""
        return self.session_manager.remove_session(session_id)
    
    async def terminate_all_user_sessions(self, user_id: int) -> int:
        """Termine toutes les sessions d'un utilisateur"""
        return self.session_manager.remove_all_user_sessions(user_id)
    
    def get_session_warnings(self) -> Dict[str, Dict[str, Any]]:
        """Obtient les avertissements de timeout"""
        return self.session_manager.get_timeout_warnings()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Obtient les statistiques des sessions"""
        return self.session_manager.get_stats()


# Instances globales
session_timeout_manager = None
session_timeout_service = None

def get_session_timeout_manager() -> SessionTimeoutManager:
    """Obtient l'instance du gestionnaire de timeout de session"""
    global session_timeout_manager
    if session_timeout_manager is None:
        session_timeout_manager = SessionTimeoutManager(
            idle_timeout_minutes=60,
            warn_before_timeout_minutes=5,
            max_concurrent_sessions=5,
            cleanup_interval_minutes=10
        )
    return session_timeout_manager

def get_session_timeout_service() -> SessionTimeoutService:
    """Obtient l'instance du service de timeout de session"""
    global session_timeout_service
    if session_timeout_service is None:
        session_timeout_service = SessionTimeoutService(get_session_timeout_manager())
    return session_timeout_service
