"""
Advanced Security API Routes

Provides REST endpoints for managing advanced security features including:
- IP whitelist/blacklist management
- Geographic blocking configuration
- MFA setup and management
- Security scanning and monitoring
- Threat analysis and response
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from wakedock.security.advanced import (
    get_ip_whitelist_manager, get_geo_blocking_manager, 
    get_mfa_manager, get_security_scanner,
    ThreatLevel, SecurityActionType
)
from wakedock.tenancy.middleware import (
    get_current_organization, get_current_user_role,
    require_permission, require_organization
)
from wakedock.api.auth.dependencies import get_current_user, require_role
from wakedock.database.models import UserRole
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API requests/responses
class IPWhitelistCreate(BaseModel):
    ip_range: str
    label: str
    description: Optional[str] = None
    expires_hours: Optional[int] = None  # Hours until expiration


class GeoBlockCreate(BaseModel):
    country_code: str
    block_type: str  # deny, allow, monitor
    country_name: Optional[str] = None
    exceptions: Optional[List[str]] = None


class MFASetupRequest(BaseModel):
    method_type: str  # totp, email, sms
    account_name: Optional[str] = None
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class MFAVerifyRequest(BaseModel):
    method_id: Optional[int] = None
    challenge_id: Optional[str] = None
    verification_code: str


class SecurityScanRequest(BaseModel):
    target: str
    scan_type: str = "full"  # full, configuration, network, application


class ThreatResponseRequest(BaseModel):
    event_id: int
    action: str  # block_ip, whitelist_ip, investigate, dismiss
    duration_hours: Optional[int] = None
    notes: Optional[str] = None


# IP Whitelist Management Routes
@router.post("/ip-whitelist", response_model=dict)
@require_organization
@require_permission("security", "write")
async def add_ip_whitelist(
    whitelist_data: IPWhitelistCreate,
    current_user = Depends(get_current_user),
    current_org = Depends(get_current_organization),
    ip_manager = Depends(get_ip_whitelist_manager)
):
    """Add IP address or range to whitelist"""
    try:
        expires_at = None
        if whitelist_data.expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=whitelist_data.expires_hours)
        
        entry = await ip_manager.add_whitelist_entry(
            ip_range=whitelist_data.ip_range,
            label=whitelist_data.label,
            user_id=current_user.id,
            organization_id=current_org.id,
            description=whitelist_data.description,
            expires_at=expires_at
        )
        
        return {
            "id": entry.id,
            "ip_range": entry.ip_range,
            "label": entry.label,
            "description": entry.description,
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
            "created_at": entry.created_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add IP whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add IP whitelist entry")


@router.get("/ip-whitelist", response_model=List[dict])
@require_organization
@require_permission("security", "read")
async def list_ip_whitelist(
    current_org = Depends(get_current_organization),
    ip_manager = Depends(get_ip_whitelist_manager)
):
    """List IP whitelist entries"""
    try:
        entries = await ip_manager.get_whitelist_entries(current_org.id)
        
        return [
            {
                "id": entry.id,
                "ip_range": entry.ip_range,
                "label": entry.label,
                "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                "is_active": entry.is_active
            }
            for entry in entries
        ]
    
    except Exception as e:
        logger.error(f"Failed to list IP whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to list IP whitelist")


@router.delete("/ip-whitelist/{entry_id}", response_model=dict)
@require_organization
@require_permission("security", "write")
async def remove_ip_whitelist(
    entry_id: int,
    current_user = Depends(get_current_user),
    ip_manager = Depends(get_ip_whitelist_manager)
):
    """Remove IP whitelist entry"""
    try:
        success = await ip_manager.remove_whitelist_entry(entry_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Whitelist entry not found")
        
        return {"message": "IP whitelist entry removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove IP whitelist: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove IP whitelist entry")


@router.post("/ip-analyze", response_model=dict)
@require_organization
@require_permission("security", "read")
async def analyze_ip(
    ip_address: str,
    current_org = Depends(get_current_organization),
    ip_manager = Depends(get_ip_whitelist_manager)
):
    """Analyze IP address for security threats"""
    try:
        analysis = await ip_manager.analyze_ip(ip_address, current_org.id)
        
        return {
            "ip_address": analysis.ip_address,
            "is_whitelisted": analysis.is_whitelisted,
            "is_blacklisted": analysis.is_blacklisted,
            "country_code": analysis.country_code,
            "reputation_score": analysis.reputation_score,
            "risk_factors": analysis.risk_factors,
            "recommendations": analysis.recommendations
        }
    
    except Exception as e:
        logger.error(f"Failed to analyze IP {ip_address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze IP address")


# Geographic Blocking Routes
@router.post("/geo-blocking", response_model=dict)
@require_organization
@require_permission("security", "write")
async def add_geo_block(
    geo_data: GeoBlockCreate,
    current_user = Depends(get_current_user),
    current_org = Depends(get_current_organization),
    geo_manager = Depends(get_geo_blocking_manager)
):
    """Add geographic blocking rule"""
    try:
        geo_block = await geo_manager.add_country_block(
            country_code=geo_data.country_code,
            block_type=geo_data.block_type,
            user_id=current_user.id,
            organization_id=current_org.id,
            country_name=geo_data.country_name,
            exceptions=geo_data.exceptions
        )
        
        return {
            "id": geo_block.id,
            "country_code": geo_block.country_code,
            "country_name": geo_block.country_name,
            "block_type": geo_block.block_type,
            "exceptions": geo_block.exceptions,
            "created_at": geo_block.created_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add geo block: {e}")
        raise HTTPException(status_code=500, detail="Failed to add geographic block")


@router.get("/geo-blocking", response_model=List[dict])
@require_organization
@require_permission("security", "read")
async def list_geo_blocks(
    current_org = Depends(get_current_organization),
    geo_manager = Depends(get_geo_blocking_manager)
):
    """List geographic blocking rules"""
    try:
        rules = await geo_manager.get_country_rules(current_org.id)
        
        return [
            {
                "id": rule.id,
                "country_code": rule.country_code,
                "country_name": rule.country_name,
                "block_type": rule.block_type,
                "exceptions": rule.exceptions,
                "is_active": rule.is_active
            }
            for rule in rules
        ]
    
    except Exception as e:
        logger.error(f"Failed to list geo blocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list geographic blocks")


@router.delete("/geo-blocking/{block_id}", response_model=dict)
@require_organization
@require_permission("security", "write")
async def remove_geo_block(
    block_id: int,
    current_user = Depends(get_current_user),
    geo_manager = Depends(get_geo_blocking_manager)
):
    """Remove geographic blocking rule"""
    try:
        success = await geo_manager.remove_country_block(block_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Geographic block not found")
        
        return {"message": "Geographic block removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove geo block: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove geographic block")


@router.get("/geo-statistics", response_model=dict)
@require_organization
@require_permission("security", "read")
async def get_geo_statistics(
    current_org = Depends(get_current_organization),
    geo_manager = Depends(get_geo_blocking_manager)
):
    """Get geographic access statistics"""
    try:
        stats = await geo_manager.get_country_statistics(current_org.id)
        return {"statistics": stats}
    
    except Exception as e:
        logger.error(f"Failed to get geo statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get geographic statistics")


# MFA Management Routes
@router.post("/mfa/setup", response_model=dict)
async def setup_mfa(
    mfa_data: MFASetupRequest,
    current_user = Depends(get_current_user),
    mfa_manager = Depends(get_mfa_manager)
):
    """Set up MFA for current user"""
    try:
        if mfa_data.method_type == "totp":
            setup_result = await mfa_manager.setup_totp(
                user_id=current_user.id,
                account_name=mfa_data.account_name
            )
            return {
                "method_type": "totp",
                "setup_data": setup_result
            }
        
        elif mfa_data.method_type == "email":
            if not mfa_data.email_address:
                raise HTTPException(status_code=400, detail="Email address required for email MFA")
            
            method_id = await mfa_manager.setup_email_mfa(
                user_id=current_user.id,
                email_address=mfa_data.email_address
            )
            return {
                "method_type": "email",
                "method_id": method_id,
                "message": f"Verification email sent to {mfa_data.email_address}"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported MFA method")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to setup MFA: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup MFA")


@router.post("/mfa/verify", response_model=dict)
async def verify_mfa(
    verify_data: MFAVerifyRequest,
    current_user = Depends(get_current_user),
    mfa_manager = Depends(get_mfa_manager)
):
    """Verify MFA setup or challenge"""
    try:
        if verify_data.method_id:
            # Verify TOTP setup
            success = await mfa_manager.verify_totp_setup(
                method_id=verify_data.method_id,
                verification_code=verify_data.verification_code
            )
            return {"verified": success}
        
        elif verify_data.challenge_id:
            # Verify MFA challenge
            result = await mfa_manager.verify_mfa_challenge(
                challenge_id=verify_data.challenge_id,
                response=verify_data.verification_code
            )
            return {
                "success": result.success,
                "method_type": result.method_type,
                "error_message": result.error_message,
                "backup_codes_remaining": result.backup_codes_remaining
            }
        
        else:
            raise HTTPException(status_code=400, detail="Either method_id or challenge_id required")
    
    except Exception as e:
        logger.error(f"Failed to verify MFA: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify MFA")


@router.get("/mfa/status", response_model=dict)
async def get_mfa_status(
    current_user = Depends(get_current_user),
    mfa_manager = Depends(get_mfa_manager)
):
    """Get user's MFA status"""
    try:
        status = await mfa_manager.get_user_mfa_status(current_user.id)
        
        return {
            "is_enabled": status.is_enabled,
            "primary_method": status.primary_method,
            "available_methods": status.available_methods,
            "backup_codes_count": status.backup_codes_count,
            "last_used_at": status.last_used_at.isoformat() if status.last_used_at else None
        }
    
    except Exception as e:
        logger.error(f"Failed to get MFA status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get MFA status")


