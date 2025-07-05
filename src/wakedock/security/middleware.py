"""
Security and Audit Middleware

Middleware for automatic security logging and monitoring:
- Request/response logging
- Authentication event tracking
- Rate limiting
- Suspicious activity detection
- Security headers
"""

import time
import json
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

from wakedock.security.audit import get_audit_service, AuditEventType, AuditSeverity
from wakedock.api.auth.jwt import verify_token

logger = logging.getLogger(__name__)


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive security and audit logging"""
    
    def __init__(self, app, 
                 log_requests: bool = True,
                 log_responses: bool = True,
                 sensitive_headers: list = None,
                 excluded_paths: list = None):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.audit_service = get_audit_service()
        
        # Headers to exclude from logging (sensitive data)
        self.sensitive_headers = sensitive_headers or [
            'authorization', 'cookie', 'x-api-key', 'x-auth-token'
        ]
        
        # Paths to exclude from detailed logging
        self.excluded_paths = excluded_paths or [
            '/health', '/metrics', '/favicon.ico'
        ]
        
        # Rate limiting tracking
        self.request_counts = defaultdict(lambda: deque())
        self.failed_login_attempts = defaultdict(lambda: deque())
        
        # Security thresholds
        self.max_requests_per_minute = 100
        self.max_login_failures = 5
        self.login_failure_window = timedelta(minutes=15)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response for security and audit logging"""
        start_time = time.time()
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', '')
        
        # Check if path should be excluded from detailed logging
        should_log_detailed = not any(
            excluded in str(request.url.path) for excluded in self.excluded_paths
        )
        
        # Get user information if authenticated
        user_info = await self._extract_user_info(request)
        
        # Rate limiting check
        if await self._check_rate_limiting(client_ip, request.url.path):
            await self.audit_service.log_security_violation(
                "rate_limit_exceeded",
                f"Rate limit exceeded for IP {client_ip}",
                user_id=user_info.get('user_id') if user_info else None,
                username=user_info.get('username') if user_info else None,
                ip_address=client_ip,
                metadata={
                    "endpoint": str(request.url.path),
                    "method": request.method,
                    "user_agent": user_agent
                }
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # Check for suspicious activity
        await self._detect_suspicious_activity(request, client_ip, user_info)
        
        # Log request if enabled and not excluded
        if self.log_requests and should_log_detailed:
            await self._log_request(request, client_ip, user_agent, user_info)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            await self.audit_service.log_event(
                event_type=AuditEventType.API_ERROR,
                severity=AuditSeverity.HIGH,
                user_id=user_info.get('user_id') if user_info else None,
                username=user_info.get('username') if user_info else None,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=str(request.url.path),
                method=request.method,
                action="api_error",
                description=f"API error: {str(e)}",
                success=False,
                error_message=str(e)
            )
            raise
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Add security headers
        response = self._add_security_headers(response)
        
        # Log response if enabled and not excluded
        if self.log_responses and should_log_detailed:
            await self._log_response(request, response, process_time, client_ip, user_info)
        
        # Track login failures for rate limiting
        if request.url.path.endswith('/login') and response.status_code >= 400:
            await self._track_login_failure(client_ip, user_info)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address, considering proxy headers"""
        # Check for real IP in proxy headers
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else 'unknown'
    
    async def _extract_user_info(self, request: Request) -> Optional[dict]:
        """Extract user information from JWT token if present"""
        try:
            authorization = request.headers.get('authorization')
            if not authorization:
                return None
            
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != 'bearer':
                return None
            
            token_data = verify_token(token)
            if token_data:
                return {
                    'user_id': token_data.user_id,
                    'username': token_data.username,
                    'role': token_data.role.value if token_data.role else None
                }
        except Exception:
            pass
        
        return None
    
    async def _check_rate_limiting(self, client_ip: str, endpoint: str) -> bool:
        """Check if client has exceeded rate limits"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.request_counts[client_ip] = deque([
            req_time for req_time in self.request_counts[client_ip]
            if req_time > minute_ago
        ])
        
        # Add current request
        self.request_counts[client_ip].append(now)
        
        # Check if limit exceeded
        return len(self.request_counts[client_ip]) > self.max_requests_per_minute
    
    async def _detect_suspicious_activity(self, request: Request, client_ip: str, user_info: Optional[dict]):
        """Detect and log suspicious activities"""
        suspicious_patterns = []
        
        # Check for SQL injection patterns
        query_string = str(request.url.query)
        if any(pattern in query_string.lower() for pattern in [
            'union select', 'drop table', 'exec(', '1=1', 'or 1=1'
        ]):
            suspicious_patterns.append("potential_sql_injection")
        
        # Check for XSS patterns
        if any(pattern in query_string.lower() for pattern in [
            '<script>', 'javascript:', 'onerror=', 'onload='
        ]):
            suspicious_patterns.append("potential_xss")
        
        # Check for path traversal
        if any(pattern in str(request.url.path) for pattern in [
            '../', '..\\', '/etc/passwd', '/windows/system32'
        ]):
            suspicious_patterns.append("potential_path_traversal")
        
        # Check for unusual user agents
        user_agent = request.headers.get('user-agent', '').lower()
        if any(bot in user_agent for bot in [
            'sqlmap', 'nikto', 'nmap', 'burp', 'zap'
        ]):
            suspicious_patterns.append("security_scanner_detected")
        
        # Log suspicious activities
        for pattern in suspicious_patterns:
            await self.audit_service.log_security_violation(
                pattern,
                f"Suspicious activity detected: {pattern}",
                user_id=user_info.get('user_id') if user_info else None,
                username=user_info.get('username') if user_info else None,
                ip_address=client_ip,
                metadata={
                    "endpoint": str(request.url.path),
                    "query_string": query_string,
                    "user_agent": request.headers.get('user-agent', ''),
                    "method": request.method
                }
            )
    
    async def _log_request(self, request: Request, client_ip: str, user_agent: str, user_info: Optional[dict]):
        """Log incoming API request"""
        # Filter sensitive headers
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in self.sensitive_headers
        }
        
        metadata = {
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": dict(request.query_params),
            "headers": dict(headers),
            "content_type": request.headers.get('content-type'),
            "content_length": request.headers.get('content-length')
        }
        
        await self.audit_service.log_event(
            event_type=AuditEventType.API_ACCESS,
            severity=AuditSeverity.LOW,
            user_id=user_info.get('user_id') if user_info else None,
            username=user_info.get('username') if user_info else None,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint=str(request.url.path),
            method=request.method,
            action="api_request",
            description=f"{request.method} {request.url.path}",
            metadata=metadata
        )
    
    async def _log_response(self, request: Request, response: Response, 
                          process_time: float, client_ip: str, user_info: Optional[dict]):
        """Log API response"""
        metadata = {
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type'),
            "content_length": response.headers.get('content-length'),
            "process_time_seconds": round(process_time, 4)
        }
        
        # Determine severity based on status code
        if response.status_code >= 500:
            severity = AuditSeverity.HIGH
        elif response.status_code >= 400:
            severity = AuditSeverity.MEDIUM
        else:
            severity = AuditSeverity.LOW
        
        await self.audit_service.log_event(
            event_type=AuditEventType.API_ACCESS,
            severity=severity,
            user_id=user_info.get('user_id') if user_info else None,
            username=user_info.get('username') if user_info else None,
            ip_address=client_ip,
            endpoint=str(request.url.path),
            method=request.method,
            action="api_response",
            description=f"{request.method} {request.url.path} -> {response.status_code}",
            metadata=metadata,
            success=response.status_code < 400
        )
    
    async def _track_login_failure(self, client_ip: str, user_info: Optional[dict]):
        """Track login failures for enhanced security monitoring"""
        now = datetime.now()
        window_start = now - self.login_failure_window
        
        # Clean old failures
        self.failed_login_attempts[client_ip] = deque([
            failure_time for failure_time in self.failed_login_attempts[client_ip]
            if failure_time > window_start
        ])
        
        # Add current failure
        self.failed_login_attempts[client_ip].append(now)
        
        # Check if threshold exceeded
        if len(self.failed_login_attempts[client_ip]) >= self.max_login_failures:
            await self.audit_service.log_security_violation(
                "multiple_login_failures",
                f"Multiple login failures from IP {client_ip}",
                user_id=user_info.get('user_id') if user_info else None,
                username=user_info.get('username') if user_info else None,
                ip_address=client_ip,
                metadata={
                    "failure_count": len(self.failed_login_attempts[client_ip]),
                    "time_window_minutes": self.login_failure_window.total_seconds() / 60
                }
            )
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        # Security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request timing and performance"""
    
    def __init__(self, app, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.audit_service = get_audit_service()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Add timing header
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log slow requests
        if process_time > self.slow_request_threshold:
            user_info = await self._extract_user_info(request)
            
            await self.audit_service.log_event(
                event_type=AuditEventType.API_ACCESS,
                severity=AuditSeverity.MEDIUM,
                user_id=user_info.get('user_id') if user_info else None,
                username=user_info.get('username') if user_info else None,
                ip_address=request.client.host if request.client else 'unknown',
                endpoint=str(request.url.path),
                method=request.method,
                action="slow_request",
                description=f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s",
                metadata={
                    "process_time_seconds": process_time,
                    "threshold_seconds": self.slow_request_threshold
                }
            )
        
        return response
    
    async def _extract_user_info(self, request: Request) -> dict:
        """Extract user information from request"""
        try:
            authorization = request.headers.get('authorization')
            if not authorization:
                return {}
            
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != 'bearer':
                return {}
            
            token_data = verify_token(token)
            if token_data:
                return {
                    'user_id': token_data.user_id,
                    'username': token_data.username
                }
        except Exception:
            pass
        
        return {}


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security logging"""
    
    def __init__(self, app, allowed_origins: list = None, log_cors_violations: bool = True):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.log_cors_violations = log_cors_violations
        self.audit_service = get_audit_service()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get('origin')
        
        # Check for CORS violations
        if origin and self.log_cors_violations and "*" not in self.allowed_origins:
            if origin not in self.allowed_origins:
                await self.audit_service.log_security_violation(
                    "cors_violation",
                    f"CORS violation: Unauthorized origin {origin}",
                    ip_address=request.client.host if request.client else 'unknown',
                    metadata={
                        "origin": origin,
                        "endpoint": str(request.url.path),
                        "method": request.method
                    }
                )
        
        response = await call_next(request)
        return response