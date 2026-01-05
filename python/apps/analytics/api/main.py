from pathlib import Path
import logging

# Avoid importing FastAPI at module import time so tests don't require fastapi installed.
# Use a lazy import and a lightweight HTTPException fallback for environments without FastAPI.
try:
    from fastapi import FastAPI, HTTPException  # type: ignore
    app = FastAPI()
except Exception:  # pragma: no cover - fallback in tests/environments without FastAPI
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

    # Construct path under the allowed directory and resolve it
    resolved = (allowed_dir / candidate_path).resolve()

    # Ensure the resolved path is still within the allowed_dir
    try:
        resolved.relative_to(allowed_dir)
    except Exception:
        raise ValueError("path resolves outside the allowed data directory")

    return resolved


@app.get("/data/{file_path:path}")
def get_data(file_path: str):
    """Return file contents for a path under ALLOWED_DATA_DIR after sanitization."""
    try:
        resolved = _sanitize_and_resolve(file_path, ALLOWED_DATA_DIR)
    except ValueError as exc:
        logger.warning("Invalid data path requested: %s (%s)", file_path, exc)
        raise HTTPException(status_code=400, detail=str(exc))

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    # Read safely (do not log the file contents or sensitive paths)
    try:
        return {"status": "ok", "path": str(resolved)}
    except Exception as exc:  # pragma: no cover - extremely defensive
        logger.exception("Error reading data file: %s", exc)
        raise HTTPException(status_code=500, detail="internal error")
