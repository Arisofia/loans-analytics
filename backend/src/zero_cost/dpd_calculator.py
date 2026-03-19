"""Backward-compatible shim for DPDCalculator.

The canonical implementation lives in backend.python.kpis.dpd_calculator.
This module is kept to preserve existing imports from backend.src.zero_cost.
"""

from backend.python.kpis.dpd_calculator import DPDCalculator

__all__ = ["DPDCalculator"]
