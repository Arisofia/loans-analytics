"""Orchestrator subpackage — structured orchestration with dependency
graph, priority rules, and action routing.
"""

from __future__ import annotations

import importlib
import types
from pathlib import Path

from backend.python.multi_agent.orchestrator.decision_orchestrator import (  # noqa: F401
    DecisionOrchestrator,
)


def _load_legacy_orchestrator() -> types.ModuleType:
    """Load the legacy orchestrator.py file that is shadowed by this package."""
    legacy_path = Path(__file__).resolve().parent.parent / "orchestrator.py"
    spec = importlib.util.spec_from_file_location(
        "backend.python.multi_agent._legacy_orchestrator", str(legacy_path)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load legacy orchestrator from {legacy_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    _legacy = _load_legacy_orchestrator()
    MultiAgentOrchestrator = _legacy.MultiAgentOrchestrator  # noqa: F401
except Exception:  # noqa: BLE001 — graceful fallback if legacy file is missing
    pass