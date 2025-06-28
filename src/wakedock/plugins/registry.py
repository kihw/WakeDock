"""
Plugin registry for WakeDock.
Manages plugin discovery, registration, and metadata.
"""

from typing import Dict, List, Type, Optional, Any
from .base import BasePlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugin discovery and metadata."""
    
    def __init__(self):
        self._registered_plugins: Dict[str, Type[BasePlugin]] = {}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}
    
    def register(self, plugin_class: Type[BasePlugin]) -> None:
        """Register a plugin class."""
        # Create temporary instance to get metadata
        temp_instance = plugin_class()
        metadata = temp_instance.metadata
        
        if metadata.name in self._registered_plugins:
            logger.warning(f"Plugin {metadata.name} already registered, overwriting")
        
        self._registered_plugins[metadata.name] = plugin_class
        self._plugin_metadata[metadata.name] = metadata
        
        logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
    
    def unregister(self, name: str) -> bool:
        """Unregister a plugin."""
        if name in self._registered_plugins:
            del self._registered_plugins[name]
            del self._plugin_metadata[name]
            logger.info(f"Unregistered plugin: {name}")
            return True
        return False
    
    def get_plugin_class(self, name: str) -> Optional[Type[BasePlugin]]:
        """Get a plugin class by name."""
        return self._registered_plugins.get(name)
    
    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name."""
        return self._plugin_metadata.get(name)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[PluginMetadata]:
        """List all registered plugins, optionally filtered by type."""
        plugins = list(self._plugin_metadata.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        
        return sorted(plugins, key=lambda p: p.name)
    
    def search_plugins(self, query: str) -> List[PluginMetadata]:
        """Search plugins by name or description."""
        query = query.lower()
        results = []
        
        for metadata in self._plugin_metadata.values():
            if (query in metadata.name.lower() or 
                query in metadata.description.lower()):
                results.append(metadata)
        
        return sorted(results, key=lambda p: p.name)
    
    def get_dependencies(self, name: str) -> List[str]:
        """Get plugin dependencies."""
        metadata = self.get_metadata(name)
        return metadata.dependencies if metadata else []
    
    def resolve_dependencies(self, name: str) -> List[str]:
        """Resolve plugin dependencies in load order."""
        visited = set()
        resolved = []
        
        def visit(plugin_name: str):
            if plugin_name in visited:
                return
            
            visited.add(plugin_name)
            metadata = self.get_metadata(plugin_name)
            
            if metadata:
                for dep in metadata.dependencies:
                    if dep not in self._registered_plugins:
                        raise ValueError(f"Plugin {plugin_name} depends on {dep} which is not registered")
                    visit(dep)
                
                resolved.append(plugin_name)
        
        visit(name)
        return resolved
    
    def validate_dependencies(self) -> List[str]:
        """Validate all plugin dependencies and return any errors."""
        errors = []
        
        for name, metadata in self._plugin_metadata.items():
            for dep in metadata.dependencies:
                if dep not in self._registered_plugins:
                    errors.append(f"Plugin {name} has unresolved dependency: {dep}")
        
        return errors


def plugin(plugin_class: Type[BasePlugin]) -> Type[BasePlugin]:
    """Decorator to register a plugin class."""
    plugin_registry.register(plugin_class)
    return plugin_class


# Global plugin registry instance
plugin_registry = PluginRegistry()


# Built-in plugin examples
@plugin
class DefaultServicePlugin(BasePlugin):
    """Default service orchestration plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="default_service",
            version="1.0.0",
            description="Default service orchestration plugin",
            author="WakeDock Team",
            plugin_type=PluginType.SERVICE
        )


@plugin
class DefaultMonitoringPlugin(BasePlugin):
    """Default monitoring plugin."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="default_monitoring",
            version="1.0.0",
            description="Default system monitoring plugin",
            author="WakeDock Team",
            plugin_type=PluginType.MONITORING
        )
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect basic system metrics."""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
