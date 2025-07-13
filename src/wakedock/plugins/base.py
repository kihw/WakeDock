"""
Base plugin classes and plugin manager for WakeDock.
Provides the foundation for the extensible plugin system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
import importlib
import inspect
from pathlib import Path

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins supported by WakeDock."""
    SERVICE = "service"           # Service orchestration plugins
    MONITORING = "monitoring"     # Monitoring and metrics plugins
    NOTIFICATION = "notification" # Notification plugins
    STORAGE = "storage"          # Storage backend plugins
    AUTH = "auth"                # Authentication plugins
    PROXY = "proxy"              # Proxy configuration plugins
    MIDDLEWARE = "middleware"     # API middleware plugins


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    enabled: bool = True


class PluginHook:
    """Decorator for marking plugin hook methods."""
    
    def __init__(self, hook_name: str, priority: int = 0):
        self.hook_name = hook_name
        self.priority = priority
    
    def __call__(self, func):
        func._plugin_hook = self.hook_name
        func._hook_priority = self.priority
        return func


class BasePlugin(ABC):
    """Base class for all WakeDock plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._hooks: Dict[str, List[Callable]] = {}
        self._initialized = False
        self._register_hooks()
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    async def initialize(self) -> None:
        """Initialize the plugin. Override for custom initialization."""
        self._initialized = True
        logger.info(f"Plugin {self.metadata.name} initialized")
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources. Override for custom cleanup."""
        self._initialized = False
        logger.info(f"Plugin {self.metadata.name} cleaned up")
    
    def _register_hooks(self):
        """Register hook methods."""
        for method_name in dir(self):
            method = getattr(self, method_name)
            if hasattr(method, '_plugin_hook'):
                hook_name = method._plugin_hook
                priority = getattr(method, '_hook_priority', 0)
                
                if hook_name not in self._hooks:
                    self._hooks[hook_name] = []
                
                self._hooks[hook_name].append((priority, method))
                # Sort by priority (higher priority first)
                self._hooks[hook_name].sort(key=lambda x: x[0], reverse=True)
    
    def get_hooks(self, hook_name: str) -> List[Callable]:
        """Get hook methods for a specific hook name."""
        return [method for _, method in self._hooks.get(hook_name, [])]
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration. Override for custom validation."""
        if self.metadata.config_schema:
            try:
                import jsonschema
                jsonschema.validate(config, self.metadata.config_schema)
                logger.debug(f"Plugin {self.metadata.name} configuration validated successfully")
                return True
            except ImportError:
                logger.warning("jsonschema library not available, skipping schema validation")
                return True
            except jsonschema.ValidationError as e:
                logger.error(f"Plugin {self.metadata.name} configuration validation failed: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during config validation for plugin {self.metadata.name}: {e}")
                return False
        return True


class ServicePlugin(BasePlugin):
    """Base class for service orchestration plugins."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="base_service",
            version="1.0.0",
            description="Base service plugin",
            author="WakeDock",
            plugin_type=PluginType.SERVICE
        )
    
    @PluginHook("service.before_start", priority=0)
    async def before_service_start(self, service_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Called before a service starts. Can modify service config."""
        return config
    
    @PluginHook("service.after_start", priority=0)
    async def after_service_start(self, service_id: str, container_info: Dict[str, Any]) -> None:
        """Called after a service starts successfully."""
        pass
    
    @PluginHook("service.before_stop", priority=0)
    async def before_service_stop(self, service_id: str) -> None:
        """Called before a service stops."""
        pass
    
    @PluginHook("service.after_stop", priority=0)
    async def after_service_stop(self, service_id: str) -> None:
        """Called after a service stops."""
        pass


class MonitoringPlugin(BasePlugin):
    """Base class for monitoring plugins."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="base_monitoring",
            version="1.0.0", 
            description="Base monitoring plugin",
            author="WakeDock",
            plugin_type=PluginType.MONITORING
        )
    
    @PluginHook("monitoring.collect_metrics", priority=0)
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect custom metrics."""
        return {}
    
    @PluginHook("monitoring.health_check", priority=0)
    async def health_check(self, service_id: str) -> bool:
        """Perform health check for a service."""
        return True


class NotificationPlugin(BasePlugin):
    """Base class for notification plugins."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="base_notification",
            version="1.0.0",
            description="Base notification plugin", 
            author="WakeDock",
            plugin_type=PluginType.NOTIFICATION
        )
    
    @PluginHook("notification.send", priority=0)
    async def send_notification(self, event: str, data: Dict[str, Any]) -> bool:
        """Send a notification."""
        return True


