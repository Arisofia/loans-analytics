"""Targeted tests for SSOT integration in graph analytics KPIs."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from backend.python.kpis.graph_analytics import npl_benchmarks


def _intermedia_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "TotalSaldoVigente": [100.0, 200.0, 300.0],
            "FechaPagoProgramado": ["2025-01-01", "2025-12-01", "2026-02-01"],
        }
    )


def test_npl_benchmarks_uses_ssot_for_npl_90_and_npl_180() -> None:
    with patch(
        "backend.python.kpis.ssot_asset_quality.KPIFormulaEngine.calculate_kpi"
    ) as mock_calc:
        mock_calc.side_effect = [{"value": 12.34}, {"value": 6.78}]

        result = npl_benchmarks(_intermedia_df())

    assert result["status"] == "ok"
    assert result["npl_90_pct"] == 12.34
    assert result["npl_180_pct"] == 6.78
    assert mock_calc.call_count == 2


def test_npl_benchmarks_fallback_when_ssot_errors() -> None:
    with patch(
        "backend.python.kpis.ssot_asset_quality.KPIFormulaEngine.calculate_kpi",
        side_effect=RuntimeError("engine error"),
    ):
        result = npl_benchmarks(_intermedia_df())

    assert result["status"] == "ok"
    assert result["npl_90_pct"] >= 0.0
    assert result["npl_180_pct"] >= 0.0
