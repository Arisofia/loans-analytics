"""Tests for the KPI metric engine (capital, covenants, engine)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from backend.src.kpi_engine.capital import (
    debt_to_equity,
    leverage_ratio,
    return_on_equity,
    return_on_assets,
)
from backend.src.kpi_engine.covenants import (
    eligible_portfolio_ratio,
    aging_compliance,
    capital_gap,
    check_all_covenants,
)
from backend.src.kpi_engine.engine import run_metric_engine


class TestCapitalMetrics:
    def test_debt_to_equity(self):
        result = debt_to_equity(Decimal("500000"), Decimal("200000"))
        assert result == Decimal("500000") / Decimal("200000")

    def test_debt_to_equity_zero_equity(self):
        result = debt_to_equity(Decimal("500000"), Decimal("0"))
        assert result == Decimal("Inf") or result > Decimal("1e9")

    def test_leverage_ratio(self):
        result = leverage_ratio(Decimal("700000"), Decimal("200000"))
        assert result == Decimal("700000") / Decimal("200000")

    def test_return_on_equity(self):
        result = return_on_equity(Decimal("50000"), Decimal("200000"))
        assert result == Decimal("50000") / Decimal("200000")

    def test_return_on_assets(self):
        result = return_on_assets(Decimal("50000"), Decimal("1000000"))
        assert result == Decimal("50000") / Decimal("1000000")


class TestCovenants:
    def test_eligible_portfolio_ratio(self):
        result = eligible_portfolio_ratio(Decimal("800000"), Decimal("1000000"))
        assert result == Decimal("0.8") or abs(float(result) - 0.8) < 1e-6

    def test_capital_gap(self):
        result = capital_gap(
            equity=Decimal("150000"),
            total_assets=Decimal("2000000"),
            target_ratio=Decimal("0.08"),
        )
        # gap = target - actual = 0.08 * 2M - 150K = 160K - 150K = 10K
        assert float(result) == pytest.approx(10000.0, abs=1)

    def test_check_all_covenants(self):
        result = check_all_covenants(
            eligible=Decimal("800000"),
            total=Decimal("1000000"),
            past_due_90=Decimal("50000"),
            equity=Decimal("200000"),
            total_assets=Decimal("2000000"),
        )
        assert isinstance(result, dict)


class TestMetricEngine:
    def test_run_metric_engine_with_dict_marts(self):
        marts = {
            "portfolio": {"total_outstanding": 1_000_000, "count": 100},
            "finance": {"net_income": 50_000, "total_assets": 1_200_000},
            "collections": {"past_due_90": 30_000},
        }
        result = run_metric_engine(
            marts, equity=200_000, lgd=0.10, min_collection_rate=0.985
        )
        assert isinstance(result, dict)
