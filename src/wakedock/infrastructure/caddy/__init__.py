"""
Caddy Infrastructure Module

Modular Caddy management for WakeDock following clean architecture.
Refactored from monolithic caddy.py (879 lines) into specialized modules.
"""

from .config import CaddyConfigManager
from .api import CaddyApiClient
from .routes import RoutesManager
from .monitoring import CaddyHealthMonitor
from .facade import CaddyManager, caddy_manager
from .types import *

__all__ = [
    'CaddyManager',  # Façade principale pour compatibilité
    'caddy_manager',  # Instance globale pour compatibilité
    'CaddyConfigManager',
    'CaddyApiClient', 
    'RoutesManager',
    'CaddyHealthMonitor',
    # Types
    'CaddyStatus',
    'RouteStatus',
    'ConfigValidation',
    'BackupResult',
    'RestoreResult',
    'ReloadResult',
    'Route',
    'RouteResult',
    'DomainValidation',
    'CaddyMetrics',
    'HealthStatus',
    'DiagnosticReport'
]