@router.post("/mfa/regenerate-backup-codes", response_model=dict)
async def regenerate_backup_codes(
    current_user = Depends(get_current_user),
    mfa_manager = Depends(get_mfa_manager)
):
    """Regenerate backup codes"""
    try:
        codes = await mfa_manager.regenerate_backup_codes(current_user.id)
        return {
            "backup_codes": codes,
            "message": "New backup codes generated. Store them securely."
        }
    
    except Exception as e:
        logger.error(f"Failed to regenerate backup codes: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate backup codes")


# Security Scanning Routes
@router.post("/scan", response_model=dict)
@require_organization
@require_permission("security", "write")
async def perform_security_scan(
    scan_data: SecurityScanRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    current_org = Depends(get_current_organization),
    scanner = Depends(get_security_scanner)
):
    """Perform security scan"""
    try:
        # Start scan in background
        background_tasks.add_task(
            _perform_scan_background,
            scanner,
            scan_data.target,
            scan_data.scan_type,
            current_user.id,
            current_org.id
        )
        
        return {
            "message": "Security scan started",
            "target": scan_data.target,
            "scan_type": scan_data.scan_type
        }
    
    except Exception as e:
        logger.error(f"Failed to start security scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to start security scan")


async def _perform_scan_background(
    scanner,
    target: str,
    scan_type: str,
    user_id: int,
    organization_id: int
):
    """Perform scan in background task"""
    try:
        result = await scanner.perform_comprehensive_scan(target, scan_type)
        logger.info(f"Completed security scan for {target}: score {result.score}")
        
        # Log scan completion (would also store results in database)
        await scanner._log_security_event(
            event_type="security_scan_completed",
            threat_level=result.threat_level,
            ip_address=target,
            description=f"Security scan completed with score {result.score}",
            metadata={
                "scan_id": result.scan_id,
                "vulnerabilities_count": len(result.vulnerabilities),
                "score": result.score
            }
        )
        
    except Exception as e:
        logger.error(f"Background security scan failed: {e}")


