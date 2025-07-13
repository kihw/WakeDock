"""
WebSocket Batch Manager for Python Backend
Optimizes real-time communication by batching messages
"""

import asyncio
import json
import time
import gzip
import base64
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Callable
from enum import Enum

class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class WebSocketMessage:
    type: str
    data: Any
    timestamp: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class BatchedMessage:
    type: str = "batch"
    messages: List[Dict[str, Any]] = None
    count: int = 0
    timestamp: str = None
    compressed: bool = False
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        self.count = len(self.messages)

class MessageCompressor:
    """Handle message compression for large payloads"""
    
    COMPRESSION_THRESHOLD = 1024  # 1KB
    
    @staticmethod
    def should_compress(data: str) -> bool:
        return len(data) > MessageCompressor.COMPRESSION_THRESHOLD
    
    @staticmethod
    def compress(data: Any) -> tuple[str, bool]:
        """Compress data if it exceeds threshold"""
        json_str = json.dumps(data, default=str)
        
        if MessageCompressor.should_compress(json_str):
            # Compress using gzip
            compressed = gzip.compress(json_str.encode('utf-8'))
            encoded = base64.b64encode(compressed).decode('utf-8')
            return f"compressed:{encoded}", True
        
        return json_str, False
    
    @staticmethod
    def decompress(data: str) -> Any:
        """Decompress data if it was compressed"""
        if data.startswith("compressed:"):
            encoded = data[11:]  # Remove "compressed:" prefix
            compressed = base64.b64decode(encoded.encode('utf-8'))
            json_str = gzip.decompress(compressed).decode('utf-8')
            return json.loads(json_str)
        
        return json.loads(data)

