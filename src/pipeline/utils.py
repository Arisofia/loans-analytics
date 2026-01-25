import os
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, Union, Callable, TypeVar
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_seconds: int = 1
    jitter_seconds: float = 0.1

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes a function with retry logic."""
        # Extract on_retry so it isn't passed to the decorated function
        on_retry = kwargs.pop("on_retry", None)

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if on_retry:
                    on_retry(e)
                if attempt < self.max_retries:
                    sleep_time = self.backoff_seconds * (2 ** attempt)
                    import random
                    if self.jitter_seconds > 0:
                        sleep_time += random.uniform(0, self.jitter_seconds)
                    time.sleep(sleep_time)

        if last_exception:
            raise last_exception
        raise RuntimeError("Max retries exceeded without exception capture")


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self.failures = 0
        self.last_failure_time = 0

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

    def record_success(self):
        """Resets failure count on success."""
        self.failures = 0

    def is_open(self) -> bool:
        if self.failures < self.failure_threshold:
            return False
        if time.time() - self.last_failure_time > self.reset_seconds:
            self.failures = 0
            return False
        return True

    def allow(self) -> bool:
        """Alias for checking if requests are allowed (opposite of is_open)."""
        return not self.is_open()


class RateLimiter:
    def __init__(
        self, calls: int = 10, period: int = 60, max_requests_per_minute: int = 60, **kwargs
    ):
        self.calls = calls
        self.period = period
        self.max_requests_per_minute = max_requests_per_minute

    def wait(self):
        pass


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensures a directory exists and returns the Path object."""
    p = Path(path)
    os.makedirs(p, exist_ok=True)
    return p


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_file(filepath: Union[str, Path]) -> str:
    sha256_hash = hashlib.sha256()
    with open(str(filepath), "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def write_json(filepath: Union[str, Path], data: Any) -> None:
    with open(str(filepath), "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_yaml(filepath: Union[str, Path]) -> Dict[str, Any]:
    import yaml

    with open(str(filepath), "r") as f:
        return yaml.safe_load(f) or {}


def deep_merge(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merges source dict into destination dict."""
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination


def resolve_placeholders(config: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves ${VAR} placeholders in string values from environment variables."""

    def _resolve(obj):
        if isinstance(obj, dict):
            return {k: _resolve(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_resolve(i) for i in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj

    return _resolve(config)


def hash_dataframe(df: pd.DataFrame) -> str:
    """Returns a SHA256 hash of the dataframe content."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
