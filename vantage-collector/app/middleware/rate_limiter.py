"""Rate limiting middleware for Vantage Collector.

Implements token bucket algorithm to prevent API abuse and DoS attacks.
"""

import time
from typing import Dict, Callable
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Named constants
RATE_LIMIT_WINDOW_SECONDS = 60  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 1000  # Max requests per window
RATE_LIMIT_ENABLED_DEFAULT = True


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, max_tokens: int, refill_rate: float):
        """Initialize token bucket.
        
        Args:
            max_tokens: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.max_tokens, self.tokens + new_tokens)
        self.last_refill = now
    
    def time_until_ready(self) -> float:
        """Calculate seconds until a token is available.
        
        Returns:
            Seconds until next token available
        """
        if self.tokens >= 1:
            return 0.0
        
        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""
    
    def __init__(
        self,
        app,
        enabled: bool = RATE_LIMIT_ENABLED_DEFAULT,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ):
        """Initialize rate limiter.
        
        Args:
            app: FastAPI application
            enabled: Whether rate limiting is enabled
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.enabled = enabled
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # Refill rate: max_requests per window = max_requests / window_seconds per second
        self.refill_rate = max_requests / window_seconds
        
        # Store buckets per client IP
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(max_requests, self.refill_rate)
        )
        
        logger.info(
            f"Rate limiting initialized: enabled={enabled}, "
            f"max_requests={max_requests}, window={window_seconds}s"
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or rate limit error
        """
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ["/health", "/ready", "/live", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Get or create bucket for this client
        bucket = self.buckets[client_ip]
        
        # Try to consume a token
        if bucket.consume():
            # Token available - allow request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time() + self.window_seconds)
            )
            
            return response
        else:
            # Rate limit exceeded
            retry_after = int(bucket.time_until_ready()) + 1
            
            logger.warning(
                f"Rate limit exceeded for {client_ip}, "
                f"retry after {retry_after}s"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {retry_after} seconds.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                }
            )
    
    def cleanup_old_buckets(self):
        """Remove inactive buckets to prevent memory leak.
        
        Should be called periodically (e.g., every hour).
        """
        now = time.time()
        inactive_threshold = now - (self.window_seconds * 2)
        
        inactive_ips = [
            ip for ip, bucket in self.buckets.items()
            if bucket.last_refill < inactive_threshold
        ]
        
        for ip in inactive_ips:
            del self.buckets[ip]
        
        if inactive_ips:
            logger.info(f"Cleaned up {len(inactive_ips)} inactive rate limit buckets")
