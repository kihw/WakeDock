"""
Rate limiting middleware for the WakeDock API.
Implements token bucket algorithm for rate limiting requests.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        async with self._lock:
            now = time.time()
            # Add tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Calculate how long to wait for tokens to be available."""
        if self.tokens >= tokens:
            return 0.0
        
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        key_func: Optional[callable] = None,
        cleanup_interval: int = 300  # 5 minutes
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Base rate limit per minute
            burst_size: Maximum burst size (defaults to requests_per_minute)
            key_func: Function to extract rate limit key from request
            cleanup_interval: Interval to cleanup old buckets (seconds)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.key_func = key_func or self._default_key_func
        self.cleanup_interval = cleanup_interval
        
        # Convert per-minute to per-second
        self.refill_rate = requests_per_minute / 60.0
        
        # Storage for token buckets
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()
        
        logger.info(
            f"Rate limiter initialized: {requests_per_minute} req/min, "
            f"burst: {self.burst_size}"
        )
    
    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP."""
        if request.client:
            return f"ip:{request.client.host}"
        return "unknown"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get rate limit key
        key = self.key_func(request)
        
        # Clean up old buckets periodically
        await self._cleanup_if_needed()
        
        # Get or create token bucket
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(
                capacity=self.burst_size,
                refill_rate=self.refill_rate
            )
        
        bucket = self.buckets[key]
        
        # Try to consume a token
        if await bucket.consume():
            # Request allowed
            response = await call_next(request)
            
            # Add rate limit headers
            self._add_rate_limit_headers(response, bucket)
            return response
        else:
            # Rate limit exceeded
            wait_time = bucket.get_wait_time()
            
            logger.warning(
                f"Rate limit exceeded for {key}",
                extra={
                    "key": key,
                    "path": request.url.path,
                    "wait_time": wait_time
                }
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Too many requests",
                        "retry_after": int(wait_time)
                    }
                },
                headers={
                    "Retry-After": str(int(wait_time)),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + wait_time))
                }
            )
    
    def _add_rate_limit_headers(self, response: Response, bucket: TokenBucket):
        """Add rate limit headers to response."""
        remaining = max(0, int(bucket.tokens))
        reset_time = int(time.time() + (self.burst_size - bucket.tokens) / self.refill_rate)
        
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    async def _cleanup_if_needed(self):
        """Clean up old, unused token buckets."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets that haven't been used recently
        cutoff_time = now - self.cleanup_interval
        keys_to_remove = []
        
        for key, bucket in self.buckets.items():
            if bucket.last_refill < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} rate limit buckets")
        
        self.last_cleanup = now


class IPRateLimiter(RateLimiterMiddleware):
    """Rate limiter based on client IP address."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, key_func=self._ip_key_func, **kwargs)
    
    def _ip_key_func(self, request: Request) -> str:
        """Extract IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        forwarded_host = request.headers.get("X-Forwarded-Host")
        if forwarded_host:
            return f"ip:{forwarded_host}"
        
        # Fall back to direct client IP
        if request.client:
            return f"ip:{request.client.host}"
        
        return "ip:unknown"


class UserRateLimiter(RateLimiterMiddleware):
    """Rate limiter based on authenticated user."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, key_func=self._user_key_func, **kwargs)
    
    def _user_key_func(self, request: Request) -> str:
        """Extract user ID from request."""
        # Try to get user from request state (set by auth middleware)
        user = getattr(request.state, 'user', None)
        if user and hasattr(user, 'id'):
            return f"user:{user.id}"
        
        # Fall back to IP-based limiting
        if request.client:
            return f"ip:{request.client.host}"
        
        return "unknown"


def create_rate_limiter(
    requests_per_minute: int = 60,
    burst_size: Optional[int] = None,
    per_user: bool = False
) -> RateLimiterMiddleware:
    """
    Factory function to create rate limiter middleware.
    
    Args:
        requests_per_minute: Rate limit per minute
        burst_size: Maximum burst size
        per_user: If True, limit per user, otherwise per IP
        
    Returns:
        Configured rate limiter middleware
    """
    if per_user:
        return UserRateLimiter(
            None,  # App will be set when added to FastAPI
            requests_per_minute=requests_per_minute,
            burst_size=burst_size
        )
    else:
        return IPRateLimiter(
            None,
            requests_per_minute=requests_per_minute,
            burst_size=burst_size
        )
