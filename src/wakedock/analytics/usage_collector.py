"""
Advanced Usage Analytics Collector

Collects comprehensive usage analytics including:
- User behavior patterns
- Feature usage statistics
- Performance metrics
- Resource utilization
- Business intelligence metrics
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum

from .types import MetricPoint, AnalyticsEvent
from wakedock.database.models import User, UserRole

logger = logging.getLogger(__name__)


class UsageEventType(Enum):
    """Types of usage events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PAGE_VIEW = "page_view"
    API_CALL = "api_call"
    FEATURE_USAGE = "feature_usage"
    ERROR_OCCURRED = "error_occurred"
    RESOURCE_ACCESS = "resource_access"
    EXPORT_DATA = "export_data"
    CONFIGURATION_CHANGE = "config_change"
    SERVICE_INTERACTION = "service_interaction"


@dataclass
class UserSession:
    """User session tracking"""
    user_id: str
    session_id: str
    start_time: datetime
    last_activity: datetime
    page_views: List[str] = field(default_factory=list)
    api_calls: List[str] = field(default_factory=list)
    features_used: Set[str] = field(default_factory=set)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class FeatureUsage:
    """Feature usage statistics"""
    feature_name: str
    total_usage: int = 0
    unique_users: Set[str] = field(default_factory=set)
    usage_by_hour: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    usage_by_day: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    avg_session_duration: float = 0.0
    last_used: Optional[datetime] = None


@dataclass
class UserAnalytics:
    """Per-user analytics data"""
    user_id: str
    total_sessions: int = 0
    total_time_spent: timedelta = timedelta()
    favorite_features: List[str] = field(default_factory=list)
    most_active_hours: List[int] = field(default_factory=list)
    last_login: Optional[datetime] = None
    total_api_calls: int = 0
    error_count: int = 0


