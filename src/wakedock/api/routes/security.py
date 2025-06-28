"""
Security endpoints for WakeDock
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

from wakedock.api.auth.dependencies import get_current_user
from wakedock.database.models import User, UserRole

router = APIRouter()


class SecurityEvent(BaseModel):
    type: str
    message: str
    timestamp: str


class SecurityMetrics(BaseModel):
    totalSessions: int
    activeSessions: int
    failedLogins: int
    lastActivity: str
    securityEvents: List[SecurityEvent]


@router.get("/security/metrics", response_model=SecurityMetrics)
async def get_security_metrics(current_user: User = Depends(get_current_user)):
    """Get security metrics and events"""
    
    # Generate some mock data for now
    # In a real implementation, this would query the database
    
    # Mock security events
    events = [
        SecurityEvent(
            type="success",
            message="User 'admin' logged in successfully",
            timestamp=(datetime.now() - timedelta(minutes=5)).isoformat()
        ),
        SecurityEvent(
            type="warning",
            message="Failed login attempt from IP 192.168.1.100",
            timestamp=(datetime.now() - timedelta(minutes=15)).isoformat()
        ),
        SecurityEvent(
            type="success",
            message="Password changed for user 'testuser'",
            timestamp=(datetime.now() - timedelta(hours=2)).isoformat()
        ),
        SecurityEvent(
            type="error",
            message="Multiple failed login attempts detected",
            timestamp=(datetime.now() - timedelta(hours=4)).isoformat()
        )
    ]
    
    return SecurityMetrics(
        totalSessions=15,
        activeSessions=3,
        failedLogins=7,
        lastActivity=(datetime.now() - timedelta(minutes=2)).isoformat(),
        securityEvents=events
    )


@router.post("/security/clear-logs")
async def clear_security_logs(current_user: User = Depends(get_current_user)):
    """Clear security logs"""
    
    # Check if user has admin permissions
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would clear logs from the database
    return {"message": "Security logs cleared successfully"}


@router.get("/security/sessions")
async def get_active_sessions(current_user: User = Depends(get_current_user)):
    """Get active user sessions"""
    
    # Mock active sessions data
    sessions = [
        {
            "id": "sess_123",
            "user": current_user.username,
            "ip": "192.168.1.10",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "lastActivity": (datetime.now() - timedelta(minutes=2)).isoformat(),
            "created": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "id": "sess_456",
            "user": "testuser",
            "ip": "192.168.1.15",
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "lastActivity": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "created": (datetime.now() - timedelta(hours=3)).isoformat()
        }
    ]
    
    return {"sessions": sessions}


@router.delete("/security/sessions/{session_id}")
async def terminate_session(session_id: str, current_user: User = Depends(get_current_user)):
    """Terminate a user session"""
    
    # Check if user has admin permissions
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, this would invalidate the session
    return {"message": f"Session {session_id} terminated successfully"}
