import time
from pathlib import Path

import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config.settings import settings

app = FastAPI(title="Abaco Analytics API v2.0")

# Redis-based Rate Limiting (Sliding Window)
try:
    r = redis.from_url(settings.redis_url)
except Exception:
    r = None


def is_rate_limited(client_ip: str, limit: int = 100, window: int = 60) -> bool:
    if not r:
        return False

    now = time.time()
    key = f"rate_limit:{client_ip}"

    # Remove old requests from window
    r.zremrangebyscore(key, 0, now - window)

    # Count requests in window
    count = r.zcard(key)

    if count >= limit:
        return True

    # Add current request
    r.zadd(key, {str(now): now})
    r.expire(key, window)
    return False


def _sanitize_and_resolve(path: str, base_dir: Path) -> Path:
    """
    Sanitize and resolve a path to prevent directory traversal.
    """
    # Ensure path is not absolute
    p = Path(path)
    if p.is_absolute():
        raise ValueError(f"Absolute paths not allowed: {path}")

    # Resolve full path
    resolved_base = base_dir.resolve()
    full_path = (resolved_base / p).resolve()

    # Check if it's still inside base_dir
    if not str(full_path).startswith(str(resolved_base)):
        raise ValueError(f"Path traversal detected: {path}")

    return full_path


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        return JSONResponse(status_code=429, content={"error": "Too Many Requests"})
    return await call_next(request)


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0"}


@app.get("/metrics/summary")
def get_metrics_summary():
    # Placeholder for actual metrics retrieval from Polars/DB
    return {"aum": 15200000.0, "npl": 0.035, "rotation": 4.6}