class UsageAnalyticsCollector:
    """Advanced usage analytics collector"""
    
    def __init__(self, storage_service=None):
        self.storage = storage_service
        
        # Active session tracking
        self.active_sessions: Dict[str, UserSession] = {}
        self.session_history: deque = deque(maxlen=10000)
        
        # Feature usage tracking
        self.feature_usage: Dict[str, FeatureUsage] = {}
        
        # User analytics
        self.user_analytics: Dict[str, UserAnalytics] = {}
        
        # Real-time metrics
        self.hourly_metrics = {
            "active_users": deque(maxlen=24),  # 24 hours
            "page_views": deque(maxlen=24),
            "api_calls": deque(maxlen=24),
            "errors": deque(maxlen=24)
        }
        
        # Performance tracking
        self.api_performance = defaultdict(lambda: {
            "total_calls": 0,
            "total_duration": 0.0,
            "error_count": 0,
            "avg_response_time": 0.0,
            "slowest_response": 0.0,
            "fastest_response": float('inf')
        })
        
        # Background tasks
        self._running = False
        self._cleanup_task = None
        self._aggregation_task = None
    
    async def start_collection(self):
        """Start background collection tasks"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        logger.info("Usage analytics collection started")
    
    async def stop_collection(self):
        """Stop background collection tasks"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._aggregation_task:
            self._aggregation_task.cancel()
            
        logger.info("Usage analytics collection stopped")
    
    async def track_user_login(self, user_id: str, session_id: str, 
                             ip_address: str = None, user_agent: str = None):
        """Track user login event"""
        now = datetime.utcnow()
        
        # Create new session
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            start_time=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.active_sessions[session_id] = session
        
        # Update user analytics
        if user_id not in self.user_analytics:
            self.user_analytics[user_id] = UserAnalytics(user_id=user_id)
        
        user_stats = self.user_analytics[user_id]
        user_stats.total_sessions += 1
        user_stats.last_login = now
        
        # Track event
        await self._record_event(UsageEventType.USER_LOGIN, {
            "user_id": user_id,
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent
        })
        
        logger.debug(f"User login tracked: {user_id}")
    
    async def track_user_logout(self, session_id: str):
        """Track user logout event"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session_duration = datetime.utcnow() - session.start_time
        
        # Update user analytics
        user_stats = self.user_analytics[session.user_id]
        user_stats.total_time_spent += session_duration
        
        # Archive session
        self.session_history.append(session)
        del self.active_sessions[session_id]
        
        # Track event
        await self._record_event(UsageEventType.USER_LOGOUT, {
            "user_id": session.user_id,
            "session_id": session_id,
            "session_duration_seconds": session_duration.total_seconds()
        })
        
        logger.debug(f"User logout tracked: {session.user_id}")
    
    async def track_page_view(self, session_id: str, page_path: str, 
                            referrer: str = None, load_time: float = None):
        """Track page view event"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.page_views.append(page_path)
            session.last_activity = datetime.utcnow()
            
            # Track event
            await self._record_event(UsageEventType.PAGE_VIEW, {
                "user_id": session.user_id,
                "session_id": session_id,
                "page_path": page_path,
                "referrer": referrer,
                "load_time_ms": load_time
            })
    
    async def track_api_call(self, session_id: str, endpoint: str, method: str,
                           response_time: float, status_code: int, user_id: str = None):
        """Track API call event"""
        # Update session if available
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.api_calls.append(f"{method} {endpoint}")
            session.last_activity = datetime.utcnow()
            actual_user_id = session.user_id
        else:
            actual_user_id = user_id
        
        # Update API performance metrics
        api_key = f"{method} {endpoint}"
        perf = self.api_performance[api_key]
        perf["total_calls"] += 1
        perf["total_duration"] += response_time
        perf["avg_response_time"] = perf["total_duration"] / perf["total_calls"]
        
        if status_code >= 400:
            perf["error_count"] += 1
        
        if response_time > perf["slowest_response"]:
            perf["slowest_response"] = response_time
        if response_time < perf["fastest_response"]:
            perf["fastest_response"] = response_time
        
        # Update user analytics
        if actual_user_id and actual_user_id in self.user_analytics:
            self.user_analytics[actual_user_id].total_api_calls += 1
            if status_code >= 400:
                self.user_analytics[actual_user_id].error_count += 1
        
        # Track event
        await self._record_event(UsageEventType.API_CALL, {
            "user_id": actual_user_id,
            "session_id": session_id,
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time,
            "status_code": status_code
        })
    
    async def track_feature_usage(self, session_id: str, feature_name: str, 
                                action: str = None, metadata: Dict = None):
        """Track feature usage event"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.features_used.add(feature_name)
        session.last_activity = datetime.utcnow()
        
        # Update feature usage statistics
        if feature_name not in self.feature_usage:
            self.feature_usage[feature_name] = FeatureUsage(feature_name=feature_name)
        
        feature_stats = self.feature_usage[feature_name]
        feature_stats.total_usage += 1
        feature_stats.unique_users.add(session.user_id)
        feature_stats.last_used = datetime.utcnow()
        
        # Track hourly usage
        current_hour = datetime.utcnow().hour
        feature_stats.usage_by_hour[current_hour] += 1
        
        # Track daily usage
        current_day = datetime.utcnow().strftime("%Y-%m-%d")
        feature_stats.usage_by_day[current_day] += 1
        
        # Track event
        await self._record_event(UsageEventType.FEATURE_USAGE, {
            "user_id": session.user_id,
            "session_id": session_id,
            "feature_name": feature_name,
            "action": action,
            "metadata": metadata or {}
        })
    
    async def track_error(self, session_id: str, error_type: str, error_message: str,
                        stack_trace: str = None, context: Dict = None):
        """Track error event"""
        user_id = None
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            user_id = session.user_id
            session.last_activity = datetime.utcnow()
        
        # Track event
        await self._record_event(UsageEventType.ERROR_OCCURRED, {
            "user_id": user_id,
            "session_id": session_id,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "context": context or {}
        })
    
    async def _record_event(self, event_type: UsageEventType, data: Dict[str, Any]):
        """Record analytics event"""
        try:
            event = AnalyticsEvent(
                event_type=event_type.value,
                user_id=data.get("user_id"),
                session_id=data.get("session_id"),
                timestamp=datetime.utcnow(),
                data=data
            )
            
            # Store event if storage is available
            if self.storage:
                await self.storage.store_event(event)
            
        except Exception as e:
            logger.error(f"Failed to record analytics event: {e}")
    
    async def _cleanup_loop(self):
        """Background cleanup of old sessions and data"""
        while self._running:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(300)  # Run every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _aggregation_loop(self):
        """Background aggregation of metrics"""
        while self._running:
            try:
                await self._aggregate_hourly_metrics()
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Aggregation loop error: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            # Sessions inactive for more than 4 hours are considered expired
            if now - session.last_activity > timedelta(hours=4):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.track_user_logout(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _aggregate_hourly_metrics(self):
        """Aggregate hourly metrics"""
        now = datetime.utcnow()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # Count active users in the last hour
        active_users = set()
        for session in self.active_sessions.values():
            if now - session.last_activity < timedelta(hours=1):
                active_users.add(session.user_id)
        
        # Store hourly metrics
        self.hourly_metrics["active_users"].append({
            "timestamp": current_hour,
            "value": len(active_users)
        })
        
        # Calculate other metrics (simplified)
        total_page_views = sum(len(s.page_views) for s in self.active_sessions.values())
        total_api_calls = sum(len(s.api_calls) for s in self.active_sessions.values())
        
        self.hourly_metrics["page_views"].append({
            "timestamp": current_hour,
            "value": total_page_views
        })
        
        self.hourly_metrics["api_calls"].append({
            "timestamp": current_hour,
            "value": total_api_calls
        })
        
        logger.info(f"Aggregated hourly metrics: {len(active_users)} active users")
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for the specified period"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=hours)
        
        # Active sessions in period
        active_in_period = [
            s for s in self.active_sessions.values()
            if s.start_time >= cutoff or s.last_activity >= cutoff
        ]
        
        # Feature usage summary
        top_features = sorted(
            self.feature_usage.values(),
            key=lambda f: f.total_usage,
            reverse=True
        )[:10]
        
        # API performance summary
        api_summary = {}
        for endpoint, perf in self.api_performance.items():
            if perf["total_calls"] > 0:
                api_summary[endpoint] = {
                    "total_calls": perf["total_calls"],
                    "avg_response_time": round(perf["avg_response_time"], 2),
                    "error_rate": round(perf["error_count"] / perf["total_calls"] * 100, 2),
                    "slowest_response": round(perf["slowest_response"], 2)
                }
        
        return {
            "period_hours": hours,
            "active_sessions": len(active_in_period),
            "total_users": len(set(s.user_id for s in active_in_period)),
            "total_page_views": sum(len(s.page_views) for s in active_in_period),
            "total_api_calls": sum(len(s.api_calls) for s in active_in_period),
            "top_features": [
                {
                    "name": f.feature_name,
                    "usage_count": f.total_usage,
                    "unique_users": len(f.unique_users)
                }
                for f in top_features
            ],
            "api_performance": api_summary,
            "generated_at": now.isoformat()
        }
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get detailed insights for a specific user"""
        if user_id not in self.user_analytics:
            return {"error": "User not found in analytics"}
        
        user_stats = self.user_analytics[user_id]
        
        # Current active session
        current_session = None
        for session in self.active_sessions.values():
            if session.user_id == user_id:
                current_session = {
                    "session_id": session.session_id,
                    "start_time": session.start_time.isoformat(),
                    "duration_minutes": (datetime.utcnow() - session.start_time).total_seconds() / 60,
                    "pages_visited": len(session.page_views),
                    "api_calls_made": len(session.api_calls),
                    "features_used": list(session.features_used)
                }
                break
        
        return {
            "user_id": user_id,
            "total_sessions": user_stats.total_sessions,
            "total_time_spent_hours": user_stats.total_time_spent.total_seconds() / 3600,
            "total_api_calls": user_stats.total_api_calls,
            "error_count": user_stats.error_count,
            "last_login": user_stats.last_login.isoformat() if user_stats.last_login else None,
            "current_session": current_session,
            "generated_at": datetime.utcnow().isoformat()
        }


# Global instance
_usage_collector = None

def get_usage_analytics_collector() -> Optional[UsageAnalyticsCollector]:
    """Get the global usage analytics collector instance"""
    return _usage_collector

def initialize_usage_analytics_collector(storage_service=None) -> UsageAnalyticsCollector:
    """Initialize the global usage analytics collector"""
    global _usage_collector
    _usage_collector = UsageAnalyticsCollector(storage_service)
    return _usage_collector