"""
Rate Limiting Middleware

Provides in-memory rate limiting for API endpoints using token bucket algorithm.
For production use with multiple instances, consider Redis-based rate limiting.
"""

from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Callable, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter for API endpoints.
    
    Uses a sliding window counter approach.
    
    Example:
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        if limiter.is_allowed('user-123'):
            # Process request
            pass
        else:
            # Return 429 Too Many Requests
            pass
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (user_id, IP address, etc.)
        
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.now()
        cutoff = now - self.window
        
        with self.lock:
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]
            
            # Check limit
            if len(self.requests[identifier]) >= self.max_requests:
                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{len(self.requests[identifier])} requests in window"
                )
                return False
            
            # Record request
            self.requests[identifier].append(now)
            return True
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        with self.lock:
            if identifier in self.requests:
                del self.requests[identifier]


class TokenBucketRateLimiter:
    """
    Token bucket algorithm for rate limiting.
    
    More sophisticated than simple counter, allows controlled bursts.
    Each request consumes tokens, which refill at a constant rate.
    
    Example:
        # Allow 10 requests/sec with burst up to 20
        limiter = TokenBucketRateLimiter(rate=10, capacity=20)
        
        if limiter.is_allowed('user-123', tokens=1):
            # Process request
            pass
    """
    
    def __init__(
        self,
        rate: int,  # tokens per second
        capacity: int,  # bucket capacity
        window_seconds: int = 60
    ):
        """
        Initialize token bucket rate limiter.
        
        Args:
            rate: Token refill rate (tokens per second)
            capacity: Maximum bucket capacity (allows bursts)
            window_seconds: Time window for cleanup (not used in algorithm)
        """
        self.rate = rate
        self.capacity = capacity
        self.window = timedelta(seconds=window_seconds)
        self.buckets: dict[str, dict[str, datetime | float]] = defaultdict(lambda: {
            'tokens': capacity,
            'last_update': datetime.now()
        })
        self.lock = threading.Lock()
    
    def _refill_bucket(self, identifier: str) -> None:
        """Refill tokens based on elapsed time."""
        bucket = self.buckets[identifier]
        now = datetime.now()
        last_update = bucket['last_update']
        if isinstance(last_update, datetime):
            elapsed = (now - last_update).total_seconds()
        else:
            elapsed = 0
        
        # Add tokens based on elapsed time
        new_tokens = elapsed * self.rate
        tokens = bucket['tokens']
        if isinstance(tokens, (int, float)):
            bucket['tokens'] = min(
                self.capacity,
                tokens + new_tokens
            )
        bucket['last_update'] = now
    
    def is_allowed(self, identifier: str, tokens: int = 1) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: User ID or IP address
            tokens: Number of tokens to consume (default 1)
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self.lock:
            self._refill_bucket(identifier)
            bucket = self.buckets[identifier]
            bucket_tokens = bucket['tokens']
            
            if not isinstance(bucket_tokens, (int, float)):
                return False
            
            if bucket_tokens >= tokens:
                bucket['tokens'] = bucket_tokens - tokens
                return True
            
            logger.warning(
                f"Rate limit exceeded for {identifier}. "
                f"Tokens available: {bucket_tokens:.2f}, needed: {tokens}"
            )
            return False
    
    def get_wait_time(self, identifier: str, tokens: int = 1) -> float:
        """
        Get time to wait before next request is allowed (seconds).
        
        Args:
            identifier: User ID or IP address
            tokens: Number of tokens needed
        
        Returns:
            Wait time in seconds (0 if request can proceed now)
        """
        with self.lock:
            self._refill_bucket(identifier)
            bucket = self.buckets[identifier]
            bucket_tokens = bucket['tokens']
            
            if not isinstance(bucket_tokens, (int, float)):
                return 0.0
            
            if bucket_tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - bucket_tokens
            return tokens_needed / self.rate
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        with self.lock:
            if identifier in self.buckets:
                del self.buckets[identifier]


# Global rate limiter instances for common use cases
api_limiter = TokenBucketRateLimiter(
    rate=10,      # 10 requests per second
    capacity=20   # Allow bursts up to 20
)

auth_limiter = TokenBucketRateLimiter(
    rate=0.083,   # ~5 requests per minute (1/12 per second)
    capacity=5    # Allow burst of 5
)

dashboard_limiter = TokenBucketRateLimiter(
    rate=100,     # 100 requests per second
    capacity=200  # Allow bursts up to 200
)


def rate_limit(
    limiter: RateLimiter | TokenBucketRateLimiter,
    tokens: int = 1,
    error_message: str = "Rate limit exceeded"
):
    """
    Decorator for rate limiting functions.
    
    Args:
        limiter: Rate limiter instance to use
        tokens: Number of tokens to consume (for TokenBucket only)
        error_message: Error message when rate limit exceeded
    
    Example:
        @rate_limit(api_limiter, tokens=1)
        def get_loan_details(loan_id: str, user_id: str):
            # ... fetch loan details ...
            pass
        
        @rate_limit(auth_limiter, error_message="Too many login attempts")
        def login(username: str, password: str, ip_address: str):
            # ... authenticate user ...
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifier from kwargs
            identifier = (
                kwargs.get('user_id') or 
                kwargs.get('ip_address') or 
                'anonymous'
            )
            
            # Check rate limit
            if isinstance(limiter, TokenBucketRateLimiter):
                allowed = limiter.is_allowed(identifier, tokens)
            else:
                allowed = limiter.is_allowed(identifier)
            
            if not allowed:
                # Get retry-after time if available
                if isinstance(limiter, TokenBucketRateLimiter):
                    wait_time = limiter.get_wait_time(identifier, tokens)
                    raise Exception(
                        f"{error_message}. Retry after {wait_time:.1f} seconds."
                    )
                raise Exception(error_message)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage functions
def example_api_endpoint(user_id: str, loan_id: str) -> dict[str, str]:
    """Example API endpoint with rate limiting."""
    @rate_limit(api_limiter, tokens=1)
    def _inner(user_id: str):
        return {"status": "success", "loan_id": loan_id}
    
    return _inner(user_id=user_id)


def example_login(username: str, password: str, ip_address: str) -> dict[str, str]:
    """Example login endpoint with strict rate limiting."""
    @rate_limit(auth_limiter, tokens=1, error_message="Too many login attempts")
    def _inner(ip_address: str):
        # ... authenticate user ...
        return {"status": "success", "token": "fake-token"}
    
    return _inner(ip_address=ip_address)
