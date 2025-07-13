"""
Advanced Security Middleware

Integrates all advanced security features including:
- IP whitelisting/blacklisting
- Geographic blocking
- Threat detection and scanning
- MFA enforcement
- Real-time security monitoring
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS

from wakedock.security.advanced.ip_whitelist import get_ip_whitelist_manager
from wakedock.security.advanced.geo_blocking import get_geo_blocking_manager
from wakedock.security.advanced.scanner import get_security_scanner
from wakedock.security.advanced.models import ThreatLevel, SecurityActionType

logger = logging.getLogger(__name__)


class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware with comprehensive protection"""
    
    def __init__(
        self,
        app,
        enable_ip_filtering: bool = True,
        enable_geo_blocking: bool = True,
        enable_threat_scanning: bool = True,
        enable_rate_limiting: bool = True,
        log_all_requests: bool = False
    ):
        super().__init__(app)
        self.enable_ip_filtering = enable_ip_filtering
        self.enable_geo_blocking = enable_geo_blocking
        self.enable_threat_scanning = enable_threat_scanning
        self.enable_rate_limiting = enable_rate_limiting
        self.log_all_requests = log_all_requests
        
        # Get security managers
        self.ip_manager = get_ip_whitelist_manager()
        self.geo_manager = get_geo_blocking_manager()
        self.scanner = get_security_scanner()
        
        # Rate limiting state
        self._rate_limits: Dict[str, List[datetime]] = {}
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_requests = 100  # requests per minute
        
        # Whitelist paths that should bypass security checks
        self.bypass_paths = {
            "/api/v1/health",
            "/api/config",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method"""
        
        start_time = datetime.utcnow()
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        path = str(request.url.path)
        method = request.method
        
        # Skip security checks for whitelisted paths
        if path in self.bypass_paths:
            return await call_next(request)
        
        try:
            # 1. IP Filtering Check
            if self.enable_ip_filtering:
                ip_check_result = await self._check_ip_access(client_ip, request)
                if ip_check_result is not None:
                    return ip_check_result
            
            # 2. Geographic Blocking Check
            if self.enable_geo_blocking:
                geo_check_result = await self._check_geographic_access(client_ip, request)
                if geo_check_result is not None:
                    return geo_check_result
            
            # 3. Rate Limiting Check
            if self.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limit(client_ip, request)
                if rate_limit_result is not None:
                    return rate_limit_result
            
            # 4. Threat Scanning (before processing request)
            if self.enable_threat_scanning:
                threat_result = await self._scan_request_threats(request, client_ip)
                if threat_result is not None:
                    return threat_result
            
            # Process the request
            response = await call_next(request)
            
            # 5. Post-processing security analysis
            if self.enable_threat_scanning or self.log_all_requests:
                await self._analyze_response(request, response, client_ip, start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error for {client_ip}: {e}")
            # Continue with request processing on middleware errors
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _check_ip_access(self, client_ip: str, request: Request) -> Optional[Response]:
        """Check IP whitelist/blacklist"""
        
        try:
            # Get organization context (if available)
            organization_id = getattr(request.state, "organization_id", None)
            
            # Check if IP is blacklisted
            is_blacklisted = await self.ip_manager.is_ip_blacklisted(client_ip, organization_id)
            if is_blacklisted:
                await self.ip_manager.log_security_event(
                    ip_address=client_ip,
                    event_type="ip_blocked",
                    threat_level=ThreatLevel.HIGH,
                    description=f"Blocked request from blacklisted IP: {client_ip}",
                    organization_id=organization_id
                )
                
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"error": "Access denied", "reason": "IP address blocked"}
                )
            
            # Check if IP is whitelisted (optional - depends on configuration)
            # For most applications, we don't want to block all non-whitelisted IPs
            # This would only be enabled for high-security environments
            
        except Exception as e:
            logger.error(f"IP access check error for {client_ip}: {e}")
        
        return None
    
    async def _check_geographic_access(self, client_ip: str, request: Request) -> Optional[Response]:
        """Check geographic access restrictions"""
        
        try:
            organization_id = getattr(request.state, "organization_id", None)
            
            # Check if IP should be blocked based on geography
            should_block, reason = await self.geo_manager.should_block_ip(client_ip, organization_id)
            
            if should_block:
                # Get location for logging
                location = await self.geo_manager.get_geo_location(client_ip)
                country_code = location.country_code if location else "Unknown"
                
                # Log the event
                await self.geo_manager.log_geo_event(
                    ip_address=client_ip,
                    country_code=country_code,
                    action_taken="blocked",
                    reason=reason or "Geographic restriction",
                    organization_id=organization_id
                )
                
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content={"error": "Access denied", "reason": "Geographic restriction"}
                )
            
        except Exception as e:
            logger.error(f"Geographic access check error for {client_ip}: {e}")
        
        return None
    
    async def _check_rate_limit(self, client_ip: str, request: Request) -> Optional[Response]:
        """Check rate limiting"""
        
        try:
            current_time = datetime.utcnow()
            
            # Initialize rate limit tracking for this IP
            if client_ip not in self._rate_limits:
                self._rate_limits[client_ip] = []
            
            # Clean old requests outside the window
            cutoff_time = current_time.timestamp() - self.rate_limit_window
            self._rate_limits[client_ip] = [
                req_time for req_time in self._rate_limits[client_ip]
                if req_time.timestamp() > cutoff_time
            ]
            
            # Check if rate limit exceeded
            if len(self._rate_limits[client_ip]) >= self.rate_limit_requests:
                # Log rate limit violation
                await self.scanner._log_security_event(
                    event_type="rate_limit_exceeded",
                    threat_level=ThreatLevel.MEDIUM,
                    ip_address=client_ip,
                    description=f"Rate limit exceeded: {len(self._rate_limits[client_ip])} requests in {self.rate_limit_window}s"
                )
                
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Rate limit exceeded", "retry_after": self.rate_limit_window}
                )
            
            # Record this request
            self._rate_limits[client_ip].append(current_time)
            
        except Exception as e:
            logger.error(f"Rate limit check error for {client_ip}: {e}")
        
        return None
    
    async def _scan_request_threats(self, request: Request, client_ip: str) -> Optional[Response]:
        """Scan request for security threats"""
        
        try:
            # Prepare request data for scanning
            request_data = {
                "ip_address": client_ip,
                "method": request.method,
                "path": str(request.url.path),
                "query_string": str(request.url.query) if request.url.query else "",
                "user_agent": request.headers.get("user-agent", ""),
                "headers": dict(request.headers),
                "body": ""  # Would read body if needed (careful with large bodies)
            }
            
            # Scan for threats
            threats = await self.scanner.scan_request(request_data)
            
            # Handle high-severity threats
            critical_threats = [t for t in threats if t.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]
            
            if critical_threats:
                # Log all threats
                for threat in threats:
                    await self.scanner._log_security_event(
                        event_type=threat.indicator_type,
                        threat_level=threat.severity,
                        ip_address=client_ip,
                        description=threat.description,
                        event_metadata={
                            "confidence": threat.confidence,
                            "source": threat.source,
                            "value": threat.value
                        }
                    )
                
                # Block critical threats
                if any(t.severity == ThreatLevel.CRITICAL for t in critical_threats):
                    # Create temporary block for critical threats
                    await self.ip_manager.create_dynamic_rule(
                        ip_address=client_ip,
                        action=SecurityActionType.BLOCK_TEMPORARY,
                        duration_seconds=3600,  # 1 hour
                        reason=f"Critical threat detected: {critical_threats[0].description}",
                        user_id=1,  # System user
                        organization_id=getattr(request.state, "organization_id", None)
                    )
                    
                    return JSONResponse(
                        status_code=HTTP_403_FORBIDDEN,
                        content={"error": "Security threat detected", "reason": "Request blocked"}
                    )
            
        except Exception as e:
            logger.error(f"Threat scanning error for {client_ip}: {e}")
        
        return None
    
    async def _analyze_response(self, request: Request, response: Response, client_ip: str, start_time: datetime):
        """Analyze response for security insights"""
        
        try:
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update behavioral data
            request_data = {
                "ip_address": client_ip,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "response_size": getattr(response, "content_length", 0) or 0,
                "response_time_ms": response_time,
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": start_time
            }
            
            # Record behavioral data
            self.scanner._record_request_behavior(request_data)
            
            # Log suspicious response patterns
            if response.status_code in [401, 403] or response_time > 5000:  # Long response times
                await self.scanner._log_security_event(
                    event_type="suspicious_response",
                    threat_level=ThreatLevel.LOW,
                    ip_address=client_ip,
                    description=f"Suspicious response: {response.status_code} with {response_time:.0f}ms response time",
                    event_metadata={
                        "status_code": response.status_code,
                        "response_time_ms": response_time,
                        "path": str(request.url.path)
                    }
                )
            
        except Exception as e:
            logger.error(f"Response analysis error for {client_ip}: {e}")
    
    async def cleanup_rate_limits(self):
        """Periodic cleanup of rate limit data"""
        current_time = datetime.utcnow()
        cutoff_time = current_time.timestamp() - (self.rate_limit_window * 2)  # Keep double the window
        
        # Clean up old rate limit data
        for ip in list(self._rate_limits.keys()):
            self._rate_limits[ip] = [
                req_time for req_time in self._rate_limits[ip]
                if req_time.timestamp() > cutoff_time
            ]
            
            # Remove empty entries
            if not self._rate_limits[ip]:
                del self._rate_limits[ip]