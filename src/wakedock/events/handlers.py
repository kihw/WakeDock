"""
Event handlers and management system for WakeDock.
Provides asynchronous event processing and subscription management.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import weakref
import json

from .types import Event, EventType, EventPriority

logger = logging.getLogger(__name__)


class EventHandler:
    """Base class for event handlers."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    async def handle(self, event: Event) -> None:
        """Handle an event. Override in subclasses."""
        pass
    
    def should_handle(self, event: Event) -> bool:
        """Check if this handler should process the event."""
        return self.enabled


class AsyncEventHandler(EventHandler):
    """Async function-based event handler."""
    
    def __init__(self, name: str, handler_func: Callable[[Event], Any]):
        super().__init__(name)
        self.handler_func = handler_func
    
    async def handle(self, event: Event) -> None:
        """Execute the handler function."""
        try:
            if asyncio.iscoroutinefunction(self.handler_func):
                await self.handler_func(event)
            else:
                self.handler_func(event)
        except Exception as e:
            logger.error(f"Error in event handler {self.name}: {e}")


class EventFilter:
    """Filter events based on criteria."""
    
    def __init__(
        self,
        event_types: Optional[Set[EventType]] = None,
        sources: Optional[Set[str]] = None,
        min_priority: Optional[EventPriority] = None,
        max_age: Optional[timedelta] = None
    ):
        self.event_types = event_types
        self.sources = sources
        self.min_priority = min_priority
        self.max_age = max_age
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check source
        if self.sources and event.source not in self.sources:
            return False
        
        # Check priority
        if self.min_priority and event.priority.value < self.min_priority.value:
            return False
        
        # Check age
        if self.max_age:
            age = datetime.now() - event.timestamp
            if age > self.max_age:
                return False
        
        return True


class EventSubscription:
    """Event subscription with handler and filter."""
    
    def __init__(
        self,
        handler: EventHandler,
        event_filter: Optional[EventFilter] = None,
        priority: int = 0
    ):
        self.handler = handler
        self.filter = event_filter
        self.priority = priority
        self.created_at = datetime.now()
        self.event_count = 0
        self.last_event_at: Optional[datetime] = None
    
    def should_handle(self, event: Event) -> bool:
        """Check if subscription should handle the event."""
        if not self.handler.should_handle(event):
            return False
        
        if self.filter and not self.filter.matches(event):
            return False
        
        return True
    
    async def handle(self, event: Event) -> None:
        """Handle event through subscription."""
        await self.handler.handle(event)
        self.event_count += 1
        self.last_event_at = datetime.now()