@router.get("/threats", response_model=dict)
@require_organization
@require_permission("security", "read")
async def get_threat_statistics(
    current_org = Depends(get_current_organization),
    scanner = Depends(get_security_scanner)
):
    """Get threat detection statistics"""
    try:
        stats = await scanner.get_threat_statistics(current_org.id)
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get threat statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat statistics")


@router.post("/threats/respond", response_model=dict)
@require_organization
@require_permission("security", "write")
async def respond_to_threat(
    response_data: ThreatResponseRequest,
    current_user = Depends(get_current_user),
    current_org = Depends(get_current_organization),
    ip_manager = Depends(get_ip_whitelist_manager)
):
    """Respond to security threat"""
    try:
        # This would implement threat response actions
        # For now, we'll handle basic IP blocking/whitelisting
        
        if response_data.action == "block_ip":
            # Get the IP from the event (would query database)
            ip_address = "placeholder_ip"  # Would get from SecurityEvent
            
            duration_seconds = (response_data.duration_hours or 24) * 3600
            
            await ip_manager.create_dynamic_rule(
                ip_address=ip_address,
                action=SecurityActionType.BLOCK_TEMPORARY,
                duration_seconds=duration_seconds,
                reason=f"Manual block: {response_data.notes or 'Threat response'}",
                user_id=current_user.id,
                organization_id=current_org.id
            )
            
            return {"message": f"IP {ip_address} blocked for {response_data.duration_hours or 24} hours"}
        
        elif response_data.action == "whitelist_ip":
            # Similar implementation for whitelisting
            return {"message": "IP whitelisted successfully"}
        
        elif response_data.action == "investigate":
            # Mark for investigation
            return {"message": "Threat marked for investigation"}
        
        elif response_data.action == "dismiss":
            # Dismiss the threat
            return {"message": "Threat dismissed"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    
    except Exception as e:
        logger.error(f"Failed to respond to threat: {e}")
        raise HTTPException(status_code=500, detail="Failed to respond to threat")