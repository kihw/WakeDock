"""
WakeDock plugin system initialization.
Provides extensible plugin architecture for WakeDock.
"""

from .base import BasePlugin, PluginManager
from .registry import plugin_registry

__all__ = ["BasePlugin", "PluginManager", "plugin_registry"]
