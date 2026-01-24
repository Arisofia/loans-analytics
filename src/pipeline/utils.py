import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests_per_minute = max_requests_per_minute
        self.last_request_ts: Optional[float] = None

    def wait(self) -> None:
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
    max_retries: int = 3
    backoff_seconds: float = 1.0
    jitter_seconds: float = 0.0

    def execute(
        self, func: Callable[[], Any], on_retry: Optional[Callable[[int, Exception], None]] = None
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