class PluginManager:
    """Manages plugin loading, initialization, and execution."""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.hooks: Dict[str, List[BasePlugin]] = {}
        self._plugin_paths: List[Path] = []
    
    def add_plugin_path(self, path: Path) -> None:
        """Add a directory to search for plugins."""
        if path not in self._plugin_paths:
            self._plugin_paths.append(path)
    
    async def load_plugin(self, plugin_class: Type[BasePlugin], config: Optional[Dict[str, Any]] = None) -> None:
        """Load and initialize a plugin."""
        try:
            plugin = plugin_class(config)
            
            # Validate configuration
            if not plugin.validate_config(plugin.config):
                raise ValueError(f"Invalid configuration for plugin {plugin.metadata.name}")
            
            # Initialize plugin
            await plugin.initialize()
            
            # Register plugin
            self.plugins[plugin.metadata.name] = plugin
            
            # Register hooks
            for hook_name in plugin._hooks:
                if hook_name not in self.hooks:
                    self.hooks[hook_name] = []
                self.hooks[hook_name].append(plugin)
            
            logger.info(f"Plugin {plugin.metadata.name} loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_class.__name__}: {e}")
            raise
    
    async def load_plugins_from_directory(self, directory: Path) -> None:
        """Load all plugins from a directory."""
        if not directory.exists():
            logger.warning(f"Plugin directory {directory} does not exist")
            return
        
        for plugin_file in directory.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BasePlugin) and 
                        obj != BasePlugin):
                        
                        await self.load_plugin(obj)
                
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")
    
    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all plugins for a specific hook."""
        results = []
        
        if hook_name not in self.hooks:
            return results
        
        for plugin in self.hooks[hook_name]:
            if not plugin._initialized:
                continue
            
            hook_methods = plugin.get_hooks(hook_name)
            
            for method in hook_methods:
                try:
                    if asyncio.iscoroutinefunction(method):
                        result = await method(*args, **kwargs)
                    else:
                        result = method(*args, **kwargs)
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(
                        f"Error executing hook {hook_name} in plugin {plugin.metadata.name}: {e}"
                    )
        
        return results
    
    async def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    async def list_plugins(self) -> List[PluginMetadata]:
        """List all loaded plugins."""
        return [plugin.metadata for plugin in self.plugins.values()]
    
    async def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        plugin = self.plugins.get(name)
        if plugin:
            plugin.metadata.enabled = True
            if not plugin._initialized:
                await plugin.initialize()
            return True
        return False
    
    async def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self.plugins.get(name)
        if plugin:
            plugin.metadata.enabled = False
            if plugin._initialized:
                await plugin.cleanup()
            return True
        return False
    
    async def unload_plugin(self, name: str) -> bool:
        """Unload a plugin completely."""
        plugin = self.plugins.get(name)
        if not plugin:
            return False
        
        # Cleanup plugin
        if plugin._initialized:
            await plugin.cleanup()
        
        # Remove from hooks
        for hook_name, hook_plugins in self.hooks.items():
            if plugin in hook_plugins:
                hook_plugins.remove(plugin)
        
        # Remove from plugins
        del self.plugins[name]
        
        logger.info(f"Plugin {name} unloaded")
        return True
    
    async def reload_plugin(self, name: str) -> bool:
        """Reload a plugin."""
        plugin = self.plugins.get(name)
        if not plugin:
            return False
        
        # Store config
        config = plugin.config
        plugin_class = type(plugin)
        
        # Unload
        await self.unload_plugin(name)
        
        # Reload
        await self.load_plugin(plugin_class, config)
        return True
    
    async def cleanup_all_plugins(self) -> None:
        """Cleanup all plugins."""
        for plugin in self.plugins.values():
            if plugin._initialized:
                await plugin.cleanup()
        
        self.plugins.clear()
        self.hooks.clear()
        logger.info("All plugins cleaned up")


# Global plugin manager instance
plugin_manager = PluginManager()
