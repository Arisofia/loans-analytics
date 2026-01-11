import hashlib
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failures = 0
        self._last_failure_time: Optional[float] = None

    def allow(self) -> bool:
        if self._failures < self.failure_threshold:
            return True
        if self._last_failure_time is None:
            return False
        if time.time() - self._last_failure_time > self.reset_seconds:
            # reset
            self._failures = 0
            self._last_failure_time = None
            return True
        return False

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.time()

    def record_success(self) -> None:
        self._failures = 0
        self._last_failure_time = None


class RateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self, max_requests_per_minute: int = 60):
        self.rate = max_requests_per_minute / 60.0
        self.capacity = max_requests_per_minute
        self.tokens = self.capacity
        self.last_refill = time.time()

    def wait(self) -> None:
        """Wait until a token is available."""
        now = time.time()
        # Refill tokens
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens < 1.0:
            sleep_time = (1.0 - self.tokens) / self.rate
            time.sleep(sleep_time)
            self.tokens = 0.0
        else:
            self.tokens -= 1.0


class RetryPolicy:
    """Retry policy with exponential backoff and jitter."""

    def __init__(
        self, max_retries: int = 3, backoff_seconds: float = 1.0, jitter_seconds: float = 0.5
    ):
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.jitter_seconds = jitter_seconds

    def execute(self, func: Callable, on_retry: Optional[Callable] = None):
        attempt = 0
        while True:
            try:
                return func()
            except Exception as exc:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                
                if on_retry:
                    try:
                        on_retry(attempt, exc)
                    except Exception:
                        pass
                
                # Exponential backoff: base * 2^(attempt-1)
                sleep_time = self.backoff_seconds * (2 ** (attempt - 1))
                # Add jitter
                if self.jitter_seconds > 0:
                    sleep_time += random.uniform(0, self.jitter_seconds)
                
                time.sleep(sleep_time)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def select_column(columns: list[str], candidates: list[str]) -> Optional[str]:
    column_map = {col.lower(): col for col in columns}
    for candidate in candidates:
        key = candidate.lower()
        if key in column_map:
            return column_map[key]
    return None
