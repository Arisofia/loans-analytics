from __future__ import annotations
import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, Optional
logger = logging.getLogger(__name__)

class RateLimiter:

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        with self._lock:
            self.requests[identifier] = [req_time for req_time in self.requests[identifier] if req_time > cutoff_time]
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(current_time)
                return True
            return False

    def get_remaining(self, identifier: str) -> int:
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        with self._lock:
            self.requests[identifier] = [req_time for req_time in self.requests[identifier] if req_time > cutoff_time]
            return max(0, self.max_requests - len(self.requests[identifier]))

    def reset(self, identifier: Optional[str]=None) -> None:
        with self._lock:
            if identifier:
                self.requests.pop(identifier, None)
            else:
                self.requests.clear()

class TokenBucketRateLimiter:

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {'tokens': capacity, 'last_update': time.time()})
        self._lock = threading.Lock()

    def is_allowed(self, identifier: str, tokens: int=1) -> bool:
        current_time = time.time()
        with self._lock:
            bucket = self.buckets[identifier]
            time_elapsed = current_time - bucket['last_update']
            bucket['tokens'] = min(self.capacity, bucket['tokens'] + time_elapsed * self.rate)
            bucket['last_update'] = current_time
            if bucket['tokens'] >= tokens:
                bucket['tokens'] -= tokens
                return True
            return False

    def get_remaining(self, identifier: str) -> float:
        current_time = time.time()
        with self._lock:
            bucket = self.buckets[identifier]
            time_elapsed = current_time - bucket['last_update']
            return min(self.capacity, bucket['tokens'] + time_elapsed * self.rate)

    def reset(self, identifier: Optional[str]=None) -> None:
        with self._lock:
            if identifier:
                self.buckets.pop(identifier, None)
            else:
                self.buckets.clear()
api_limiter = RateLimiter(max_requests=100, window_seconds=10)
auth_limiter = RateLimiter(max_requests=5, window_seconds=60)
dashboard_limiter = TokenBucketRateLimiter(rate=100, capacity=1000)

def rate_limit(limiter: RateLimiter | TokenBucketRateLimiter, identifier_func: Optional[Callable[..., str]]=None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = kwargs.get('user_id') or kwargs.get('ip') or 'default'
            if not limiter.is_allowed(identifier):
                remaining = limiter.get_remaining(identifier)
                logger.warning('Rate limit exceeded for %s (remaining: %s)', identifier, remaining)
                raise RateLimitExceeded(f'Rate limit exceeded. Remaining: {remaining}')
            return func(*args, **kwargs)
        return wrapper
    return decorator

class RateLimitExceeded(Exception):
    pass