class EventQueue:
    """Asynchronous event queue with priority support."""
    
    def __init__(self, maxsize: int = 1000):
        self._queues = {
            EventPriority.CRITICAL: asyncio.Queue(maxsize=maxsize // 4),
            EventPriority.HIGH: asyncio.Queue(maxsize=maxsize // 4),
            EventPriority.NORMAL: asyncio.Queue(maxsize=maxsize // 2),
            EventPriority.LOW: asyncio.Queue(maxsize=maxsize // 4)
        }
        self._stop_event = asyncio.Event()
    
    async def put(self, event: Event) -> None:
        """Add event to queue."""
        queue = self._queues[event.priority]
        try:
            await queue.put(event)
        except asyncio.QueueFull:
            logger.warning(f"Event queue full for priority {event.priority}, dropping event")
    
    async def get(self) -> Optional[Event]:
        """Get next event from queue (priority order)."""
        # Check queues in priority order
        for priority in [EventPriority.CRITICAL, EventPriority.HIGH, EventPriority.NORMAL, EventPriority.LOW]:
            queue = self._queues[priority]
            try:
                return queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
        
        # If no events available, wait for any
        pending = []
        for queue in self._queues.values():
            pending.append(asyncio.create_task(queue.get()))
        
        pending.append(asyncio.create_task(self._stop_event.wait()))
        
        done, pending_tasks = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel remaining tasks
        for task in pending_tasks:
            task.cancel()
        
        # Get result
        for task in done:
            result = task.result()
            if isinstance(result, Event):
                return result
        
        return None
    
    def stop(self) -> None:
        """Stop the queue."""
        self._stop_event.set()
    
    def size(self) -> Dict[EventPriority, int]:
        """Get queue sizes."""
        return {priority: queue.qsize() for priority, queue in self._queues.items()}


class EventManager:
    """Central event management system."""
    
    def __init__(self, max_queue_size: int = 1000, max_history: int = 10000):
        self.subscriptions: Dict[EventType, List[EventSubscription]] = defaultdict(list)
        self.global_subscriptions: List[EventSubscription] = []
        self.event_queue = EventQueue(max_queue_size)
        self.event_history: List[Event] = []
        self.max_history = max_history
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0
        }
    
    async def start(self) -> None:
        """Start the event manager."""
        if self._running:
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("Event manager started")
    
    async def stop(self) -> None:
        """Stop the event manager."""
        if not self._running:
            return
        
        self._running = False
        self.event_queue.stop()
        
        if self._processing_task:
            await self._processing_task
        
        logger.info("Event manager stopped")
    
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any],
        name: Optional[str] = None,
        event_filter: Optional[EventFilter] = None,
        priority: int = 0
    ) -> str:
        """Subscribe to specific event type."""
        handler_name = name or f"handler_{len(self.subscriptions[event_type])}"
        event_handler = AsyncEventHandler(handler_name, handler)
        subscription = EventSubscription(event_handler, event_filter, priority)
        
        self.subscriptions[event_type].append(subscription)
        # Sort by priority (higher first)
        self.subscriptions[event_type].sort(key=lambda s: s.priority, reverse=True)
        
        logger.debug(f"Subscribed {handler_name} to {event_type}")
        return handler_name
    
    def subscribe_global(
        self,
        handler: Callable[[Event], Any],
        name: Optional[str] = None,
        event_filter: Optional[EventFilter] = None,
        priority: int = 0
    ) -> str:
        """Subscribe to all events."""
        handler_name = name or f"global_handler_{len(self.global_subscriptions)}"
        event_handler = AsyncEventHandler(handler_name, handler)
        subscription = EventSubscription(event_handler, event_filter, priority)
        
        self.global_subscriptions.append(subscription)
        self.global_subscriptions.sort(key=lambda s: s.priority, reverse=True)
        
        logger.debug(f"Subscribed {handler_name} globally")
        return handler_name
    
    def unsubscribe(self, event_type: EventType, handler_name: str) -> bool:
        """Unsubscribe from event type."""
        subscriptions = self.subscriptions[event_type]
        for i, subscription in enumerate(subscriptions):
            if subscription.handler.name == handler_name:
                del subscriptions[i]
                logger.debug(f"Unsubscribed {handler_name} from {event_type}")
                return True
        return False
    
    def unsubscribe_global(self, handler_name: str) -> bool:
        """Unsubscribe from global events."""
        for i, subscription in enumerate(self.global_subscriptions):
            if subscription.handler.name == handler_name:
                del self.global_subscriptions[i]
                logger.debug(f"Unsubscribed {handler_name} from global events")
                return True
        return False
    
    async def publish(self, event: Event) -> None:
        """Publish an event."""
        await self.event_queue.put(event)
        self._stats["events_published"] += 1
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        logger.debug(f"Published event: {event.event_type} from {event.source}")
    
    async def publish_sync(self, event: Event) -> None:
        """Publish and process event synchronously."""
        await self._handle_event(event)
    
    async def _process_events(self) -> None:
        """Process events from queue."""
        while self._running:
            try:
                event = await self.event_queue.get()
                if event:
                    await self._handle_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing events: {e}")
                self._stats["events_failed"] += 1
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event."""
        try:
            # Handle specific subscriptions
            subscriptions = self.subscriptions.get(event.event_type, [])
            for subscription in subscriptions:
                if subscription.should_handle(event):
                    try:
                        await subscription.handle(event)
                    except Exception as e:
                        logger.error(f"Error in subscription {subscription.handler.name}: {e}")
            
            # Handle global subscriptions
            for subscription in self.global_subscriptions:
                if subscription.should_handle(event):
                    try:
                        await subscription.handle(event)
                    except Exception as e:
                        logger.error(f"Error in global subscription {subscription.handler.name}: {e}")
            
            self._stats["events_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error handling event {event.event_id}: {e}")
            self._stats["events_failed"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics."""
        return {
            **self._stats,
            "queue_sizes": self.event_queue.size(),
            "history_size": len(self.event_history),
            "subscription_count": sum(len(subs) for subs in self.subscriptions.values()),
            "global_subscription_count": len(self.global_subscriptions)
        }
    
    def get_history(
        self,
        limit: Optional[int] = None,
        event_filter: Optional[EventFilter] = None
    ) -> List[Event]:
        """Get event history."""
        events = self.event_history
        
        if event_filter:
            events = [e for e in events if event_filter.matches(e)]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()


# Global event manager instance
event_manager = EventManager()


# Convenience functions
async def publish_event(event: Event) -> None:
    """Publish an event using the global event manager."""
    await event_manager.publish(event)


def subscribe_to_event(
    event_type: EventType,
    handler: Callable[[Event], Any],
    **kwargs
) -> str:
    """Subscribe to an event using the global event manager."""
    return event_manager.subscribe(event_type, handler, **kwargs)


def subscribe_to_all_events(
    handler: Callable[[Event], Any],
    **kwargs
) -> str:
    """Subscribe to all events using the global event manager."""
    return event_manager.subscribe_global(handler, **kwargs)
