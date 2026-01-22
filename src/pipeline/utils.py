def resolve_placeholders(config, context=None):
    """Stub for resolve_placeholders: returns config unchanged."""
    return config
def load_yaml(path):
    """Stub for load_yaml: load YAML from a file path."""
    import yaml
    with open(path, 'r') as f:
        return yaml.safe_load(f)
def ensure_dir(path):
    """Stub for ensure_dir: create directory if it does not exist."""
    import os
    os.makedirs(path, exist_ok=True)

def write_json(data, path):
    """Stub for write_json: write data as JSON to a file."""
    import json
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
def hash_dataframe(df):
    """Return a hash of a pandas DataFrame's values and columns."""
    import pandas as pd
    import hashlib
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    # Hash values and columns
    data_bytes = pd.util.hash_pandas_object(df, index=True).values.tobytes() + str(list(df.columns)).encode()
    return hashlib.sha256(data_bytes).hexdigest()

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

__all__ = [
    "CircuitBreaker",
    "RateLimiter",
    "RetryPolicy",
    "hash_file",
    "utc_now",
]
