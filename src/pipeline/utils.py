# -*- coding: utf-8 -*-

import time
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable, Optional

__all__ = [
    "CircuitBreaker",
    "RateLimiter",
    "RetryPolicy",
    "hash_file",
    "utc_now",
]


class CircuitBreaker:
    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self._failures = 0
        self._last_failure_time = None

    def record_failure(self) -> None:
        """
        Record a failure event.

        Increment the failure count and update the last failure time.
        """
        self._failures += 1
        self._last_failure_time = time.time()

    def record_success(self) -> None:
        """
        Record a success event.

        Reset the failure count and last failure time.
        """
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
        self,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        jitter_seconds: float = 0.0,
    ):
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.jitter_seconds = jitter_seconds

    def execute(self, func: Callable, on_retry: Optional[Callable] = None):
        attempt = 0
        while True:
            try:
                return func()
            except (
                Exception
            ) as exc:  # noqa: E722  # Catching Exception is intentional for retry logic
                attempt += 1
                if attempt > self.max_retries:
                    raise
                if on_retry:
                    import contextlib

                    with contextlib.suppress(Exception):
                        on_retry(attempt, exc)
                time.sleep(self.backoff_seconds)


def hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
