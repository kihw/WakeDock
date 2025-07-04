"""
System Metrics Handler
Collects and broadcasts system metrics via WebSocket
"""
import asyncio
import json
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Set

logger = logging.getLogger(__name__)

class SystemMetricsHandler:
    """
    Handles system metrics collection and broadcasting
    """
    
    def __init__(self, update_interval: int = 5):
        self.update_interval = update_interval
        self.is_monitoring = False
        self.metrics_task: Optional[asyncio.Task] = None
        self.subscribers: Set[Callable] = set()
        self.last_metrics = {}
        
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to system metrics updates"""
        self.subscribers.add(callback)
        logger.debug(f"Added system metrics subscriber. Total: {len(self.subscribers)}")
        
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from system metrics updates"""
        self.subscribers.discard(callback)
        logger.debug(f"Removed system metrics subscriber. Total: {len(self.subscribers)}")
    
    async def start_monitoring(self) -> None:
        """Start monitoring system metrics"""
        if self.is_monitoring:
            logger.warning("System metrics monitoring is already running")
            return
            
        self.is_monitoring = True
        self.metrics_task = asyncio.create_task(self._monitor_metrics())
        logger.info(f"Started system metrics monitoring (interval: {self.update_interval}s)")
        
    async def stop_monitoring(self) -> None:
        """Stop monitoring system metrics"""
        self.is_monitoring = False
        
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
            self.metrics_task = None
            
        logger.info("Stopped system metrics monitoring")
        
    async def _monitor_metrics(self) -> None:
        """Monitor system metrics in a background task"""
        try:
            logger.info("System metrics monitoring started")
            
            while self.is_monitoring:
                try:
                    # Collect current metrics
                    metrics = await self._collect_metrics()
                    
                    # Only broadcast if metrics have changed significantly
                    if self._should_broadcast(metrics):
                        await self._broadcast_metrics(metrics)
                        self.last_metrics = metrics
                    
                    # Wait for next update
                    await asyncio.sleep(self.update_interval)
                    
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
                    await asyncio.sleep(self.update_interval)
                    
        except Exception as e:
            logger.error(f"System metrics monitoring failed: {e}")
        finally:
            self.is_monitoring = False
            
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            # Run CPU and memory collection in executor to avoid blocking
            cpu_percent = await asyncio.get_event_loop().run_in_executor(
                None, psutil.cpu_percent, 1
            )
            
            memory = await asyncio.get_event_loop().run_in_executor(
                None, psutil.virtual_memory
            )
            
            disk = await asyncio.get_event_loop().run_in_executor(
                None, psutil.disk_usage, '/'
            )
            
            # Network I/O
            net_io = await asyncio.get_event_loop().run_in_executor(
                None, psutil.net_io_counters
            )
            
            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = await asyncio.get_event_loop().run_in_executor(
                    None, psutil.getloadavg
                )
                load_avg = {
                    '1min': round(load_avg[0], 2),
                    '5min': round(load_avg[1], 2),
                    '15min': round(load_avg[2], 2)
                }
            except (AttributeError, OSError):
                # getloadavg is not available on Windows
                pass
            
            # Process count
            process_count = len(psutil.pids())
            
            # Boot time
            boot_time = psutil.boot_time()
            uptime = datetime.now().timestamp() - boot_time
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu': {
                    'percent': round(cpu_percent, 2),
                    'count': psutil.cpu_count(),
                    'freq': None
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': round(memory.percent, 2),
                    'used': memory.used,
                    'free': memory.free,
                    'buffers': getattr(memory, 'buffers', 0),
                    'cached': getattr(memory, 'cached', 0)
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': round(disk.percent, 2)
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                },
                'system': {
                    'uptime': round(uptime, 2),
                    'processes': process_count,
                    'load_average': load_avg
                }
            }
            
            # Try to get CPU frequency
            try:
                cpu_freq = await asyncio.get_event_loop().run_in_executor(
                    None, psutil.cpu_freq
                )
                if cpu_freq:
                    metrics['cpu']['freq'] = {
                        'current': round(cpu_freq.current, 2),
                        'min': round(cpu_freq.min, 2),
                        'max': round(cpu_freq.max, 2)
                    }
            except (AttributeError, OSError):
                pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            
    def _should_broadcast(self, metrics: Dict[str, Any]) -> bool:
        """Determine if metrics should be broadcast based on changes"""
        if not self.last_metrics:
            return True
            
        # Check for significant changes
        try:
            current_cpu = metrics.get('cpu', {}).get('percent', 0)
            last_cpu = self.last_metrics.get('cpu', {}).get('percent', 0)
            
            current_memory = metrics.get('memory', {}).get('percent', 0)
            last_memory = self.last_metrics.get('memory', {}).get('percent', 0)
            
            # Broadcast if CPU or memory changed by more than 5%
            cpu_change = abs(current_cpu - last_cpu)
            memory_change = abs(current_memory - last_memory)
            
            if cpu_change > 5 or memory_change > 5:
                return True
                
            # Also broadcast every 30 seconds regardless of changes
            last_timestamp = self.last_metrics.get('timestamp', '')
            if last_timestamp:
                last_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                current_time = datetime.fromisoformat(metrics['timestamp'])
                time_diff = (current_time - last_time).total_seconds()
                
                if time_diff > 30:
                    return True
                    
        except Exception as e:
            logger.debug(f"Error checking metrics change: {e}")
            return True
            
        return False
        
    async def _broadcast_metrics(self, metrics: Dict[str, Any]) -> None:
        """Broadcast metrics to all subscribers"""
        if not self.subscribers:
            return
            
        system_update = {
            'type': 'system_metrics',
            'data': metrics
        }
        
        # Broadcast to all subscribers
        for callback in self.subscribers.copy():
            try:
                await self._safe_callback(callback, system_update)
            except Exception as e:
                logger.error(f"Error in system metrics callback: {e}")
                
    async def _safe_callback(self, callback: Callable, data: Dict[str, Any]) -> None:
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"System metrics callback execution failed: {e}")
            
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics on demand"""
        return await self._collect_metrics()

# Global instance (will be initialized by the main app)
system_metrics_handler: Optional[SystemMetricsHandler] = None

def initialize_system_metrics(update_interval: int = 5) -> SystemMetricsHandler:
    """Initialize the global system metrics handler"""
    global system_metrics_handler
    system_metrics_handler = SystemMetricsHandler(update_interval)
    return system_metrics_handler

def get_system_metrics_handler() -> Optional[SystemMetricsHandler]:
    """Get the global system metrics handler"""
    return system_metrics_handler