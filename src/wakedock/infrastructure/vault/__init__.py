"""
WakeDock HashiCorp Vault Integration

Provides secure secret management capabilities using HashiCorp Vault.
Supports multiple authentication methods, secret engines, and monitoring.
"""

from .client import VaultClient
from .config import VaultConfig, VaultAuthMethod
from .manager import SecretManager
from .monitor import VaultMonitor
from .service import VaultService, get_vault_service

__all__ = [
    "VaultClient",
    "VaultConfig", 
    "VaultAuthMethod",
    "SecretManager",
    "VaultMonitor",
    "VaultService",
    "get_vault_service"
]