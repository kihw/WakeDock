"""
Configuration Vault pour WakeDock.

Gère les paramètres de connexion, authentification et politiques
pour l'intégration avec HashiCorp Vault.
"""

import os
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class VaultAuthMethod(str, Enum):
    """Méthodes d'authentification Vault supportées"""
    TOKEN = "token"
    APPROLE = "approle"
    KUBERNETES = "kubernetes"
    USERPASS = "userpass"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


@dataclass
class VaultEngineConfig:
    """Configuration pour un engine Vault"""
    path: str
    engine_type: str
    version: str = "2"
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}


class VaultSettings(BaseSettings):
    """Configuration Vault via variables d'environnement"""
    
    # Activation du service
    enabled: bool = Field(False, env="VAULT_ENABLED")
    
    # Connexion de base
    url: str = Field("http://vault:8200", env="VAULT_ADDR")
    namespace: Optional[str] = Field(None, env="VAULT_NAMESPACE")
    verify_ssl: bool = Field(True, env="VAULT_VERIFY_SSL")
    timeout: int = Field(30, env="VAULT_TIMEOUT")
    
    # Authentification
    auth_method: VaultAuthMethod = Field(VaultAuthMethod.TOKEN, env="VAULT_AUTH_METHOD")
    token: Optional[str] = Field(None, env="VAULT_TOKEN")
    
    # AppRole Auth
    role_id: Optional[str] = Field(None, env="VAULT_ROLE_ID")
    secret_id: Optional[str] = Field(None, env="VAULT_SECRET_ID")
    approle_path: str = Field("approle", env="VAULT_APPROLE_PATH")
    
    # Kubernetes Auth
    k8s_role: Optional[str] = Field(None, env="VAULT_K8S_ROLE")
    k8s_jwt_path: str = Field("/var/run/secrets/kubernetes.io/serviceaccount/token", env="VAULT_K8S_JWT_PATH")
    k8s_auth_path: str = Field("kubernetes", env="VAULT_K8S_AUTH_PATH")
    
    # Userpass Auth
    username: Optional[str] = Field(None, env="VAULT_USERNAME")
    password: Optional[str] = Field(None, env="VAULT_PASSWORD")
    userpass_path: str = Field("userpass", env="VAULT_USERPASS_PATH")
    
    # Cloud Auth (AWS/Azure/GCP)
    aws_role: Optional[str] = Field(None, env="VAULT_AWS_ROLE")
    azure_role: Optional[str] = Field(None, env="VAULT_AZURE_ROLE")
    gcp_role: Optional[str] = Field(None, env="VAULT_GCP_ROLE")
    
    # Configuration des engines
    kv_path: str = Field("secret", env="VAULT_KV_PATH")
    kv_version: str = Field("2", env="VAULT_KV_VERSION")
    
    # Configuration avancée
    max_retries: int = Field(3, env="VAULT_MAX_RETRIES")
    retry_delay: float = Field(1.0, env="VAULT_RETRY_DELAY")
    token_renewal_buffer: int = Field(300, env="VAULT_TOKEN_RENEWAL_BUFFER")  # 5 minutes
    
    # Cache et performance
    cache_secrets: bool = Field(True, env="VAULT_CACHE_SECRETS")
    cache_ttl: int = Field(300, env="VAULT_CACHE_TTL")  # 5 minutes
    batch_size: int = Field(10, env="VAULT_BATCH_SIZE")
    
    # Monitoring
    enable_monitoring: bool = Field(True, env="VAULT_ENABLE_MONITORING")
    health_check_interval: int = Field(60, env="VAULT_HEALTH_CHECK_INTERVAL")
    metrics_path: str = Field("wakedock/metrics", env="VAULT_METRICS_PATH")
    
    # Audit et sécurité
    enable_audit: bool = Field(True, env="VAULT_ENABLE_AUDIT")
    audit_path: str = Field("wakedock/audit", env="VAULT_AUDIT_PATH")
    encrypt_cache: bool = Field(True, env="VAULT_ENCRYPT_CACHE")
    
    class Config:
        env_file = ".env"
        env_prefix = "VAULT_"
        case_sensitive = False
        
    @validator("url")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("VAULT_URL must start with http:// or https://")
        return v.rstrip("/")
    
    @validator("auth_method")
    def validate_auth_method(cls, v):
        if isinstance(v, str):
            try:
                return VaultAuthMethod(v.lower())
            except ValueError:
                valid_methods = [method.value for method in VaultAuthMethod]
                raise ValueError(f"Invalid auth method. Must be one of: {valid_methods}")
        return v


