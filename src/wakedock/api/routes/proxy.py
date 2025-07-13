"""
Proxy endpoints for handling service requests
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import re

router = APIRouter()
logger = logging.getLogger(__name__)

def validate_subdomain(subdomain: str) -> bool:
    """Validate subdomain to prevent security issues"""
    if not subdomain:
        return False
    
    # Check for path traversal attempts
    if '..' in subdomain or '//' in subdomain:
        return False
    
    # Check for malicious patterns
    dangerous_patterns = [
        r'[<>"\']',  # HTML/script injection
        r'[\x00-\x1f\x7f-\x9f]',  # Control characters
        r'[;&|`$]',  # Command injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, subdomain):
            return False
    
    return True


@router.get("/{subdomain:path}", include_in_schema=False)
async def proxy_request(request: Request, subdomain: str):
    """Handle proxy requests to services"""
    # Validate subdomain input for security
    if not validate_subdomain(subdomain):
        logger.warning(f"Invalid subdomain request: {subdomain}")
        raise HTTPException(status_code=400, detail="Invalid subdomain format")
    
    # This will be handled by the ProxyMiddleware
    # This endpoint is just a fallback
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WakeDock</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            .logo { font-size: 2em; margin-bottom: 20px; }
            .message { font-size: 1.2em; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🐳 WakeDock</div>
            <div class="message">
                Service not found or not configured.
            </div>
        </div>
    </body>
    </html>
    """)


@router.api_route("/{subdomain:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
async def proxy_request_all_methods(request: Request, subdomain: str):
    """Handle all HTTP methods for proxy requests"""
    # Validate subdomain input for security
    if not validate_subdomain(subdomain):
        logger.warning(f"Invalid subdomain request: {subdomain}")
        raise HTTPException(status_code=400, detail="Invalid subdomain format")
    
    return await proxy_request(request, subdomain)
