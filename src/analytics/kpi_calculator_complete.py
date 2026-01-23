"""Compatibility shim for the historical `kpi_calculator_complete` module.

This module provides a lightweight, well-typed surface so tests that import
`src.analytics.kpi_calculator_complete` succeed.  It delegates to the
minimal implementations living in `src.analytics.run_pipeline` when possible.
"""
from __future__ import annotations

from typing import Any, Dict

from src.analytics.run_pipeline import calculate_kpis, create_metrics_csv  # re-export

__all__ = ["calculate_kpis", "create_metrics_csv"]


def compute_kpis(df) -> Dict[str, Any]:
    """Backward-compatible alias used by older callers/tests."""
    return calculate_kpis(df)