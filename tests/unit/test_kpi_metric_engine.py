"""Tests for the KPI metric engine (capital, covenants, engine)."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from backend.src.kpi_engine.capital import (
    debt_to_equity,
    leverage_ratio,
    return_on_equity,
    return_on_assets,
)
from backend.src.kpi_engine.covenants import (
    eligible_portfolio_ratio,
    capital_gap,
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


class TestMetricEngine:
    def test_run_metric_engine_with_dataframes(self):
        portfolio = pd.DataFrame(
            {
                "loan_id": ["L1", "L2", "L3"],
                "days_past_due": [0, 45, 100],  # L3 has NPL (dpd >= 90)
                "outstanding_principal": [100000, 200000, 150000],
                "default_flag": [0, 0, 0],
                "origination_date": ["2024-01-01", "2024-02-01", "2023-12-01"],
                "funded_amount": [100000, 200000, 150000],
                "sector": ["gov", "gov", "gov"],
                "country": ["SV", "SV", "SV"],
                "customer_id": ["C1", "C2", "C3"],
                "apr": [0.12, 0.15, 0.18],
                "term_days": [360, 720, 360],
                "dpd_bucket": ["current", "31_60", "90_plus"],
                "source_channel": ["web", "web", "web"],
                "originator": ["O1", "O1", "O1"],
                "cohort": ["2024-01", "2024-02", "2023-12"],
                "vintage": ["2024-01", "2024-02", "2023-12"],
            }
        )
        marts = {
            "portfolio_mart": portfolio,
            "finance_mart": pd.DataFrame(
                {
                    "interest_income": [1000],
                    "fee_income": [100],
                    "funding_cost": [200],
                    "debt_balance": [50000],
                    "gross_margin": [900],
                    "provision_expense": [75000],  # Provision for NPL
                }
            ),
            "sales_mart": pd.DataFrame(
                {
                    "lead_id": ["S1"],
                    "funded_flag": [1],
                    "requested_ticket": [150000],
                    "approved_ticket": [150000],
                }
            ),
        }
        result = run_metric_engine(marts)
        assert isinstance(result, dict)
