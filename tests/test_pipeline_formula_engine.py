"""Tests for pipeline formula engine and ingestion data-source guardrails."""

import pandas as pd
import pytest

from backend.src.pipeline.calculation import KPIFormulaEngine
from backend.src.pipeline.ingestion import IngestionPhase


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


def test_where_clause_supports_or_conditions_for_npl_ratio_style_formulas():
    """OR predicates in WHERE clauses must not fail open to 100% numerator coverage."""
    df = pd.DataFrame(
        {
            "dpd": [10, 95, 0],
            "status": ["active", "delinquent", "defaulted"],
            "outstanding_balance": [100.0, 200.0, 300.0],
        }
    )
    engine = KPIFormulaEngine(df)
    formula = (
        "SUM(outstanding_balance WHERE dpd > 90 OR status = 'defaulted') "
        "/ SUM(outstanding_balance) * 100"
    )

    # Numerator = 200 (dpd>90) + 300 (defaulted), denominator = 600.
    assert float(engine.calculate(formula)) == pytest.approx(83.3333333333)


def test_where_clause_supports_and_conditions():
    """AND predicates should be evaluated as intersection of simple filters."""
    df = pd.DataFrame(
        {
            "dpd": [10, 95, 0],
            "status": ["active", "delinquent", "defaulted"],
            "outstanding_balance": [100.0, 200.0, 300.0],
        }
    )
    engine = KPIFormulaEngine(df)
    formula = (
        "SUM(outstanding_balance WHERE dpd > 30 AND status != 'defaulted') "
        "/ SUM(outstanding_balance) * 100"
    )

    # Only second row matches both predicates.
    assert float(engine.calculate(formula)) == pytest.approx(33.3333333333)

