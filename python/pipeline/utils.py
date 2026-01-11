import hashlib
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
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests_per_minute = max_requests_per_minute
        # Simple no-op limiter for tests; implementations can add sleep logic

    def wait(self) -> None:
        return None


class RetryPolicy:
    def __init__(
        self, max_retries: int = 3, backoff_seconds: float = 1.0, jitter_seconds: float = 0.0
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
                time.sleep(self.backoff_seconds)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
