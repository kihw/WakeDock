"""
Security endpoints for WakeDock
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

from wakedock.api.auth.dependencies import get_current_user
from wakedock.database.models import User, UserRole

# Try to import enhanced security modules, gracefully handle import errors
try:
    from wakedock.security.audit_enhanced import (
        get_enhanced_audit_system, 
        IncidentSeverity, 
        ResponseAction
    )
    from wakedock.security.intrusion_detection import ThreatLevel, AttackType
    from wakedock.security.manager import get_security_manager
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError as e:
    # Fallback when enhanced security modules are not available
    ENHANCED_SECURITY_AVAILABLE = False
    
    # Define minimal enum classes for compatibility
    class IncidentSeverity:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class ThreatLevel:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class AttackType:
        BRUTE_FORCE = "brute_force"
        SQL_INJECTION = "sql_injection"
        XSS = "xss"
    
    def get_enhanced_audit_system():
        return None
    
    def get_security_manager():
        return None

router = APIRouter()


def require_security_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require security admin privileges"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security admin privileges required"
        )
    return current_user


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


# Enhanced security models
class IncidentResponse(BaseModel):
    """Incident response data"""
    id: str
    title: str
    description: str
    severity: str
    attack_type: str
    source_ip: str
    target_endpoint: str
    start_time: datetime
    detection_time: datetime
    event_count: int
    auto_blocked: bool
    response_actions: List[str]
    status: str
    reputation_score: Optional[float] = None


class ThreatIntelResponse(BaseModel):
    """Threat intelligence response"""
    ip_address: str
    reputation_score: float
    categories: List[str]
    source: str
    last_updated: datetime
    confidence: float
    additional_data: Dict[str, Any]


class SecurityDashboardResponse(BaseModel):
    """Security dashboard response"""
    timestamp: datetime
    overview: Dict[str, Any]
    incidents: Dict[str, Any]
    threat_intelligence: Dict[str, Any]
    top_threats: List[Dict[str, Any]]
    response_actions: Dict[str, Any]
    system_health: Dict[str, Any]


class SecurityAuditResponse(BaseModel):
    """Security audit response"""
    timestamp: datetime
    audit_type: str
    results: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    security_score: int


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


# === ENHANCED SECURITY AUDIT ENDPOINTS ===

@router.get("/security/dashboard")
async def get_enhanced_security_dashboard(
    current_user: User = Depends(require_security_admin)
):
    """Get comprehensive security dashboard with advanced threat analysis"""
    if not ENHANCED_SECURITY_AVAILABLE:
        return {
            "error": "Enhanced security features not available",
            "message": "Enhanced security audit system is not installed",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        audit_system = get_enhanced_audit_system()
        dashboard_data = await audit_system.get_security_dashboard()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security dashboard: {str(e)}"
        )


@router.get("/security/incidents", response_model=List[IncidentResponse])
async def get_security_incidents(
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    attack_type: Optional[str] = Query(None, description="Filter by attack type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of incidents to return"),
    current_user: User = Depends(require_security_admin)
):
    """Get security incidents with advanced filtering"""
    try:
        audit_system = get_enhanced_audit_system()
        
        incidents = list(audit_system.active_incidents.values())
        
        # Apply filters
        if severity:
            incidents = [i for i in incidents if i.severity.value == severity]
        
        if attack_type:
            incidents = [i for i in incidents if i.attack_type.value == attack_type]
        
        if status:
            incidents = [i for i in incidents if i.status == status]
        
        # Sort by detection time (newest first)
        incidents.sort(key=lambda x: x.detection_time, reverse=True)
        
        # Apply limit
        incidents = incidents[:limit]
        
        # Convert to response format
        response_incidents = []
        for incident in incidents:
            response_incidents.append(IncidentResponse(
                id=incident.id,
                title=incident.title,
                description=incident.description,
                severity=incident.severity.value,
                attack_type=incident.attack_type.value,
                source_ip=incident.source_ip,
                target_endpoint=incident.target_endpoint,
                start_time=incident.start_time,
                detection_time=incident.detection_time,
                event_count=len(incident.events),
                auto_blocked=incident.auto_blocked,
                response_actions=[action.value for action in incident.response_actions],
                status=incident.status,
                reputation_score=incident.threat_intel.reputation_score if incident.threat_intel else None
            ))
        
        return response_incidents
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security incidents: {str(e)}"
        )


@router.get("/security/incidents/{incident_id}")
async def get_incident_details(
    incident_id: str,
    current_user: User = Depends(require_security_admin)
):
    """Get detailed information about a specific security incident"""
    try:
        audit_system = get_enhanced_audit_system()
        
        if incident_id not in audit_system.active_incidents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found"
            )
        
        incident = audit_system.active_incidents[incident_id]
        
        # Build detailed response
        response = {
            "incident": audit_system._incident_to_dict(incident),
            "events": [{
                "timestamp": event.timestamp.isoformat(),
                "ip_address": event.ip_address,
                "attack_type": event.attack_type.value,
                "threat_level": event.threat_level.value,
                "confidence": event.confidence,
                "endpoint": event.endpoint,
                "user_agent": event.user_agent,
                "payload": event.payload[:500] if event.payload else None,  # Truncate for safety
                "blocked": event.blocked,
                "details": event.details
            } for event in incident.events],
            "indicators": incident.indicators,
            "threat_intelligence": {
                "ip_address": incident.threat_intel.ip_address,
                "reputation_score": incident.threat_intel.reputation_score,
                "categories": incident.threat_intel.categories,
                "source": incident.threat_intel.source,
                "confidence": incident.threat_intel.confidence,
                "last_updated": incident.threat_intel.last_updated.isoformat()
            } if incident.threat_intel else None,
            "evidence": incident.evidence
        }
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incident details: {str(e)}"
        )


@router.post("/security/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    resolution_notes: str = Query(..., description="Resolution notes"),
    current_user: User = Depends(require_security_admin)
):
    """Resolve a security incident"""
    try:
        audit_system = get_enhanced_audit_system()
        
        if incident_id not in audit_system.active_incidents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident {incident_id} not found"
            )
        
        incident = audit_system.active_incidents[incident_id]
        incident.status = "resolved"
        incident.resolution_notes = resolution_notes
        incident.assigned_to = current_user.username
        incident.end_time = datetime.now()
        
        return {
            "success": True,
            "message": f"Incident {incident_id} resolved successfully",
            "resolved_by": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve incident: {str(e)}"
        )


@router.post("/security/block-ip/{ip_address}")
async def block_ip_address(
    ip_address: str,
    reason: str = Query(..., description="Reason for blocking"),
    current_user: User = Depends(require_security_admin)
):
    """Manually block an IP address"""
    try:
        audit_system = get_enhanced_audit_system()
        audit_system.ids.block_ip(ip_address)
        
        # Log the manual block action
        await audit_system.audit_service.log_security_violation(
            event_type="manual_ip_block",
            description=f"IP {ip_address} manually blocked by {current_user.username}. Reason: {reason}",
            user_id=current_user.id,
            username=current_user.username,
            ip_address=ip_address,
            event_metadata={"reason": reason, "blocked_by": current_user.username}
        )
        
        return {
            "success": True,
            "message": f"IP {ip_address} blocked successfully",
            "blocked_by": current_user.username,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block IP: {str(e)}"
        )


@router.post("/security/unblock-ip/{ip_address}")
async def unblock_ip_address(
    ip_address: str,
    reason: str = Query(..., description="Reason for unblocking"),
    current_user: User = Depends(require_security_admin)
):
    """Manually unblock an IP address"""
    try:
        audit_system = get_enhanced_audit_system()
        audit_system.ids.unblock_ip(ip_address)
        
        # Log the manual unblock action
        await audit_system.audit_service.log_security_violation(
            event_type="manual_ip_unblock",
            description=f"IP {ip_address} manually unblocked by {current_user.username}. Reason: {reason}",
            user_id=current_user.id,
            username=current_user.username,
            ip_address=ip_address,
            event_metadata={"reason": reason, "unblocked_by": current_user.username}
        )
        
        return {
            "success": True,
            "message": f"IP {ip_address} unblocked successfully",
            "unblocked_by": current_user.username,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock IP: {str(e)}"
        )


@router.get("/security/blocked-ips")
async def get_blocked_ips(
    current_user: User = Depends(require_security_admin)
):
    """Get list of blocked IP addresses with threat intelligence"""
    try:
        audit_system = get_enhanced_audit_system()
        blocked_ips = list(audit_system.ids.blocked_ips)
        
        # Enrich with threat intelligence if available
        enriched_ips = []
        for ip in blocked_ips:
            ip_data = {"ip_address": ip, "blocked": True}
            
            # Add threat intelligence if available
            if ip in audit_system.threat_intel_cache:
                intel = audit_system.threat_intel_cache[ip]
                ip_data.update({
                    "reputation_score": intel.reputation_score,
                    "categories": intel.categories,
                    "last_updated": intel.last_updated.isoformat()
                })
            
            enriched_ips.append(ip_data)
        
        return {
            "blocked_ips": enriched_ips,
            "total_count": len(blocked_ips),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blocked IPs: {str(e)}"
        )


@router.get("/security/threat-intelligence/{ip_address}")
async def get_threat_intelligence(
    ip_address: str,
    current_user: User = Depends(require_security_admin)
):
    """Get threat intelligence for specific IP address"""
    try:
        audit_system = get_enhanced_audit_system()
        threat_intel = await audit_system._get_threat_intelligence(ip_address)
        
        if not threat_intel:
            return {
                "ip_address": ip_address,
                "found": False,
                "message": "No threat intelligence available for this IP"
            }
        
        return {
            "ip_address": threat_intel.ip_address,
            "found": True,
            "reputation_score": threat_intel.reputation_score,
            "categories": threat_intel.categories,
            "source": threat_intel.source,
            "last_updated": threat_intel.last_updated.isoformat(),
            "confidence": threat_intel.confidence,
            "additional_data": threat_intel.additional_data
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get threat intelligence: {str(e)}"
        )


@router.get("/security/audit/run", response_model=SecurityAuditResponse)
async def run_comprehensive_security_audit(
    current_user: User = Depends(require_security_admin)
):
    """Run comprehensive security audit with advanced analytics"""
    try:
        security_manager = get_security_manager()
        audit_results = await security_manager.run_security_audit()
        
        return SecurityAuditResponse(
            timestamp=datetime.fromisoformat(audit_results["timestamp"]),
            audit_type=audit_results["audit_type"],
            results=audit_results["results"],
            recommendations=audit_results["recommendations"],
            security_score=audit_results["security_score"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run security audit: {str(e)}"
        )


@router.post("/security/analyze-events")
async def analyze_security_events(
    limit: int = Query(100, description="Number of recent events to analyze"),
    current_user: User = Depends(require_security_admin)
):
    """Manually trigger advanced security event analysis"""
    try:
        audit_system = get_enhanced_audit_system()
        
        # Get recent security events from IDS
        recent_events = audit_system.ids.get_security_events(limit=limit)
        
        if not recent_events:
            return {
                "message": "No recent security events to analyze",
                "events_processed": 0,
                "incidents_created": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze events and create incidents
        incidents = await audit_system.analyze_security_events(recent_events)
        
        return {
            "message": f"Analyzed {len(recent_events)} security events",
            "events_processed": len(recent_events),
            "incidents_created": len(incidents),
            "new_incidents": [{
                "id": incident.id,
                "title": incident.title,
                "severity": incident.severity.value,
                "auto_blocked": incident.auto_blocked
            } for incident in incidents],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze security events: {str(e)}"
        )


@router.get("/security/recommendations")
async def get_security_recommendations(
    current_user: User = Depends(require_security_admin)
):
    """Get AI-powered security recommendations"""
    try:
        security_manager = get_security_manager()
        recommendations = security_manager.get_security_recommendations()
        
        return {
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security recommendations: {str(e)}"
        )


@router.post("/security/cleanup")
async def cleanup_security_data(
    current_user: User = Depends(require_security_admin)
):
    """Manually trigger security data cleanup"""
    try:
        audit_system = get_enhanced_audit_system()
        
        # Run cleanup
        await audit_system.cleanup_old_data()
        
        return {
            "success": True,
            "message": "Security data cleanup completed",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup security data: {str(e)}"
        )
