import time
import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class CircuitBreaker:
    """
    A simple circuit breaker implementation to prevent cascading failures.

    Args:
        failure_threshold (int): Number of failures allowed before opening the circuit.
        reset_seconds (int): Seconds to wait before attempting to close the circuit.
    """

    def __init__(self, failure_threshold: int = 3, reset_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self.failures = 0
        self.last_failure_time = 0

    def record_failure(self):
        """Increments the failure count and updates the timestamp."""
        self.failures += 1
        self.last_failure_time = time.time()

    def is_open(self) -> bool:
        """
        Checks if the circuit is currently open (blocking requests).

        Returns:
            bool: True if the circuit is open, False otherwise.
        """
        if self.failures < self.failure_threshold:
            return False

        # If enough time has passed, tentatively close the circuit (reset failures)
        if time.time() - self.last_failure_time > self.reset_seconds:
            self.failures = 0
            return False

        return True


# --- Other existing utilities likely needed in this file ---


def utc_now() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def hash_file(filepath: str) -> str:
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def ensure_dir(path: str) -> None:
    """Ensures a directory exists."""
    os.makedirs(path, exist_ok=True)


def write_json(filepath: str, data: Any) -> None:
    """Writes data to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml
import pandas as pd


class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests_per_minute = max_requests_per_minute
        self.last_request_ts: Optional[float] = None

    def wait() -> None:
        if self.max_requests_per_minute <= 0:
            return
        interval = 60.0 / float(self.max_requests_per_minute)
        now = time.time()
        if self.last_request_ts is None:
            self.last_request_ts = now
            return
        elapsed = now - self.last_request_ts
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self.last_request_ts = time.time()


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

    def execute(
        self,
        func: Callable[[], Any],
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ) -> Any:
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


class CircuitBreakerError(Exception):
    """Raised when the circuit breaker is open."""

    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        reset_seconds: Optional[float] = None,
    ):
        self.failure_threshold = failure_threshold
        # Use reset_seconds if provided (legacy support), otherwise recovery_timeout
        self.recovery_timeout = reset_seconds if reset_seconds is not None else recovery_timeout

        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def allow(self) -> bool:
        if self.state == "OPEN":
            if (
                self.last_failure_time
                and (time.time() - self.last_failure_time) > self.recovery_timeout
            ):
                self.state = "HALF-OPEN"
                return True
            return False
        return True

    def record_success() -> None:
        if self.state == "HALF-OPEN":
            self.state = "CLOSED"
            self.failures = 0
        elif self.state == "CLOSED":
            self.failures = 0

    def record_failure() -> None:
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def call(self, func: Callable[[], Any]) -> Any:
        if not self.allow():
            raise CircuitBreakerError("CircuitBreaker is OPEN")
        try:
            result = func()
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise


def deep_merge(base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge override_dict into base_dict, with override taking precedence."""
    result = base_dict.copy()
    for key, value in override_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return it."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> None:
    """Write data to JSON file."""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_yaml(path: Path) -> Any:
    """Load YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_placeholders(data: Any, context: Dict[str, Any]) -> Any:
    """Recursively resolve placeholders in strings using context."""
    if isinstance(data, dict):
        return {k: resolve_placeholders(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_placeholders(i, context) for i in data]
    elif isinstance(data, str):
        try:
            return data.format(**context)
        except (KeyError, ValueError, IndexError):
            return data
    return data


def hash_dataframe(df: pd.DataFrame) -> str:
    """Compute a hash for a DataFrame."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
