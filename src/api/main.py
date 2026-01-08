from pathlib import Path
import logging

try:
    from fastapi import FastAPI, HTTPException
    app = FastAPI(title="Abaco Analytics API")
except ImportError:
    # Lightweight fallback for environments without FastAPI
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
    app = None

logger = logging.getLogger("abaco.api")

# Directory that contains allowed data files
ALLOWED_DATA_DIR = Path("/data/archives").resolve()

def _sanitize_and_resolve(candidate: str, allowed_dir: Path) -> Path:
    """Safely join and resolve a user-provided path candidate under allowed_dir."""
    if not candidate:
        raise ValueError("empty path")

    candidate_path = Path(candidate)

    if candidate_path.is_absolute():
        raise ValueError("absolute paths are not allowed")

    if any(p == ".." for p in candidate_path.parts):
        raise ValueError("parent traversal is not allowed in path")

    resolved = (allowed_dir / candidate_path).resolve()

    try:
        resolved.relative_to(allowed_dir)
    except (ValueError, RuntimeError):
        raise ValueError("path resolves outside the allowed data directory")

    return resolved

if app:
    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.get("/data/{file_path:path}")
    def get_data(file_path: str):
        """Return file metadata and path for a sanitized path under ALLOWED_DATA_DIR."""
        try:
            resolved = _sanitize_and_resolve(file_path, ALLOWED_DATA_DIR)
        except ValueError as exc:
            logger.warning("Invalid data path requested: %s (%s)", file_path, exc)
            raise HTTPException(status_code=400, detail=str(exc))

        if not resolved.exists() or not resolved.is_file():
            raise HTTPException(status_code=404, detail="file not found")

        return {
            "status": "ok",
            "path": str(resolved),
            "size": resolved.stat().st_size,
            "modified": resolved.stat().st_mtime
        }
