"""Loaders for decision-intelligence state files.

Pages call these helpers to read the latest pipeline run artefacts
from the ``logs/runs/<run_id>/decision/`` directory tree.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_RUNS_DIR = Path("logs/runs")


def _latest_run_dir() -> Optional[Path]:
    """Return the most recent run directory, or *None*."""
    if not _RUNS_DIR.exists():
        return None
    dirs = [d for d in _RUNS_DIR.iterdir() if d.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.stat().st_mtime)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return None


# ── public loaders ──────────────────────────────────────────────────────

def load_decision_state() -> Optional[Dict[str, Any]]:
    """Load the latest ``decision_center_state.json``."""
    run_dir = _latest_run_dir()
    if run_dir is None:
        return None
    return _load_json(run_dir / "decision" / "decision_center_state.json")


def load_data_quality() -> Optional[Dict[str, Any]]:
    """Load the latest ``data_quality.json``."""
    run_dir = _latest_run_dir()
    if run_dir is None:
        return None
    return _load_json(run_dir / "decision" / "data_quality.json")


def load_scenario_results() -> Optional[Dict[str, Any]]:
    """Load the latest ``scenarios.json``."""
    run_dir = _latest_run_dir()
    if run_dir is None:
        return None
    return _load_json(run_dir / "decision" / "scenarios.json")


def load_metrics() -> Optional[Dict[str, Any]]:
    """Load the latest ``metrics.json``."""
    run_dir = _latest_run_dir()
    if run_dir is None:
        return None
    return _load_json(run_dir / "decision" / "metrics.json")


def load_run_manifest() -> Optional[Dict[str, Any]]:
    """Load the pipeline ``manifest.json``."""
    run_dir = _latest_run_dir()
    if run_dir is None:
        return None
    return _load_json(run_dir / "manifest.json")


def load_pipeline_results() -> Optional[Dict[str, Any]]:
    """Load the latest ``pipeline_results.json`` (full run manifest).

    The file is written by :class:`~backend.src.pipeline.orchestrator.UnifiedPipeline`
    to the run root directory (``logs/runs/<run_id>/pipeline_results.json``),
    *not* inside the ``decision/`` sub-directory used by the other loaders.
    It contains top-level pipeline metadata (run_id, start_time, status,
    duration_seconds) as well as per-phase results including the ingestion
    provenance fields (``ingestion_source``, ``data_as_of_date``,
    ``data_as_of_column``).
    """
    run_dir = _latest_run_dir()
    if run_dir is None:
        return None
    return _load_json(run_dir / "pipeline_results.json")
