"""
Infrastructure de cache intelligent pour WakeDock.

Ce module fournit un système de cache Redis avec stratégies intelligentes:
- Write-through, write-behind, read-through
- Refresh ahead proactif  
- Compression et TTL adaptatifs
- Monitoring des performances
"""

from .intelligent import IntelligentCache, CacheStrategy, CacheConfig
from .manager import CacheManager
from .monitoring import CacheMonitor

__all__ = [
    'IntelligentCache',
    'CacheStrategy', 
    'CacheConfig',
    'CacheManager',
    'CacheMonitor'
]