"""Tests for pipeline formula engine and ingestion data-source guardrails."""

import pandas as pd
import pytest

from src.pipeline.calculation import KPIFormulaEngine
from src.pipeline.ingestion import IngestionPhase


def test_comparison_formula_uses_latest_and_previous_month_balances():
    """Comparison formulas should evaluate against real month-over-month balances."""
    df = pd.DataFrame(
        {
            "measurement_date": ["2025-01-05", "2025-01-20", "2025-02-10", "2025-02-19"],
            "outstanding_balance": [100.0, 150.0, 200.0, 100.0],
        }
    )
    engine = KPIFormulaEngine(df)
    formula = "(current_month_balance - previous_month_balance) / previous_month_balance * 100"

    result = engine.calculate(formula)

    # Jan = 250, Feb = 300 -> growth = 20%
    assert result == pytest.approx(20.0)


def test_comparison_formula_returns_zero_when_previous_month_is_zero():
    """Division-by-zero in period comparisons should fail closed to 0.0."""
    df = pd.DataFrame(
        {
            "measurement_date": ["2025-02-01", "2025-02-15"],
            "outstanding_balance": [500.0, 500.0],
        }
    )
    engine = KPIFormulaEngine(df)
    formula = "(current_month_balance - previous_month_balance) / previous_month_balance * 100"

    result = engine.calculate(formula)

    assert result == 0.0


def test_comparison_formula_ignores_origination_dates_without_opt_in(monkeypatch):
    """Legacy origination-date fallback must stay disabled by default."""
    monkeypatch.delenv("KPI_ENGINE_ALLOW_ORIGINATION_FALLBACK", raising=False)
    df = pd.DataFrame(
        {
            "origination_date": ["2025-01-05", "2025-01-20", "2025-02-10", "2025-02-19"],
            "outstanding_balance": [100.0, 150.0, 200.0, 100.0],
        }
    )
    engine = KPIFormulaEngine(df)
    formula = "(current_month_balance - previous_month_balance) / previous_month_balance * 100"

    result = engine.calculate(formula)

    assert result == 0.0


def test_ingestion_without_input_fails_instead_of_using_dummy_data():
    """Ingestion must not fallback to sample/dummy rows when input is missing."""
    phase = IngestionPhase(config={})

    result = phase.execute(input_path=None, run_dir=None)

    assert result["status"] == "failed"
    assert "dummy/sample fallback is disabled" in result["error"]


def test_dpd_bucket_formulas_support_range_logic_via_aggregation_deltas():
    """DPD bucket formulas should support bounded ranges using aggregation arithmetic."""
    df = pd.DataFrame(
        {
            "dpd": [0, 15, 45, 95],
            "outstanding_balance": [100.0, 200.0, 300.0, 400.0],
        }
    )
    engine = KPIFormulaEngine(df)

    f_1_30 = (
        "(SUM(outstanding_balance WHERE dpd <= 30) - "
        "SUM(outstanding_balance WHERE dpd <= 0)) / "
        "SUM(outstanding_balance) * 100"
    )
    f_31_60 = (
        "(SUM(outstanding_balance WHERE dpd <= 60) - "
        "SUM(outstanding_balance WHERE dpd <= 30)) / "
        "SUM(outstanding_balance) * 100"
    )
    f_61_90 = (
        "(SUM(outstanding_balance WHERE dpd <= 90) - "
        "SUM(outstanding_balance WHERE dpd <= 60)) / "
        "SUM(outstanding_balance) * 100"
    )
    f_90_plus = "SUM(outstanding_balance WHERE dpd > 90) / SUM(outstanding_balance) * 100"

    assert engine.calculate(f_1_30) == pytest.approx(20.0)
    assert engine.calculate(f_31_60) == pytest.approx(30.0)
    assert engine.calculate(f_61_90) == pytest.approx(0.0)
    assert engine.calculate(f_90_plus) == pytest.approx(40.0)
