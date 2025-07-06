"""
Audit Logging System

Comprehensive audit logging for security events, user actions, and system changes:
- User authentication events
- Service management actions
- Configuration changes
- System admin actions
- API access logs
- Security violations
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Index
from sqlalchemy.sql import func
from pydantic import BaseModel

from wakedock.database.database import Base, get_db_session
from wakedock.database.models import UserRole

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_STATUS_CHANGED = "user_status_changed"
    PASSWORD_CHANGED = "password_changed"
    
    # Service management
    SERVICE_CREATED = "service_created"
    SERVICE_UPDATED = "service_updated"
    SERVICE_DELETED = "service_deleted"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_RESTARTED = "service_restarted"
    
    # Configuration changes
    CONFIG_CREATED = "config_created"
    CONFIG_UPDATED = "config_updated"
    CONFIG_DELETED = "config_deleted"
    
    # Security events
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    
    # System events
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    SYSTEM_MAINTENANCE = "system_maintenance"
    
    # API events
    API_ACCESS = "api_access"
    API_ERROR = "api_error"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """Audit log model for storing security and system events"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # User and session info
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    user_role = Column(String(20), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True)
    
    # Event details
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    
    # Additional data
    event_metadata = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Status and outcome
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_event_time', 'event_type', 'timestamp'),
        Index('idx_audit_severity_time', 'severity', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(event_type='{self.event_type}', user='{self.username}')>"


class AuditEventData(BaseModel):
    """Pydantic model for audit event data"""
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.MEDIUM
    
    # User information
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_role: Optional[UserRole] = None
    session_id: Optional[str] = None
    
    # Request information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # Event details
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    description: str
    
    # Additional data
    event_metadata: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    
    # Status
    success: bool = True
    error_message: Optional[str] = None


class AuditLogger:
    """Service for logging audit events"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.audit")
    
    async def log_event(self, event_data: AuditEventData) -> AuditLog:
        """Log an audit event to the database and system logs"""
        try:
            # Create audit log entry
            audit_entry = AuditLog(
                event_type=event_data.event_type.value,
                severity=event_data.severity.value,
                user_id=event_data.user_id,
                username=event_data.username,
                user_role=event_data.user_role.value if event_data.user_role else None,
                session_id=event_data.session_id,
                ip_address=event_data.ip_address,
                user_agent=event_data.user_agent,
                endpoint=event_data.endpoint,
                method=event_data.method,
                resource_type=event_data.resource_type,
                resource_id=event_data.resource_id,
                action=event_data.action,
                description=event_data.description,
                event_metadata=event_data.event_metadata,
                old_values=event_data.old_values,
                new_values=event_data.new_values,
                success=event_data.success,
                error_message=event_data.error_message
            )
            
            # Save to database
            async with get_db_session() as db:
                db.add(audit_entry)
                await db.commit()
                await db.refresh(audit_entry)
            
            # Log to system logs
            log_level = self._get_log_level(event_data.severity)
            log_message = self._format_log_message(event_data)
            self.logger.log(log_level, log_message, extra={
                'audit_id': audit_entry.id,
                'event_type': event_data.event_type.value,
                'user_id': event_data.user_id,
                'username': event_data.username,
                'ip_address': event_data.ip_address
            })
            
            return audit_entry
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            # Log to system logs as fallback
            self.logger.error(f"AUDIT FALLBACK: {event_data.event_type.value} - {event_data.description}")
            raise
    
    def _get_log_level(self, severity: AuditSeverity) -> int:
        """Convert audit severity to log level"""
        severity_map = {
            AuditSeverity.LOW: logging.INFO,
            AuditSeverity.MEDIUM: logging.WARNING,
            AuditSeverity.HIGH: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_map.get(severity, logging.INFO)
    
    def _format_log_message(self, event_data: AuditEventData) -> str:
        """Format audit event for system logs"""
        parts = [
            f"[AUDIT:{event_data.event_type.value}]",
            f"User: {event_data.username or 'anonymous'}",
            f"Action: {event_data.action}",
            f"IP: {event_data.ip_address or 'unknown'}"
        ]
        
        if event_data.resource_type:
            parts.append(f"Resource: {event_data.resource_type}:{event_data.resource_id}")
        
        if not event_data.success:
            parts.append(f"ERROR: {event_data.error_message}")
        
        return " | ".join(parts)


class AuditService:
    """High-level audit service with convenience methods"""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
    
    async def log_user_login(self, user_id: int, username: str, ip_address: str, 
                           user_agent: str, success: bool = True, error: str = None):
        """Log user login attempt"""
        event_data = AuditEventData(
            event_type=AuditEventType.USER_LOGIN if success else AuditEventType.USER_LOGIN_FAILED,
            severity=AuditSeverity.LOW if success else AuditSeverity.MEDIUM,
            user_id=user_id if success else None,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login_attempt",
            description=f"User {username} login {'successful' if success else 'failed'}",
            success=success,
            error_message=error
        )
        return await self.audit_logger.log_event(event_data)
    
    async def log_user_logout(self, user_id: int, username: str, ip_address: str):
        """Log user logout"""
        event_data = AuditEventData(
            event_type=AuditEventType.USER_LOGOUT,
            severity=AuditSeverity.LOW,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action="logout",
            description=f"User {username} logged out"
        )
        return await self.audit_logger.log_event(event_data)
    
    async def log_permission_denied(self, user_id: int, username: str, action: str,
                                  resource_type: str, resource_id: str, ip_address: str,
                                  endpoint: str):
        """Log permission denied events"""
        event_data = AuditEventData(
            event_type=AuditEventType.PERMISSION_DENIED,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            endpoint=endpoint,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=f"Permission denied: {username} attempted {action} on {resource_type}:{resource_id}",
            success=False
        )
        return await self.audit_logger.log_event(event_data)
    
    async def log_service_action(self, user_id: int, username: str, service_id: str,
                               service_name: str, action: str, success: bool = True,
                               error: str = None, event_metadata: Dict = None):
        """Log service management actions"""
        action_types = {
            "create": AuditEventType.SERVICE_CREATED,
            "update": AuditEventType.SERVICE_UPDATED,
            "delete": AuditEventType.SERVICE_DELETED,
            "start": AuditEventType.SERVICE_STARTED,
            "stop": AuditEventType.SERVICE_STOPPED,
            "restart": AuditEventType.SERVICE_RESTARTED
        }
        
        event_data = AuditEventData(
            event_type=action_types.get(action, AuditEventType.SERVICE_UPDATED),
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            username=username,
            resource_type="service",
            resource_id=service_id,
            action=action,
            description=f"Service {service_name} {action} by {username}",
            event_metadata=event_metadata,
            success=success,
            error_message=error
        )
        return await self.audit_logger.log_event(event_data)
    
    async def log_config_change(self, user_id: int, username: str, config_key: str,
                              old_value: Any, new_value: Any, category: str = None):
        """Log configuration changes"""
        event_data = AuditEventData(
            event_type=AuditEventType.CONFIG_UPDATED,
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            username=username,
            resource_type="configuration",
            resource_id=config_key,
            action="update_config",
            description=f"Configuration '{config_key}' updated by {username}",
            old_values={"value": old_value, "category": category},
            new_values={"value": new_value, "category": category}
        )
        return await self.audit_logger.log_event(event_data)
    
    async def log_security_violation(self, event_type: str, description: str,
                                   user_id: int = None, username: str = None,
                                   ip_address: str = None, event_metadata: Dict = None):
        """Log security violations"""
        event_data = AuditEventData(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.CRITICAL,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action=event_type,
            description=description,
            event_metadata=event_metadata,
            success=False
        )
        return await self.audit_logger.log_event(event_data)
    
    async def get_audit_logs(self, user_id: Optional[int] = None,
                           event_type: Optional[AuditEventType] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: int = 100) -> List[AuditLog]:
        """Retrieve audit logs with filtering"""
        try:
            async with get_db_session() as db:
                query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
                
                if user_id:
                    query = query.filter(AuditLog.user_id == user_id)
                
                if event_type:
                    query = query.filter(AuditLog.event_type == event_type.value)
                
                if start_time:
                    query = query.filter(AuditLog.timestamp >= start_time)
                
                if end_time:
                    query = query.filter(AuditLog.timestamp <= end_time)
                
                return query.limit(limit).all()
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit logs: {e}")
            return []


# Global audit service instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get global audit service instance"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service