"""
Global error handler middleware for the WakeDock API.
Provides centralized error handling, logging, and response formatting.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...exceptions import (
    WakeDockException,
    DockerException,
    CaddyException,
    ValidationException,
    AuthenticationException,
    AuthorizationException
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all application errors globally."""
    
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Handle request and catch any exceptions."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._handle_exception(request, exc)
    
    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of exceptions."""
        
        # Log the exception
        logger.error(
            f"Exception occurred: {type(exc).__name__}: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else None,
                "traceback": traceback.format_exc() if self.debug else None
            }
        )
        
        # Handle specific exception types
        if isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc)
        elif isinstance(exc, WakeDockException):
            return await self._handle_wakedock_exception(exc)
        else:
            return await self._handle_generic_exception(exc)
    
    async def _handle_http_exception(self, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail,
                    "status_code": exc.status_code
                }
            }
        )
    
    async def _handle_wakedock_exception(self, exc: WakeDockException) -> JSONResponse:
        """Handle custom WakeDock exceptions."""
        status_code = self._get_status_code_for_exception(exc)
        
        error_data = {
            "error": {
                "type": exc.__class__.__name__.lower().replace("exception", ""),
                "message": str(exc),
                "code": getattr(exc, 'code', None)
            }
        }
        
        # Add additional context if available
        if hasattr(exc, 'context') and exc.context:
            error_data["error"]["context"] = exc.context
        
        if self.debug and hasattr(exc, 'details'):
            error_data["error"]["details"] = exc.details
        
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )
    
    async def _handle_generic_exception(self, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.critical(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        
        if self.debug:
            error_data = {
                "error": {
                    "type": "internal_error",
                    "message": str(exc),
                    "traceback": traceback.format_exc()
                }
            }
        else:
            error_data = {
                "error": {
                    "type": "internal_error",
                    "message": "An internal server error occurred"
                }
            }
        
        return JSONResponse(
            status_code=500,
            content=error_data
        )
    
    def _get_status_code_for_exception(self, exc: WakeDockException) -> int:
        """Map exception types to HTTP status codes."""
        status_map = {
            ValidationException: 400,
            AuthenticationException: 401,
            AuthorizationException: 403,
            DockerException: 500,
            CaddyException: 500,
        }
        
        return status_map.get(type(exc), 500)


def create_error_response(
    message: str,
    error_type: str = "error",
    status_code: int = 500,
    context: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response."""
    error_data = {
        "error": {
            "type": error_type,
            "message": message
        }
    }
    
    if context:
        error_data["error"]["context"] = context
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


def handle_validation_error(errors: list) -> JSONResponse:
    """Handle Pydantic validation errors."""
    formatted_errors = []
    
    for error in errors:
        formatted_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Validation failed",
                "details": formatted_errors
            }
        }
    )
