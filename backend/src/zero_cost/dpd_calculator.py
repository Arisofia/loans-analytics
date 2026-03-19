"""Backward-compatible shim for DPDCalculator.

The canonical implementation lives in backend.python.kpis.dpd_calculator.
This module preserves legacy imports from backend.src.zero_cost.dpd_calculator.
"""

from backend.python.kpis.dpd_calculator import DPDCalculator

__all__ = ["DPDCalculator"]