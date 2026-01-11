import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd
import yaml

ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_placeholder(value: str, context: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if ":" in token:
            key, default = token.split(":", 1)
        else:
            key, default = token, ""
        return context.get(key, os.getenv(key, default))

    return ENV_PATTERN.sub(replace, value)


def resolve_placeholders(payload: Any, context: Optional[Dict[str, str]] = None) -> Any:
    if context is None:
        context = {}
    if isinstance(payload, dict):
        return {key: resolve_placeholders(value, context) for key, value in payload.items()}
    if isinstance(payload, list):
        return [resolve_placeholders(item, context) for item in payload]
    if isinstance(payload, str):
        return _resolve_placeholder(payload, context)
    return payload


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def hash_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_dataframe(df: pd.DataFrame) -> str:
    if df.empty:
        return hashlib.sha256(b"").hexdigest()
    sorted_df = df.copy()
    sorted_df = sorted_df.reindex(sorted(sorted_df.columns), axis=1)
    data_hash = pd.util.hash_pandas_object(sorted_df, index=True).values
    return hashlib.sha256(data_hash.tobytes()).hexdigest()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)


@dataclass
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
                    on_retry(attempt, exc)
                sleep_for = self.backoff_seconds * (2 ** (attempt - 1))
                if self.jitter_seconds:
                    sleep_for += self.jitter_seconds * (0.5 - os.urandom(1)[0] / 255)
                time.sleep(max(0.0, sleep_for))


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    reset_seconds: int = 60
    failures: int = 0
    opened_at: Optional[float] = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if (time.time() - self.opened_at) > self.reset_seconds:
            self.failures = 0
            self.opened_at = None
            return True
        return False

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.time()

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None


@dataclass
class RateLimiter:
    max_requests_per_minute: int = 60
    last_request_ts: Optional[float] = None

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
