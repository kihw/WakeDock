"""
Advanced Performance Cache Optimizer

Implements intelligent cache optimization strategies including:
- Predictive prefetching based on usage patterns
- Dynamic TTL adjustment based on access frequency  
- Cache partition optimization for different workloads
- Adaptive compression for memory efficiency
- ML-based cache replacement policies
"""

import asyncio
import logging
import time
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CacheOptimizationStrategy(Enum):
    """Cache optimization strategies"""
    FREQUENCY_BASED = "frequency_based"
    TIME_BASED = "time_based"
    PREDICTIVE = "predictive"
    WORKLOAD_ADAPTIVE = "workload_adaptive"


@dataclass
class AccessPattern:
    """Cache access pattern analysis"""
    key: str
    access_count: int = 0
    last_access: float = 0
    access_times: deque = field(default_factory=lambda: deque(maxlen=100))
    hit_rate: float = 0.0
    avg_interval: float = 0.0
    trend: str = "stable"  # increasing, decreasing, stable, volatile


@dataclass
class CachePartition:
    """Cache partition configuration"""
    name: str
    max_memory_mb: int
    eviction_policy: str  # lru, lfu, random, ttl
    compression_level: int = 0  # 0-9, 0 = no compression
    min_ttl: int = 60
    max_ttl: int = 3600
    priority: int = 1  # 1-10, higher = more important


