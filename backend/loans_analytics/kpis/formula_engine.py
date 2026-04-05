"""Compatibility entrypoint for legacy formula engine imports.

Active formula execution has moved to backend.src.kpi_engine; this module is
kept so security tests and legacy import paths still resolve.
"""

from __future__ import annotations

from backend.loans_analytics.kpis.ssot_asset_quality import KPIFormulaEngine

__all__ = ["KPIFormulaEngine"]
