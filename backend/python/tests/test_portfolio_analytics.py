"""Tests for portfolio analytics SSOT-backed KPI behavior."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from backend.python.kpis.portfolio_analytics import credit_line_category_kpis


def test_credit_line_category_kpis_uses_ssot_for_par_metrics() -> None:
    loans_df = pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3"],
            "categorialineacredito": ["A", "A", "B"],
            "outstanding_loan_value": [100.0, 300.0, 200.0],
            "days_past_due": [0, 60, 100],
            "disbursement_amount": [120.0, 320.0, 220.0],
            "interest_rate_apr": [0.2, 0.3, 0.4],
            "term": [90, 120, 150],
            "loan_status": ["active", "active", "defaulted"],
        }
    )

    with patch("backend.python.kpis.ssot_asset_quality.KPIFormulaEngine.calculate_kpi") as mock_calc:
        # 2 categories * (par30, par90) = 4 calls
        mock_calc.side_effect = [
            {"value": 12.3},
            {"value": 4.5},
            {"value": 67.8},
            {"value": 45.6},
        ]

        result = credit_line_category_kpis(loans_df)

    by_cat = {row["category"]: row for row in result["by_category"]}
    assert by_cat["A"]["par30_pct"] == 12.3
    assert by_cat["A"]["par90_pct"] == 4.5
    assert by_cat["B"]["par30_pct"] == 67.8
    assert by_cat["B"]["par90_pct"] == 45.6
    assert mock_calc.call_count == 4
