"""Rate limiting middleware for production API protection.

Provides two implementations:
1. RateLimiter: Simple sliding window rate limiter
2. TokenBucketRateLimiter: Token bucket algorithm for burst handling

Usage:
    from python.middleware import api_limiter, rate_limit

    @rate_limit(api_limiter)
    def my_api_endpoint():
        return {"data": "response"}
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple sliding window rate limiter.

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds

    Example:
        >>> limiter = RateLimiter(max_requests=10, window_seconds=60)
        >>> limiter.is_allowed("user_123")
        True
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        """Check if request from identifier is allowed.

        Args:
            identifier: Unique identifier (user_id, IP, etc.)

        Returns:
            True if request is within rate limit, False otherwise
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        with self._lock:
            # Remove expired requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] if req_time > cutoff_time
            ]

            # Check if under limit
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(current_time)
                return True

            return False

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining requests in current window
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        with self._lock:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] if req_time > cutoff_time
            ]
            return max(0, self.max_requests - len(self.requests[identifier]))

    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset rate limit for identifier or all.

        Args:
            identifier: Specific identifier to reset, or None for all
        """
        with self._lock:
            if identifier:
                self.requests.pop(identifier, None)
            else:
                self.requests.clear()


class TokenBucketRateLimiter:
    """Token bucket rate limiter for handling burst traffic.

    Args:
        rate: Tokens added per second
        capacity: Maximum bucket capacity

    Example:
        >>> limiter = TokenBucketRateLimiter(rate=10, capacity=100)
        >>> limiter.is_allowed("user_123")
        True
    """

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.buckets: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"tokens": capacity, "last_update": time.time()}
        )
        self._lock = threading.Lock()

    def is_allowed(self, identifier: str, tokens: int = 1) -> bool:
        """Check if request is allowed under token bucket.

        Args:
            identifier: Unique identifier
            tokens: Number of tokens required (default: 1)

        Returns:
            True if sufficient tokens available, False otherwise
        """
        current_time = time.time()

        with self._lock:
            bucket = self.buckets[identifier]

            # Add tokens based on time elapsed
            time_elapsed = current_time - bucket["last_update"]
            bucket["tokens"] = min(
                self.capacity, bucket["tokens"] + time_elapsed * self.rate
            )
            bucket["last_update"] = current_time

            # Check if sufficient tokens
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return True

            return False

    def get_remaining(self, identifier: str) -> float:
        """Get remaining tokens for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Number of tokens available
        """
        current_time = time.time()

        with self._lock:
            bucket = self.buckets[identifier]
            time_elapsed = current_time - bucket["last_update"]
            tokens = min(self.capacity, bucket["tokens"] + time_elapsed * self.rate)
            return tokens

    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset bucket for identifier or all.

        Args:
            identifier: Specific identifier to reset, or None for all
        """
        with self._lock:
            if identifier:
                self.buckets.pop(identifier, None)
            else:
                self.buckets.clear()


# Global rate limiters for different use cases
api_limiter = RateLimiter(max_requests=100, window_seconds=10)  # 10 req/sec
auth_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5 req/min (auth)
dashboard_limiter = TokenBucketRateLimiter(rate=100, capacity=1000)  # Burst-friendly


def rate_limit(
    limiter: RateLimiter | TokenBucketRateLimiter,
    identifier_func: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to apply rate limiting to a function.

    Args:
        limiter: RateLimiter or TokenBucketRateLimiter instance
        identifier_func: Function to extract identifier from args/kwargs
                        (default: uses "user_id" or "ip" from kwargs)

    Returns:
        Decorated function with rate limiting

    Example:
        @rate_limit(api_limiter)
        def my_endpoint(user_id: str):
            return {"data": "response"}

        @rate_limit(auth_limiter, lambda *args, **kwargs: kwargs.get("email"))
        def login(email: str, password: str):
            return {"token": "..."}
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = kwargs.get("user_id") or kwargs.get("ip") or "default"

            # Check rate limit
            if not limiter.is_allowed(identifier):
                remaining = limiter.get_remaining(identifier)
                logger.warning(
                    "Rate limit exceeded for %s (remaining: %s)",
                    identifier,
                    remaining,
                )
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Remaining: {remaining}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