class VaultConfig:
    """Configuration principale Vault"""
    
    def __init__(self, settings: Optional[VaultSettings] = None):
        self.settings = settings or VaultSettings()
        self._engines = self._setup_default_engines()
        self._policies = self._setup_default_policies()
    
    def _setup_default_engines(self) -> Dict[str, VaultEngineConfig]:
        """Configuration des engines par défaut"""
        return {
            "secrets": VaultEngineConfig(
                path=self.settings.kv_path,
                engine_type="kv",
                version=self.settings.kv_version,
                options={"max_versions": 10}
            ),
            "database": VaultEngineConfig(
                path="database",
                engine_type="database",
                options={"default_ttl": "1h", "max_ttl": "24h"}
            ),
            "pki": VaultEngineConfig(
                path="pki",
                engine_type="pki",
                options={"max_lease_ttl": "8760h"}  # 1 year
            ),
            "transit": VaultEngineConfig(
                path="transit",
                engine_type="transit",
                options={"type": "aes256-gcm96"}
            )
        }
    
    def _setup_default_policies(self) -> Dict[str, str]:
        """Politiques d'accès par défaut"""
        return {
            "wakedock-admin": """
                # Admin policy for WakeDock
                path "secret/*" {
                    capabilities = ["create", "read", "update", "delete", "list"]
                }
                path "database/*" {
                    capabilities = ["create", "read", "update", "delete", "list"]
                }
                path "pki/*" {
                    capabilities = ["create", "read", "update", "delete", "list"]
                }
                path "transit/*" {
                    capabilities = ["create", "read", "update", "delete", "list"]
                }
                path "sys/mounts" {
                    capabilities = ["read", "list"]
                }
                path "sys/health" {
                    capabilities = ["read"]
                }
            """,
            "wakedock-service": """
                # Service policy for WakeDock services
                path "secret/data/wakedock/*" {
                    capabilities = ["read", "list"]
                }
                path "secret/data/services/{{identity.entity.name}}/*" {
                    capabilities = ["create", "read", "update", "delete", "list"]
                }
                path "database/creds/{{identity.entity.name}}" {
                    capabilities = ["read"]
                }
                path "transit/encrypt/wakedock" {
                    capabilities = ["update"]
                }
                path "transit/decrypt/wakedock" {
                    capabilities = ["update"]
                }
            """,
            "wakedock-readonly": """
                # Read-only policy for monitoring
                path "secret/data/wakedock/*" {
                    capabilities = ["read", "list"]
                }
                path "sys/health" {
                    capabilities = ["read"]
                }
                path "sys/metrics" {
                    capabilities = ["read"]
                }
            """
        }
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Configuration d'authentification basée sur la méthode choisie"""
        method = self.settings.auth_method
        
        config = {
            "method": method.value,
            "url": self.settings.url,
            "verify": self.settings.verify_ssl,
            "timeout": self.settings.timeout,
            "namespace": self.settings.namespace
        }
        
        if method == VaultAuthMethod.TOKEN:
            config.update({
                "token": self.settings.token or os.getenv("VAULT_TOKEN")
            })
        
        elif method == VaultAuthMethod.APPROLE:
            config.update({
                "role_id": self.settings.role_id,
                "secret_id": self.settings.secret_id,
                "mount_point": self.settings.approle_path
            })
        
        elif method == VaultAuthMethod.KUBERNETES:
            config.update({
                "role": self.settings.k8s_role,
                "jwt_path": self.settings.k8s_jwt_path,
                "mount_point": self.settings.k8s_auth_path
            })
        
        elif method == VaultAuthMethod.USERPASS:
            config.update({
                "username": self.settings.username,
                "password": self.settings.password,
                "mount_point": self.settings.userpass_path
            })
        
        elif method == VaultAuthMethod.AWS:
            config.update({
                "role": self.settings.aws_role,
                "mount_point": "aws"
            })
        
        elif method == VaultAuthMethod.AZURE:
            config.update({
                "role": self.settings.azure_role,
                "mount_point": "azure"
            })
        
        elif method == VaultAuthMethod.GCP:
            config.update({
                "role": self.settings.gcp_role,
                "mount_point": "gcp"
            })
        
        return config
    
    def get_engine_config(self, engine_name: str) -> Optional[VaultEngineConfig]:
        """Récupérer la configuration d'un engine"""
        return self._engines.get(engine_name)
    
    def get_policy(self, policy_name: str) -> Optional[str]:
        """Récupérer une politique d'accès"""
        return self._policies.get(policy_name)
    
    def get_secret_path(self, path: str) -> str:
        """Construire le chemin complet d'un secret"""
        kv_config = self._engines["secrets"]
        if kv_config.version == "2":
            return f"{kv_config.path}/data/{path.lstrip('/')}"
        else:
            return f"{kv_config.path}/{path.lstrip('/')}"
    
    def get_secret_metadata_path(self, path: str) -> str:
        """Construire le chemin metadata d'un secret (KV v2 seulement)"""
        kv_config = self._engines["secrets"]
        if kv_config.version == "2":
            return f"{kv_config.path}/metadata/{path.lstrip('/')}"
        else:
            raise ValueError("Metadata path only available for KV v2")