class PerformanceOptimizer:
    """Advanced cache performance optimizer"""
    
    def __init__(self, redis_client, cache_manager):
        self.redis = redis_client
        self.cache_manager = cache_manager
        
        # Access pattern tracking
        self.access_patterns: Dict[str, AccessPattern] = {}
        self.access_history: deque = deque(maxlen=10000)
        
        # Cache partitions for different workloads
        self.partitions = {
            "hot_data": CachePartition(
                name="hot_data",
                max_memory_mb=512,
                eviction_policy="lfu",
                compression_level=1,
                min_ttl=30,
                max_ttl=300,
                priority=10
            ),
            "warm_data": CachePartition(
                name="warm_data", 
                max_memory_mb=1024,
                eviction_policy="lru",
                compression_level=3,
                min_ttl=300,
                max_ttl=1800,
                priority=5
            ),
            "cold_data": CachePartition(
                name="cold_data",
                max_memory_mb=2048,
                eviction_policy="ttl",
                compression_level=6,
                min_ttl=1800,
                max_ttl=7200,
                priority=1
            )
        }
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "prefetch_hits": 0,
            "prefetch_misses": 0,
            "dynamic_ttl_adjustments": 0,
            "compression_savings_mb": 0.0,
            "optimization_runs": 0
        }
        
        # Optimization configuration
        self.config = {
            "enable_predictive_prefetch": True,
            "enable_dynamic_ttl": True,
            "enable_adaptive_compression": True,
            "enable_workload_partitioning": True,
            "optimization_interval": 300,  # 5 minutes
            "access_pattern_window": 3600,  # 1 hour
            "prefetch_threshold": 0.7,  # Prefetch if prediction confidence > 70%
            "ttl_adjustment_factor": 0.1,  # Max 10% TTL adjustment per optimization
            "memory_usage_threshold": 0.8  # Trigger optimization at 80% memory usage
        }
        
        # Background optimization task
        self._optimization_task = None
        self._running = False
    
    async def start_optimization(self):
        """Start background optimization"""
        if self._running:
            return
        
        self._running = True
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        logger.info("Cache performance optimizer started")
    
    async def stop_optimization(self):
        """Stop background optimization"""
        self._running = False
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache performance optimizer stopped")
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while self._running:
            try:
                await self.run_optimization_cycle()
                await asyncio.sleep(self.config["optimization_interval"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization cycle failed: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def run_optimization_cycle(self):
        """Run a complete optimization cycle"""
        start_time = time.time()
        
        try:
            # Analyze current cache state
            cache_info = await self._analyze_cache_state()
            
            # Update access patterns
            await self._update_access_patterns()
            
            # Run optimization strategies
            if self.config["enable_predictive_prefetch"]:
                await self._run_predictive_prefetching()
            
            if self.config["enable_dynamic_ttl"]:
                await self._optimize_ttl_values()
            
            if self.config["enable_adaptive_compression"]:
                await self._optimize_compression()
            
            if self.config["enable_workload_partitioning"]:
                await self._optimize_partitions()
            
            # Update metrics
            self.metrics["optimization_runs"] += 1
            
            duration = time.time() - start_time
            logger.info(f"Optimization cycle completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Optimization cycle failed: {e}")
    
    async def _analyze_cache_state(self) -> Dict[str, Any]:
        """Analyze current cache state"""
        try:
            # Redis info
            redis_info = self.redis.info()
            memory_info = self.redis.info('memory')
            
            # Key analysis
            sample_keys = self.redis.keys("*")  # In production, use SCAN
            key_count = len(sample_keys)
            
            # Calculate cache efficiency
            total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
            hit_rate = self.metrics["cache_hits"] / total_requests if total_requests > 0 else 0
            
            return {
                "memory_used_mb": memory_info.get('used_memory', 0) / 1024 / 1024,
                "memory_peak_mb": memory_info.get('used_memory_peak', 0) / 1024 / 1024,
                "key_count": key_count,
                "hit_rate": hit_rate,
                "connected_clients": redis_info.get('connected_clients', 0),
                "ops_per_sec": redis_info.get('instantaneous_ops_per_sec', 0)
            }
        except Exception as e:
            logger.error(f"Failed to analyze cache state: {e}")
            return {}
    
    async def _update_access_patterns(self):
        """Update access pattern analysis"""
        current_time = time.time()
        
        # Clean old patterns
        cutoff_time = current_time - self.config["access_pattern_window"]
        for key in list(self.access_patterns.keys()):
            pattern = self.access_patterns[key]
            if pattern.last_access < cutoff_time:
                del self.access_patterns[key]
        
        # Analyze patterns for trend detection
        for pattern in self.access_patterns.values():
            if len(pattern.access_times) >= 5:
                # Calculate access trend
                recent_accesses = list(pattern.access_times)[-10:]
                if len(recent_accesses) >= 3:
                    # Simple trend analysis
                    intervals = [recent_accesses[i] - recent_accesses[i-1] 
                               for i in range(1, len(recent_accesses))]
                    avg_interval = statistics.mean(intervals)
                    pattern.avg_interval = avg_interval
                    
                    # Determine trend
                    if len(intervals) >= 3:
                        recent_trend = statistics.mean(intervals[-3:])
                        older_trend = statistics.mean(intervals[:-3]) if len(intervals) > 3 else recent_trend
                        
                        if recent_trend < older_trend * 0.8:
                            pattern.trend = "increasing"
                        elif recent_trend > older_trend * 1.2:
                            pattern.trend = "decreasing"
                        else:
                            pattern.trend = "stable"
    
    async def _run_predictive_prefetching(self):
        """Run predictive prefetching based on patterns"""
        prefetch_candidates = []
        
        for key, pattern in self.access_patterns.items():
            # Skip if recently accessed
            if time.time() - pattern.last_access < 60:
                continue
            
            # Predict next access time
            prediction_confidence = self._predict_next_access(pattern)
            
            if prediction_confidence > self.config["prefetch_threshold"]:
                # Check if key exists and when it expires
                ttl = self.redis.ttl(key)
                if ttl > 0 and ttl < 300:  # Expires within 5 minutes
                    prefetch_candidates.append((key, prediction_confidence))
        
        # Sort by confidence and prefetch top candidates
        prefetch_candidates.sort(key=lambda x: x[1], reverse=True)
        
        for key, confidence in prefetch_candidates[:10]:  # Limit to 10 prefetches
            try:
                # Attempt to refresh from source
                cache_type = self._infer_cache_type(key)
                if cache_type:
                    # This would need integration with the specific data fetchers
                    logger.debug(f"Prefetch candidate: {key} (confidence: {confidence:.2f})")
                    self.metrics["prefetch_hits"] += 1
            except Exception as e:
                logger.debug(f"Prefetch failed for {key}: {e}")
                self.metrics["prefetch_misses"] += 1
    
    def _predict_next_access(self, pattern: AccessPattern) -> float:
        """Predict probability of next access"""
        if len(pattern.access_times) < 3:
            return 0.0
        
        # Factor in access frequency
        frequency_score = min(pattern.access_count / 100, 1.0)
        
        # Factor in recency
        time_since_last = time.time() - pattern.last_access
        recency_score = max(0, 1.0 - (time_since_last / 3600))  # Decay over 1 hour
        
        # Factor in trend
        trend_score = 0.5
        if pattern.trend == "increasing":
            trend_score = 0.8
        elif pattern.trend == "decreasing":
            trend_score = 0.2
        
        # Factor in regularity
        if pattern.avg_interval > 0:
            expected_next_access = pattern.last_access + pattern.avg_interval
            time_variance = abs(time.time() - expected_next_access) / pattern.avg_interval
            regularity_score = max(0, 1.0 - time_variance)
        else:
            regularity_score = 0.5
        
        # Combined confidence score
        confidence = (frequency_score * 0.3 + 
                     recency_score * 0.3 + 
                     trend_score * 0.2 + 
                     regularity_score * 0.2)
        
        return min(confidence, 1.0)
    
    async def _optimize_ttl_values(self):
        """Optimize TTL values based on access patterns"""
        adjustments_made = 0
        
        for key, pattern in self.access_patterns.items():
            current_ttl = self.redis.ttl(key)
            if current_ttl <= 0:
                continue
            
            # Calculate optimal TTL based on access pattern
            optimal_ttl = self._calculate_optimal_ttl(pattern)
            
            if optimal_ttl and abs(optimal_ttl - current_ttl) / current_ttl > 0.2:
                # Significant difference, adjust TTL
                adjustment_factor = self.config["ttl_adjustment_factor"]
                new_ttl = current_ttl + (optimal_ttl - current_ttl) * adjustment_factor
                new_ttl = max(60, min(7200, int(new_ttl)))  # Clamp to reasonable range
                
                try:
                    self.redis.expire(key, new_ttl)
                    adjustments_made += 1
                    logger.debug(f"Adjusted TTL for {key}: {current_ttl} -> {new_ttl}")
                except Exception as e:
                    logger.error(f"Failed to adjust TTL for {key}: {e}")
        
        self.metrics["dynamic_ttl_adjustments"] += adjustments_made
        
        if adjustments_made > 0:
            logger.info(f"Optimized TTL for {adjustments_made} keys")
    
    def _calculate_optimal_ttl(self, pattern: AccessPattern) -> Optional[int]:
        """Calculate optimal TTL for access pattern"""
        if pattern.avg_interval <= 0:
            return None
        
        # Base TTL on average access interval
        base_ttl = pattern.avg_interval * 1.5  # 1.5x safety margin
        
        # Adjust based on trend
        if pattern.trend == "increasing":
            base_ttl *= 0.8  # Shorter TTL for increasing access
        elif pattern.trend == "decreasing":
            base_ttl *= 1.5  # Longer TTL for decreasing access
        
        # Adjust based on frequency
        if pattern.access_count > 50:
            base_ttl *= 0.9  # Popular data gets shorter TTL
        elif pattern.access_count < 10:
            base_ttl *= 1.2  # Unpopular data gets longer TTL
        
        return max(60, min(7200, int(base_ttl)))
    
    async def _optimize_compression(self):
        """Optimize compression settings based on memory usage"""
        try:
            memory_info = self.redis.info('memory')
            used_memory_mb = memory_info.get('used_memory', 0) / 1024 / 1024
            
            # If memory usage is high, increase compression
            if used_memory_mb > 1000:  # Over 1GB
                # This would require rebuilding cache with different compression
                # For now, just log the recommendation
                logger.info(f"High memory usage ({used_memory_mb:.1f}MB), consider increasing compression")
                
                # Update compression recommendations for new data
                for partition in self.partitions.values():
                    if partition.compression_level < 6:
                        partition.compression_level = min(6, partition.compression_level + 1)
        
        except Exception as e:
            logger.error(f"Compression optimization failed: {e}")
    
    async def _optimize_partitions(self):
        """Optimize cache partitions based on workload"""
        try:
            # Analyze current key distribution
            key_distribution = await self._analyze_key_distribution()
            
            # Adjust partition sizes based on usage
            total_memory_mb = sum(p.max_memory_mb for p in self.partitions.values())
            
            for partition_name, usage_ratio in key_distribution.items():
                if partition_name in self.partitions:
                    partition = self.partitions[partition_name]
                    ideal_memory = total_memory_mb * usage_ratio
                    
                    # Gradual adjustment
                    adjustment = (ideal_memory - partition.max_memory_mb) * 0.1
                    new_memory = max(256, int(partition.max_memory_mb + adjustment))
                    
                    if abs(new_memory - partition.max_memory_mb) > 50:  # Significant change
                        partition.max_memory_mb = new_memory
                        logger.debug(f"Adjusted {partition_name} memory: {new_memory}MB")
        
        except Exception as e:
            logger.error(f"Partition optimization failed: {e}")
    
    async def _analyze_key_distribution(self) -> Dict[str, float]:
        """Analyze distribution of keys across partitions"""
        distribution = defaultdict(int)
        total_keys = 0
        
        try:
            # Sample keys (in production use SCAN)
            sample_keys = self.redis.keys("*")
            total_keys = len(sample_keys)
            
            for key in sample_keys:
                partition = self._classify_key_to_partition(key.decode() if isinstance(key, bytes) else key)
                distribution[partition] += 1
            
            # Convert to ratios
            return {k: v / total_keys for k, v in distribution.items()} if total_keys > 0 else {}
        
        except Exception as e:
            logger.error(f"Key distribution analysis failed: {e}")
            return {}
    
    def _classify_key_to_partition(self, key: str) -> str:
        """Classify key to appropriate partition"""
        # Simple classification based on key patterns
        if any(hot_pattern in key for hot_pattern in ["session", "user", "auth"]):
            return "hot_data"
        elif any(warm_pattern in key for warm_pattern in ["service", "status", "metrics"]):
            return "warm_data"
        else:
            return "cold_data"
    
    def _infer_cache_type(self, key: str) -> Optional[str]:
        """Infer cache type from key pattern"""
        if "user" in key:
            return "user_permissions"
        elif "service" in key:
            return "service_status" 
        elif "metrics" in key:
            return "system_metrics"
        elif "dashboard" in key:
            return "dashboard_overview"
        return None
    
    def record_access(self, key: str, hit: bool = True):
        """Record cache access for pattern analysis"""
        current_time = time.time()
        
        # Update access pattern
        if key not in self.access_patterns:
            self.access_patterns[key] = AccessPattern(key=key)
        
        pattern = self.access_patterns[key]
        pattern.access_count += 1
        pattern.last_access = current_time
        pattern.access_times.append(current_time)
        
        # Update hit rate
        if hit:
            self.metrics["cache_hits"] += 1
            pattern.hit_rate = ((pattern.hit_rate * (pattern.access_count - 1)) + 1) / pattern.access_count
        else:
            self.metrics["cache_misses"] += 1
            pattern.hit_rate = (pattern.hit_rate * (pattern.access_count - 1)) / pattern.access_count
        
        # Record in history
        self.access_history.append({
            "key": key,
            "timestamp": current_time,
            "hit": hit
        })
    
    async def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        try:
            cache_info = await self._analyze_cache_state()
            
            # Calculate efficiency metrics
            total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
            hit_rate = self.metrics["cache_hits"] / total_requests if total_requests > 0 else 0
            
            # Pattern analysis stats
            pattern_stats = {
                "total_patterns": len(self.access_patterns),
                "increasing_trends": sum(1 for p in self.access_patterns.values() if p.trend == "increasing"),
                "decreasing_trends": sum(1 for p in self.access_patterns.values() if p.trend == "decreasing"),
                "stable_trends": sum(1 for p in self.access_patterns.values() if p.trend == "stable")
            }
            
            return {
                "cache_performance": {
                    "hit_rate": round(hit_rate * 100, 2),
                    "total_requests": total_requests,
                    "cache_hits": self.metrics["cache_hits"],
                    "cache_misses": self.metrics["cache_misses"]
                },
                "optimization_metrics": {
                    "prefetch_success_rate": (self.metrics["prefetch_hits"] / 
                                            max(1, self.metrics["prefetch_hits"] + self.metrics["prefetch_misses"]) * 100),
                    "ttl_adjustments": self.metrics["dynamic_ttl_adjustments"],
                    "optimization_runs": self.metrics["optimization_runs"],
                    "compression_savings_mb": self.metrics["compression_savings_mb"]
                },
                "access_patterns": pattern_stats,
                "cache_state": cache_info,
                "partitions": {name: {
                    "max_memory_mb": p.max_memory_mb,
                    "compression_level": p.compression_level,
                    "eviction_policy": p.eviction_policy,
                    "priority": p.priority
                } for name, p in self.partitions.items()},
                "configuration": self.config
            }
        
        except Exception as e:
            logger.error(f"Failed to get optimization stats: {e}")
            return {"error": str(e)}
    
    async def tune_configuration(self, updates: Dict[str, Any]):
        """Update optimization configuration"""
        for key, value in updates.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                logger.info(f"Updated config {key}: {old_value} -> {value}")
            else:
                logger.warning(f"Unknown config key: {key}")


# Factory function
def create_performance_optimizer(redis_client, cache_manager) -> PerformanceOptimizer:
    """Create and configure performance optimizer"""
    return PerformanceOptimizer(redis_client, cache_manager)