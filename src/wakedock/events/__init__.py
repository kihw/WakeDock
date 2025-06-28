"""
Event system for WakeDock.
Provides asynchronous event handling and notifications.
"""

from .handlers import EventManager, event_manager
from .types import Event, EventType, EventPriority

__all__ = ["EventManager", "event_manager", "Event", "EventType", "EventPriority"]
