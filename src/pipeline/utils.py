import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml
import pandas as pd


class RateLimiter:
# ... (skipping to CircuitBreaker)
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
        self.recovery_timeout = (
            reset_seconds if reset_seconds is not None else recovery_timeout
        )

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

    def record_success(self) -> None:
        if self.state == "HALF-OPEN":
            self.state = "CLOSED"
            self.failures = 0
        elif self.state == "CLOSED":
            self.failures = 0

    def record_failure(self) -> None:
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
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_yaml(path: Path) -> Any:
    """Load YAML file."""
    with open(path, "r") as f:
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
