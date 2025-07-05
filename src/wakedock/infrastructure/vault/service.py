"""
Service principal Vault pour WakeDock.

Coordonne l'intégration complète de HashiCorp Vault,
incluant l'authentification, la gestion des secrets et le monitoring.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from .client import VaultClient, VaultConnectionError, VaultAuthenticationError
from .config import VaultConfig, VaultSettings, VaultAuthMethod
from .manager import SecretManager, SecretType, SecretPolicy
from .monitor import VaultMonitor

logger = logging.getLogger(__name__)


class VaultService:
    """Service principal pour l'intégration Vault"""
    
    def __init__(self, settings: Optional[VaultSettings] = None):
        self.settings = settings or VaultSettings()
        self.config = VaultConfig(self.settings)
        
        # Composants principaux
        self.client: Optional[VaultClient] = None
        self.secret_manager: Optional[SecretManager] = None
        self.monitor: Optional[VaultMonitor] = None
        
        # État du service
        self._initialized = False
        self._healthy = False
        
        # Métriques du service
        self._service_metrics = {
            "initialization_time": None,
            "last_health_check": None,
            "total_operations": 0,
            "failed_operations": 0,
            "cache_operations": 0
        }
    
    async def initialize(self):
        """Initialiser le service Vault"""
        if self._initialized:
            logger.warning("Vault service already initialized")
            return
        
        start_time = datetime.now()
        
        try:
            logger.info("Initializing Vault service...")
            
            # Vérifier configuration
            if not self._validate_config():
                raise VaultConnectionError("Invalid Vault configuration")
            
            # Initialiser client Vault
            self.client = VaultClient(self.config)
            await self.client.initialize()
            
            # Initialiser gestionnaire de secrets
            self.secret_manager = SecretManager(self.client, self.config)
            
            # Initialiser monitoring
            self.monitor = VaultMonitor(self.client, self.config)
            await self.monitor.start_monitoring()
            
            # Vérifier santé initiale
            health = await self.client.health_check()
            self._healthy = health.get("healthy", False)
            
            if not self._healthy:
                logger.warning("Vault service initialized but not healthy")
            
            # Configurer politiques et engines si nécessaire
            await self._setup_vault_configuration()
            
            self._initialized = True
            init_time = (datetime.now() - start_time).total_seconds()
            self._service_metrics["initialization_time"] = init_time
            
            logger.info(f"Vault service initialized successfully ({init_time:.2f}s)")
            
            # Log événement de démarrage
            if self.monitor:
                await self.monitor.log_auth_event(
                    success=True,
                    details={"action": "service_initialized", "auth_method": self.settings.auth_method.value}
                )
            
        except Exception as e:
            logger.error(f"Failed to initialize Vault service: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Arrêter le service Vault"""
        if not self._initialized:
            return
        
        logger.info("Shutting down Vault service...")
        
        try:
            # Arrêter monitoring
            if self.monitor:
                await self.monitor.stop_monitoring()
            
            # Fermer client
            if self.client:
                await self.client.close()
            
            self._initialized = False
            self._healthy = False
            
            logger.info("Vault service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during Vault service shutdown: {e}")
    
    def _validate_config(self) -> bool:
        """Valider la configuration Vault"""
        # Vérifier URL
        if not self.settings.url:
            logger.error("Vault URL not configured")
            return False
        
        # Vérifier authentification
        auth_method = self.settings.auth_method
        
        if auth_method == VaultAuthMethod.TOKEN:
            if not self.settings.token and not os.getenv("VAULT_TOKEN"):
                logger.error("Token authentication requires VAULT_TOKEN")
                return False
        
        elif auth_method == VaultAuthMethod.APPROLE:
            if not self.settings.role_id or not self.settings.secret_id:
                logger.error("AppRole authentication requires role_id and secret_id")
                return False
        
        elif auth_method == VaultAuthMethod.KUBERNETES:
            if not self.settings.k8s_role:
                logger.error("Kubernetes authentication requires k8s_role")
                return False
        
        elif auth_method == VaultAuthMethod.USERPASS:
            if not self.settings.username or not self.settings.password:
                logger.error("Userpass authentication requires username and password")
                return False
        
        return True
    
    async def _setup_vault_configuration(self):
        """Configurer Vault (engines, politiques)"""
        if not self.client:
            return
        
        try:
            # Cette méthode pourrait configurer des engines et politiques
            # si l'utilisateur a les permissions appropriées
            logger.info("Vault configuration setup completed")
            
        except Exception as e:
            logger.warning(f"Could not setup Vault configuration: {e}")
    
    # === Interface publique pour secrets ===
    
    async def create_secret(
        self,
        path: str,
        data: Union[Dict[str, Any], str],
        secret_type: SecretType = SecretType.CONFIG,
        **kwargs
    ) -> bool:
        """Créer un secret"""
        if not self._ensure_ready():
            return False
        
        try:
            self._service_metrics["total_operations"] += 1
            
            result = await self.secret_manager.create_secret(
                path=path,
                data=data,
                secret_type=secret_type,
                **kwargs
            )
            
            if result and self.monitor:
                await self.monitor.log_secret_operation("create", path)
            
            return result
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to create secret {path}: {e}")
            return False
    
    async def get_secret(
        self,
        path: str,
        version: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Récupérer un secret"""
        if not self._ensure_ready():
            return None
        
        try:
            self._service_metrics["total_operations"] += 1
            
            if use_cache:
                self._service_metrics["cache_operations"] += 1
            
            result = await self.secret_manager.get_secret(
                path=path,
                version=version,
                use_cache=use_cache
            )
            
            if result and self.monitor:
                await self.monitor.log_secret_access(path)
            
            return result
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to get secret {path}: {e}")
            return None
    
    async def update_secret(
        self,
        path: str,
        data: Union[Dict[str, Any], str],
        merge: bool = False
    ) -> bool:
        """Mettre à jour un secret"""
        if not self._ensure_ready():
            return False
        
        try:
            self._service_metrics["total_operations"] += 1
            
            result = await self.secret_manager.update_secret(
                path=path,
                data=data,
                merge=merge
            )
            
            if result and self.monitor:
                await self.monitor.log_secret_operation("update", path)
            
            return result
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to update secret {path}: {e}")
            return False
    
    async def delete_secret(self, path: str, permanent: bool = False) -> bool:
        """Supprimer un secret"""
        if not self._ensure_ready():
            return False
        
        try:
            self._service_metrics["total_operations"] += 1
            
            result = await self.secret_manager.delete_secret(
                path=path,
                permanent=permanent
            )
            
            if result and self.monitor:
                await self.monitor.log_secret_operation("delete", path, details={"permanent": permanent})
            
            return result
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to delete secret {path}: {e}")
            return False
    
    async def rotate_secret(self, path: str, force: bool = False) -> bool:
        """Effectuer la rotation d'un secret"""
        if not self._ensure_ready():
            return False
        
        try:
            self._service_metrics["total_operations"] += 1
            
            result = await self.secret_manager.rotate_secret(
                path=path,
                force=force
            )
            
            if result and self.monitor:
                await self.monitor.log_secret_operation("rotate", path, details={"forced": force})
            
            return result
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to rotate secret {path}: {e}")
            return False
    
    async def list_secrets(self, path: str = "", include_metadata: bool = False) -> List[Union[str, Dict[str, Any]]]:
        """Lister les secrets"""
        if not self._ensure_ready():
            return []
        
        try:
            self._service_metrics["total_operations"] += 1
            
            return await self.secret_manager.list_secrets(
                path=path,
                include_metadata=include_metadata
            )
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to list secrets at {path}: {e}")
            return []
    
    # === Interface publique pour chiffrement ===
    
    async def encrypt_data(self, plaintext: str, key_name: str = "wakedock") -> Optional[str]:
        """Chiffrer des données"""
        if not self._ensure_ready():
            return None
        
        try:
            self._service_metrics["total_operations"] += 1
            
            return await self.client.encrypt_data(plaintext, key_name)
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to encrypt data: {e}")
            return None
    
    async def decrypt_data(self, ciphertext: str, key_name: str = "wakedock") -> Optional[str]:
        """Déchiffrer des données"""
        if not self._ensure_ready():
            return None
        
        try:
            self._service_metrics["total_operations"] += 1
            
            return await self.client.decrypt_data(ciphertext, key_name)
            
        except Exception as e:
            self._service_metrics["failed_operations"] += 1
            logger.error(f"Failed to decrypt data: {e}")
            return None
    
    # === Interface publique pour santé et monitoring ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifier la santé du service"""
        try:
            if not self.client:
                return {
                    "healthy": False,
                    "error": "Service not initialized",
                    "vault_status": None,
                    "service_metrics": self._service_metrics
                }
            
            vault_health = await self.client.health_check()
            self._healthy = vault_health.get("healthy", False)
            self._service_metrics["last_health_check"] = datetime.now().isoformat()
            
            return {
                "healthy": self._healthy,
                "vault_health": vault_health,
                "service_metrics": self._service_metrics,
                "initialized": self._initialized
            }
            
        except Exception as e:
            self._healthy = False
            return {
                "healthy": False,
                "error": str(e),
                "service_metrics": self._service_metrics
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques complètes"""
        metrics = {
            "service": self._service_metrics,
            "vault_client": self.client.get_metrics() if self.client else {},
            "secret_manager": self.secret_manager.get_metrics() if self.secret_manager else {},
            "monitor": {
                "health": self.monitor.get_health_metrics() if self.monitor else {},
                "performance": self.monitor.get_performance_metrics() if self.monitor else {},
                "security": self.monitor.get_security_metrics() if self.monitor else {}
            }
        }
        
        return metrics
    
    def get_events(self, **kwargs) -> List[Dict[str, Any]]:
        """Récupérer les événements"""
        if not self.monitor:
            return []
        
        return self.monitor.get_events(**kwargs)
    
    async def export_prometheus_metrics(self) -> str:
        """Exporter métriques Prometheus"""
        if not self.monitor:
            return ""
        
        return await self.monitor.export_metrics_prometheus()
    
    # === Gestion des politiques ===
    
    def add_secret_policy(self, name: str, policy: SecretPolicy):
        """Ajouter une politique de secret"""
        if self.secret_manager:
            self.secret_manager.add_policy(name, policy)
    
    def add_alert_callback(self, callback):
        """Ajouter callback d'alerte"""
        if self.monitor:
            self.monitor.add_alert_callback(callback)
    
    # === Méthodes utilitaires ===
    
    def is_initialized(self) -> bool:
        """Vérifier si le service est initialisé"""
        return self._initialized
    
    def is_healthy(self) -> bool:
        """Vérifier si le service est en bonne santé"""
        return self._healthy
    
    def _ensure_ready(self) -> bool:
        """S'assurer que le service est prêt"""
        if not self._initialized:
            logger.error("Vault service not initialized")
            return False
        
        if not self.client or not self.secret_manager:
            logger.error("Vault service components not available")
            return False
        
        return True
    
    # === Context manager ===
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.shutdown()


# Instance globale du service Vault
_vault_service: Optional[VaultService] = None


def get_vault_service() -> VaultService:
    """Récupérer l'instance globale du service Vault"""
    global _vault_service
    if _vault_service is None:
        _vault_service = VaultService()
    return _vault_service


async def init_vault_service(settings: Optional[VaultSettings] = None) -> VaultService:
    """Initialiser le service Vault global"""
    global _vault_service
    
    if _vault_service is not None:
        logger.warning("Vault service already initialized")
        return _vault_service
    
    _vault_service = VaultService(settings)
    await _vault_service.initialize()
    
    return _vault_service


async def shutdown_vault_service():
    """Arrêter le service Vault global"""
    global _vault_service
    
    if _vault_service is not None:
        await _vault_service.shutdown()
        _vault_service = None


# === Décorateurs utilitaires ===

def vault_secret(path: str, use_cache: bool = True):
    """Décorateur pour récupérer automatiquement un secret"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            vault_service = get_vault_service()
            
            if not vault_service.is_initialized():
                logger.error("Vault service not initialized for secret retrieval")
                return await func(*args, **kwargs)
            
            secret_data = await vault_service.get_secret(path, use_cache=use_cache)
            
            if secret_data:
                # Injecter secret dans kwargs
                kwargs['vault_secret'] = secret_data
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def vault_encrypt_response(key_name: str = "wakedock"):
    """Décorateur pour chiffrer automatiquement la réponse"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if isinstance(result, str):
                vault_service = get_vault_service()
                
                if vault_service.is_initialized():
                    encrypted = await vault_service.encrypt_data(result, key_name)
                    return encrypted if encrypted else result
            
            return result
        
        return wrapper
    return decorator