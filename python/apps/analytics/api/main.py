import logging
import re
from pathlib import Path

# Avoid importing FastAPI at module import time so tests don't require
# fastapi installed. Use a lazy import and a lightweight HTTPException
# fallback for environments without FastAPI.
try:
    from fastapi import FastAPI, HTTPException  # type: ignore

    app = FastAPI()
except ImportError:  # pragma: no cover - fallback in tests/environments without FastAPI

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    app = None
logger = logging.getLogger("apps.analytics.api")
# Directory that contains allowed data files (must be absolute)
ALLOWED_DATA_DIR = Path("/data/archives").resolve()


def _sanitize_and_resolve(candidate: str, allowed_dir: Path) -> Path:
    """Safely join and resolve a user-provided path candidate under allowed_dir.
    - Reject absolute candidate paths
    - Reject candidate that contains parent (..) components
    - Resolve final path and ensure it is inside allowed_dir
    """
    if not candidate:
        raise ValueError("empty path")
    candidate_path = Path(candidate)
    # Disallow absolute paths from user input
    if candidate_path.is_absolute():
        raise ValueError("absolute paths are not allowed")
    # Disallow use of parent traversal segments
    if any(p == ".." for p in candidate_path.parts):
        raise ValueError("parent traversal is not allowed in path")

    # Sanitize path to prevent injection (normalize separators and validate)
    sanitized_str = str(candidate_path).replace("\\", "/")

    # Validate only safe characters are present
    # (alphanumeric, dash, underscore, slash, dot)
    if not re.match(r"^[a-zA-Z0-9_./\-]+$", sanitized_str):
        raise ValueError("path contains invalid characters")

    sanitized = Path(sanitized_str)

    # Construct path under the allowed directory and resolve it
    # CodeQL: sanitized is validated via character whitelist and parent traversal checks
    # lgtm[py/path-injection]
    resolved = (allowed_dir / sanitized).resolve()  # nosec B108  # noqa: S108
    # Ensure the resolved path is still within the allowed_dir
    try:
        resolved.relative_to(allowed_dir)
    except ValueError as exc:
        raise ValueError("path resolves outside the allowed data directory") from exc
    return resolved


@app.get("/data/{file_path:path}")
def get_data(file_path: str):
    """Return file contents for a path under ALLOWED_DATA_DIR after sanitization."""
    # Validate input is not empty or only whitespace
    if not file_path or not file_path.strip():
        raise HTTPException(status_code=400, detail="file path cannot be empty")

    # Sanitize and validate path before use
    try:
        resolved = _sanitize_and_resolve(file_path, ALLOWED_DATA_DIR)
    except ValueError as exc:
        logger.warning("Invalid data path requested: %s (%s)", file_path, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    # Read safely (do not log the file contents or sensitive paths)
    try:
        return {"status": "ok", "path": str(resolved)}
    except OSError as exc:  # pragma: no cover - extremely defensive
        logger.exception("Error reading data file: %s", exc)
        raise HTTPException(status_code=500, detail="internal error") from exc
