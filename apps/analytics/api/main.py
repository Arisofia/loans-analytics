import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
import os
import subprocess

logger = logging.getLogger(__name__)


def _find_repo_root(start: Path | None | Callable[[], Path] = None) -> Path:
    """Find the repository root by looking for common marker files.

    Walks up from the start path and looks for `pyproject.toml`, `.git`, or
    `README.md`. Falls back to a conservative parent if nothing is found.

    The function handles `start` being either a `Path`, `None`, or a callable
    that returns a `Path`. We coerce the result to `Path` and resolve it to
    avoid type-checker issues when using the `/` operator on union types.
    """
    # If a callable was provided (e.g., a thunk that returns a Path), call it.
    if callable(start):
        start_value = start()
    else:
        start_value = start

    # Ensure `start_value` is a Path instance and resolved before use.
    start_path = (
        Path(start_value).resolve() if start_value is not None else Path(__file__).resolve()
    )
    p = start_path

    for _ in range(12):
        if (p / "pyproject.toml").exists() or (p / ".git").exists() or (p / "README.md").exists():
            return p
        parent = p.parent
        if parent == p:
            break
        p = parent
    # Fallback to previous heuristic (legacy behavior)
    # Converting .parents to a tuple avoids certain type-checker issues where
    # `.parents` can be treated as a non-subscriptable callable/type.
    return tuple(Path(__file__).resolve().parents)[3]


# Ensure repository root is on sys.path for local/script runs (idempotent)
repo_root = _find_repo_root()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi import BackgroundTasks, FastAPI, HTTPException  # noqa: E402

app = FastAPI(title="ABACO Analytics API")

ARTIFACTS_DIR = Path("logs/runs")


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/kpis/latest")
def get_latest_kpis():
    """Fetch the latest KPI results from the most recent run manifest."""
    if not ARTIFACTS_DIR.exists():
        raise HTTPException(status_code=404, detail="No run artifacts found")

    # Find the latest manifest
    manifests = sorted(
        ARTIFACTS_DIR.glob("*/**/*_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not manifests:
        raise HTTPException(status_code=404, detail="No manifests found")

    latest_manifest_path = manifests[0]
    try:
        with latest_manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        if not isinstance(manifest, dict):
            logger.error(
                "Manifest at %s is not an object (type=%s)",
                latest_manifest_path,
                type(manifest).__name__,
            )
            raise HTTPException(status_code=500, detail="Malformed manifest file")
        return {
            "run_id": manifest.get("run_id"),
            "generated_at": manifest.get("generated_at"),
            "metrics": manifest.get("metrics"),
            "quality_checks": manifest.get("quality_checks"),
        }
    except Exception as e:
        # Re-raise with chaining so the original exception is preserved
        raise HTTPException(status_code=500, detail=f"Error reading manifest: {str(e)}") from e


@app.post("/api/pipeline/trigger")
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    input_file: str = "data/archives/abaco_portfolio_calculations.csv",
):
    """Trigger the Prefect pipeline flow as a background task.

    Execution strategy is configurable via `PIPELINE_EXECUTION_MODE` env var:
      - "inline": import and run the flow object in the web process (not
        recommended for production; useful for local debugging).
      - "subprocess": spawn a separate Python process that runs the flow as a
        detached child (recommended; avoids initializing Prefect in the web
        server process).

    The subprocess approach avoids heavy Prefect/server initialization in the
    API process which can cause runtime import/init issues and block request
    handling. Input file paths are validated to be under `data/archives/` to
    prevent path traversal and unauthorized file access.
    """
    logger = logging.getLogger(__name__)

    # Validate input_file to avoid path traversal and ensure files are under data/archives
    ALLOWED_DATA_DIR = (repo_root / "data" / "archives").resolve()

    def _validate_input_file(path_str: str) -> Path:
        candidate = Path(path_str)
        # disallow absolute paths
        if candidate.is_absolute():
            raise HTTPException(status_code=400, detail="Absolute paths are not allowed")
        resolved = (repo_root / candidate).resolve()
        try:
            resolved.relative_to(ALLOWED_DATA_DIR)
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid input file; must be under data/archives/"
            )
        return resolved

    # perform validation; will raise HTTPException on invalid input
    validated_input_path = _validate_input_file(input_file)

    mode = os.getenv("PIPELINE_EXECUTION_MODE", "subprocess")

    if mode == "inline":
        # Local/debug mode: run the flow object directly (keeps previous behavior)
        from src.pipeline.prefect_orchestrator import abaco_pipeline_flow

        # Run in background via FastAPI BackgroundTasks; exceptions will propagate
        # to the background runner but won't block request handling.
        background_tasks.add_task(abaco_pipeline_flow, input_file=str(validated_input_path))
        logger.info("Triggered pipeline inline for input: %s", validated_input_path)
        return {"message": "Pipeline triggered (inline)", "input_file": str(validated_input_path)}

    # Default: spawn a detached subprocess to run the flow so the web process is
    # not affected by Prefect initialization, long-running tasks, or heavy deps.
    try:
        python = sys.executable or "python"
        # Build a small python one-liner that reads the input_file from argv[1].
        # Passing the input as an argv value avoids producing Python source with
        # embedded quotes that can break for inputs with special characters.
        script = (
            "import sys; "
            "from src.pipeline.prefect_orchestrator import abaco_pipeline_flow; "
            "abaco_pipeline_flow(input_file=sys.argv[1])"
        )

        # Ensure log dir exists and run subprocess with output redirected so
        # failures are recorded for later investigation.
        log_path = Path("logs/pipeline_subprocess.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            log_file = log_path.open("a")
        except Exception:
            log_file = subprocess.DEVNULL

        # Start a detached process without shell=True for safety and pass args
        # directly to avoid shell interpretation issues. Use start_new_session to
        # properly detach on Unix-like systems.
        subprocess.Popen(
            [python, "-c", script, str(validated_input_path)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
        logger.info(
            "Spawned pipeline subprocess for input: %s (logs: %s)", validated_input_path, log_path
        )
        return {
            "message": "Pipeline triggered (subprocess)",
            "input_file": str(validated_input_path),
        }
    except Exception as e:
        logger.exception("Failed to trigger pipeline: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start pipeline") from e


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
