"""
Service de Configuration de Sécurité Centralisé
Initialise et configure tous les services de sécurité
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from .jwt_rotation import JWTRotationService, JWTRotationManager
from .session_timeout import SessionTimeoutManager, SessionTimeoutService
from .intrusion_detection import IntrusionDetectionSystem
from .ids_middleware import IntrusionDetectionMiddleware
from .config import SecurityConfig, SecurityConfigManager

logger = logging.getLogger(__name__)

@dataclass
class SecurityServices:
    """Container pour tous les services de sécurité"""
    jwt_rotation_service: JWTRotationService
    jwt_rotation_manager: JWTRotationManager
    session_timeout_manager: SessionTimeoutManager
    session_timeout_service: SessionTimeoutService
    intrusion_detection_system: IntrusionDetectionSystem
    security_config: SecurityConfig

class SecurityManager:
    """Gestionnaire central de la sécurité"""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.services: Optional[SecurityServices] = None
        self._initialized = False
        self._background_tasks = []
    
    async def initialize(self, app_config: Optional[Dict[str, Any]] = None) -> SecurityServices:
        """Initialise tous les services de sécurité"""
        
        if self._initialized:
            return self.services
        
        logger.info("Initialisation des services de sécurité...")
        
        try:
            # Charger la configuration de sécurité
            if app_config:
                config_manager = SecurityConfigManager()
                self.config = config_manager.load_config(app_config.get("security", {}))
            
            # Initialiser le service de rotation JWT
            jwt_rotation_service = JWTRotationService(
                secret_key=app_config.get("jwt_secret_key", "default-secret-key"),
                algorithm=self.config.encryption.jwt_algorithm,
                access_token_expire_minutes=self.config.session.access_token_expire_minutes,
                refresh_token_expire_days=self.config.session.refresh_token_expire_days,
                rotation_threshold_minutes=5  # Rotation 5 minutes avant expiration
            )
            
            jwt_rotation_manager = JWTRotationManager(jwt_rotation_service)
            
            # Initialiser le gestionnaire de timeout de session
            session_timeout_manager = SessionTimeoutManager(
                idle_timeout_minutes=self.config.session.idle_timeout_minutes,
                warn_before_timeout_minutes=self.config.session.warn_before_timeout_minutes,
                max_concurrent_sessions=self.config.session.max_concurrent_sessions,
                cleanup_interval_minutes=10
            )
            
            session_timeout_service = SessionTimeoutService(session_timeout_manager)
            
            # Initialiser le système de détection d'intrusion
            intrusion_detection_system = IntrusionDetectionSystem()
            
            # Créer le container de services
            self.services = SecurityServices(
                jwt_rotation_service=jwt_rotation_service,
                jwt_rotation_manager=jwt_rotation_manager,
                session_timeout_manager=session_timeout_manager,
                session_timeout_service=session_timeout_service,
                intrusion_detection_system=intrusion_detection_system,
                security_config=self.config
            )
            
            # Démarrer les services
            await self._start_background_services()
            
            self._initialized = True
            logger.info("Services de sécurité initialisés avec succès")
            
            return self.services
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des services de sécurité: {e}")
            raise
    
    async def _start_background_services(self):
        """Démarre les services en arrière-plan"""
        
        if not self.services:
            return
        
        # Démarrer le service de rotation JWT
        await self.services.jwt_rotation_manager.start()
        
        # Démarrer le service de timeout de session
        await self.services.session_timeout_service.start()
        
        # Démarrer le nettoyage automatique de l'IDS
        ids_cleanup_task = asyncio.create_task(
            self.services.intrusion_detection_system.cleanup_old_data()
        )
        self._background_tasks.append(ids_cleanup_task)
        
        logger.info("Services de sécurité en arrière-plan démarrés")
    
    async def shutdown(self):
        """Arrête tous les services de sécurité"""
        
        if not self._initialized or not self.services:
            return
        
        logger.info("Arrêt des services de sécurité...")
        
        try:
            # Arrêter les services principaux
            await self.services.jwt_rotation_manager.stop()
            await self.services.session_timeout_service.stop()
            
            # Arrêter les tâches en arrière-plan
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._background_tasks.clear()
            self._initialized = False
            
            logger.info("Services de sécurité arrêtés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt des services de sécurité: {e}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Obtient le statut de sécurité général"""
        
        if not self._initialized or not self.services:
            return {
                "status": "not_initialized",
                "services": {},
                "config": {}
            }
        
        # Statistiques JWT
        jwt_stats = self.services.jwt_rotation_service.get_rotation_stats()
        
        # Statistiques de session
        session_stats = self.services.session_timeout_service.get_session_stats()
        
        # Statistiques IDS
        ids_stats = self.services.intrusion_detection_system.get_statistics()
        
        return {
            "status": "initialized",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "jwt_rotation": {
                    "enabled": True,
                    "stats": jwt_stats
                },
                "session_timeout": {
                    "enabled": True,
                    "stats": session_stats
                },
                "intrusion_detection": {
                    "enabled": True,
                    "stats": ids_stats
                }
            },
            "config": {
                "environment": self.config.environment,
                "debug_mode": self.config.debug_mode,
                "features": {
                    "mfa_enabled": self.config.features.enable_mfa,
                    "rate_limiting": self.config.features.enable_api_rate_limiting,
                    "intrusion_detection": self.config.features.enable_intrusion_detection,
                    "session_rotation": self.config.session.enable_session_rotation
                }
            }
        }
    
    def get_security_config(self) -> SecurityConfig:
        """Obtient la configuration de sécurité"""
        return self.config
    
    def update_security_config(self, updates: Dict[str, Any]) -> SecurityConfig:
        """Met à jour la configuration de sécurité"""
        
        config_manager = SecurityConfigManager()
        self.config = config_manager.update_config(updates)
        
        # Ici, vous pourriez redémarrer les services affectés
        # par les changements de configuration
        
        logger.info("Configuration de sécurité mise à jour")
        return self.config
    
    async def run_security_audit(self) -> Dict[str, Any]:
        """Exécute un audit de sécurité"""
        
        if not self._initialized or not self.services:
            return {"error": "Services de sécurité non initialisés"}
        
        audit_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_type": "security_audit",
            "results": {}
        }
        
        # Audit JWT
        jwt_stats = self.services.jwt_rotation_service.get_rotation_stats()
        audit_results["results"]["jwt_rotation"] = {
            "status": "ok" if jwt_stats["successful_rotations"] > 0 or jwt_stats["total_rotations"] == 0 else "warning",
            "total_rotations": jwt_stats["total_rotations"],
            "failed_rotations": jwt_stats["failed_rotations"],
            "revoked_tokens": jwt_stats["revoked_tokens_count"]
        }
        
        # Audit sessions
        session_stats = self.services.session_timeout_service.get_session_stats()
        audit_results["results"]["session_management"] = {
            "status": "ok",
            "active_sessions": session_stats["active_sessions_count"],
            "expired_sessions": session_stats["expired_sessions"],
            "concurrent_sessions_rejected": session_stats.get("concurrent_sessions_rejected", 0)
        }
        
        # Audit IDS
        ids_stats = self.services.intrusion_detection_system.get_statistics()
        top_threats = self.services.intrusion_detection_system.get_top_threats(5)
        
        audit_results["results"]["intrusion_detection"] = {
            "status": "warning" if ids_stats["active_threats"] > 0 else "ok",
            "total_events": ids_stats["total_events"],
            "blocked_attacks": ids_stats["blocked_attacks"],
            "active_threats": ids_stats["active_threats"],
            "blocked_ips": ids_stats["blocked_ips_count"],
            "top_threats": top_threats
        }
        
        # Recommandations
        recommendations = []
        
        if jwt_stats["failed_rotations"] > 0:
            recommendations.append({
                "priority": "medium",
                "category": "jwt",
                "message": f"{jwt_stats['failed_rotations']} échecs de rotation JWT détectés"
            })
        
        if ids_stats["active_threats"] > 0:
            recommendations.append({
                "priority": "high",
                "category": "security",
                "message": f"{ids_stats['active_threats']} menaces actives détectées"
            })
        
        if ids_stats["blocked_ips_count"] > 10:
            recommendations.append({
                "priority": "medium",
                "category": "security",
                "message": f"{ids_stats['blocked_ips_count']} adresses IP bloquées - Vérifier la configuration"
            })
        
        audit_results["recommendations"] = recommendations
        
        # Score de sécurité global
        security_score = 100
        
        if jwt_stats["failed_rotations"] > 0:
            security_score -= 10
        
        if ids_stats["active_threats"] > 0:
            security_score -= (ids_stats["active_threats"] * 5)
        
        if session_stats.get("concurrent_sessions_rejected", 0) > 10:
            security_score -= 5
        
        audit_results["security_score"] = max(security_score, 0)
        
        return audit_results
    
    def get_security_recommendations(self) -> list[Dict[str, Any]]:
        """Obtient les recommandations de sécurité"""
        
        recommendations = []
        
        if not self._initialized:
            recommendations.append({
                "priority": "high",
                "category": "system",
                "message": "Services de sécurité non initialisés"
            })
            return recommendations
        
        # Vérifier la configuration
        if self.config.environment == "production":
            if self.config.debug_mode:
                recommendations.append({
                    "priority": "critical",
                    "category": "config",
                    "message": "Mode debug activé en production"
                })
            
            if not self.config.features.enable_mfa:
                recommendations.append({
                    "priority": "high",
                    "category": "authentication",
                    "message": "MFA désactivé en production"
                })
            
            if not self.config.features.enable_intrusion_detection:
                recommendations.append({
                    "priority": "medium",
                    "category": "security",
                    "message": "Détection d'intrusion désactivée"
                })
        
        # Vérifier les paramètres de session
        if self.config.session.idle_timeout_minutes > 120:
            recommendations.append({
                "priority": "medium",
                "category": "session",
                "message": "Timeout de session trop long (>2h)"
            })
        
        # Vérifier les paramètres de mot de passe
        if self.config.password_policy.min_length < 8:
            recommendations.append({
                "priority": "high",
                "category": "password",
                "message": "Longueur minimale de mot de passe trop faible"
            })
        
        return recommendations


# Instance globale
security_manager = None

def get_security_manager() -> SecurityManager:
    """Obtient l'instance du gestionnaire de sécurité"""
    global security_manager
    if security_manager is None:
        security_manager = SecurityManager()
    return security_manager

async def initialize_security(app_config: Optional[Dict[str, Any]] = None) -> SecurityServices:
    """Initialise les services de sécurité"""
    manager = get_security_manager()
    return await manager.initialize(app_config)

async def shutdown_security():
    """Arrête les services de sécurité"""
    manager = get_security_manager()
    await manager.shutdown()