class WebSocketBatchManager:
    """Manages message batching for WebSocket connections"""
    
    def __init__(self):
        # Configuration
        self.BATCH_SIZE = 10
        self.BATCH_INTERVAL = 0.1  # 100ms
        self.HIGH_PRIORITY_INTERVAL = 0.05  # 50ms
        self.MAX_BATCH_SIZE = 50
        self.COMPRESSION_ENABLED = True
        
        # Message queues per connection
        self.message_queues: Dict[str, deque] = defaultdict(deque)
        self.high_priority_queues: Dict[str, deque] = defaultdict(deque)
        
        # Batch timers per connection
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.high_priority_timers: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self.stats = {
            'messages_queued': 0,
            'batches_sent': 0,
            'bytes_saved_compression': 0,
            'messages_sent': 0
        }
        
        # Connection manager reference
        self.websocket_manager: Optional[Any] = None
    
    def set_websocket_manager(self, manager):
        """Set the WebSocket manager for sending messages"""
        self.websocket_manager = manager
    
    async def queue_message(self, connection_id: str, message: WebSocketMessage) -> None:
        """Queue a message for batching"""
        self.stats['messages_queued'] += 1
        
        # Convert message to dict for serialization
        message_dict = {
            'type': message.type,
            'data': message.data,
            'timestamp': message.timestamp,
            'priority': message.priority.value
        }
        
        # Handle high priority messages
        if message.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
            self.high_priority_queues[connection_id].append(message_dict)
            await self._schedule_high_priority_flush(connection_id)
            return
        
        # Regular priority messages
        self.message_queues[connection_id].append(message_dict)
        
        # Check if we should flush immediately
        if len(self.message_queues[connection_id]) >= self.BATCH_SIZE:
            await self.flush_batch(connection_id)
        else:
            await self._schedule_batch_flush(connection_id)
        
        # Safety valve - prevent memory buildup
        if len(self.message_queues[connection_id]) >= self.MAX_BATCH_SIZE:
            print(f"WARNING: Connection {connection_id} queue exceeded max size, flushing")
            await self.flush_batch(connection_id)
    
    async def send_immediate(self, connection_id: str, message: WebSocketMessage) -> None:
        """Send a message immediately (bypass batching)"""
        if not self.websocket_manager:
            print("WebSocket manager not set")
            return
        
        message_dict = {
            'type': message.type,
            'data': message.data,
            'timestamp': message.timestamp,
            'priority': message.priority.value
        }
        
        # Compress if needed
        payload, is_compressed = MessageCompressor.compress(message_dict)
        
        if is_compressed:
            original_size = len(json.dumps(message_dict, default=str))
            self.stats['bytes_saved_compression'] += original_size - len(payload)
        
        await self.websocket_manager.send_to_connection(connection_id, payload)
        self.stats['messages_sent'] += 1
    
    async def flush_batch(self, connection_id: str) -> None:
        """Flush all queued messages for a connection"""
        if connection_id not in self.message_queues:
            return
        
        messages = list(self.message_queues[connection_id])
        self.message_queues[connection_id].clear()
        
        if not messages:
            return
        
        # Cancel any pending batch timer
        if connection_id in self.batch_timers:
            self.batch_timers[connection_id].cancel()
            del self.batch_timers[connection_id]
        
        await self._send_batch(connection_id, messages)
    
    async def flush_high_priority_batch(self, connection_id: str) -> None:
        """Flush high priority messages"""
        if connection_id not in self.high_priority_queues:
            return
        
        messages = list(self.high_priority_queues[connection_id])
        self.high_priority_queues[connection_id].clear()
        
        if not messages:
            return
        
        # Cancel any pending high priority timer
        if connection_id in self.high_priority_timers:
            self.high_priority_timers[connection_id].cancel()
            del self.high_priority_timers[connection_id]
        
        await self._send_batch(connection_id, messages, is_high_priority=True)
    
    async def _send_batch(self, connection_id: str, messages: List[Dict], is_high_priority: bool = False) -> None:
        """Send a batch of messages"""
        if not self.websocket_manager or not messages:
            return
        
        batch = BatchedMessage(
            messages=messages,
            timestamp=datetime.now().isoformat()
        )
        
        # Compress batch if enabled and beneficial
        payload, is_compressed = MessageCompressor.compress(asdict(batch))
        
        if is_compressed:
            batch.compressed = True
            original_size = len(json.dumps(asdict(batch), default=str))
            self.stats['bytes_saved_compression'] += original_size - len(payload)
        
        # Add batch prefix for client identification
        if is_compressed:
            payload = f"batch:{payload}"
        else:
            payload = json.dumps(asdict(batch), default=str)
        
        await self.websocket_manager.send_to_connection(connection_id, payload)
        
        self.stats['batches_sent'] += 1
        self.stats['messages_sent'] += len(messages)
        
        print(f"Sent batch of {len(messages)} messages to {connection_id} "
              f"{'(high priority)' if is_high_priority else ''} "
              f"{'(compressed)' if is_compressed else ''}")
    
    async def _schedule_batch_flush(self, connection_id: str) -> None:
        """Schedule a batch flush after the batch interval"""
        if connection_id in self.batch_timers:
            return  # Timer already scheduled
        
        async def flush_after_delay():
            try:
                await asyncio.sleep(self.BATCH_INTERVAL)
                await self.flush_batch(connection_id)
            except asyncio.CancelledError:
                pass  # Timer was cancelled
        
        self.batch_timers[connection_id] = asyncio.create_task(flush_after_delay())
    
    async def _schedule_high_priority_flush(self, connection_id: str) -> None:
        """Schedule a high priority batch flush"""
        if connection_id in self.high_priority_timers:
            return  # Timer already scheduled
        
        async def flush_after_delay():
            try:
                await asyncio.sleep(self.HIGH_PRIORITY_INTERVAL)
                await self.flush_high_priority_batch(connection_id)
            except asyncio.CancelledError:
                pass
        
        self.high_priority_timers[connection_id] = asyncio.create_task(flush_after_delay())
    
    async def flush_all_connections(self) -> None:
        """Flush all pending messages for all connections"""
        tasks = []
        
        # Flush high priority first
        for connection_id in list(self.high_priority_queues.keys()):
            if self.high_priority_queues[connection_id]:
                tasks.append(self.flush_high_priority_batch(connection_id))
        
        # Then regular priority
        for connection_id in list(self.message_queues.keys()):
            if self.message_queues[connection_id]:
                tasks.append(self.flush_batch(connection_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def cleanup_connection(self, connection_id: str) -> None:
        """Clean up resources for a disconnected connection"""
        # Cancel timers
        if connection_id in self.batch_timers:
            self.batch_timers[connection_id].cancel()
            del self.batch_timers[connection_id]
        
        if connection_id in self.high_priority_timers:
            self.high_priority_timers[connection_id].cancel()
            del self.high_priority_timers[connection_id]
        
        # Clear queues
        if connection_id in self.message_queues:
            del self.message_queues[connection_id]
        
        if connection_id in self.high_priority_queues:
            del self.high_priority_queues[connection_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        total_queued = sum(len(q) for q in self.message_queues.values())
        total_high_priority = sum(len(q) for q in self.high_priority_queues.values())
        
        return {
            **self.stats,
            'active_connections': len(self.message_queues),
            'queued_messages': total_queued,
            'queued_high_priority': total_high_priority,
            'active_timers': len(self.batch_timers) + len(self.high_priority_timers),
            'average_batch_size': (
                self.stats['messages_sent'] / self.stats['batches_sent'] 
                if self.stats['batches_sent'] > 0 else 0
            )
        }
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self.stats = {
            'messages_queued': 0,
            'batches_sent': 0,
            'bytes_saved_compression': 0,
            'messages_sent': 0
        }

# Global batch manager instance
batch_manager = WebSocketBatchManager()
