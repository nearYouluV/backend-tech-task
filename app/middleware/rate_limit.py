import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        
        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory token buckets."""
    
    def __init__(self, app, rate_limit_per_minute: int = None):
        super().__init__(app)
        self.rate_limit_per_minute = rate_limit_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                capacity=self.rate_limit_per_minute,
                refill_rate=self.rate_limit_per_minute / 60.0  
            )
        )
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP", "") or
            request.client.host if request.client else "unknown"
        )
        return client_ip
    
    def _cleanup_old_buckets(self):
        """Clean up old unused buckets to prevent memory leaks."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff_time = now - 3600
            to_remove = [
                client_id for client_id, bucket in self.buckets.items()
                if bucket.last_refill < cutoff_time
            ]
            
            for client_id in to_remove:
                del self.buckets[client_id]
            
            self.last_cleanup = now
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old rate limit buckets")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        bucket = self.buckets[client_id]
        
        if not bucket.consume():
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path,
                method=request.method
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
    
        self._cleanup_old_buckets()
        
        return response
