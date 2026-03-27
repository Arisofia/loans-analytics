"""Tests for individual mart builders."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.src.marts.portfolio_mart import build as build_portfolio
from backend.src.marts.finance_mart import build as build_finance
from backend.src.marts.sales_mart import build as build_sales
from backend.src.marts.marketing_mart import build as build_marketing
from backend.src.marts.collections_mart import build as build_collections
from backend.src.marts.treasury_mart import build as build_treasury
from backend.src.marts.build_all_marts import build_all_marts


@pytest.fixture()
def loan_df() -> pd.DataFrame:
    """Minimal loan-level dataframe with typical columns."""
    return pd.DataFrame(
        {
            "loan_id": ["L001", "L002", "L003"],
            "customer_id": ["C1", "C2", "C3"],
            "borrower_id": ["C1", "C2", "C3"],
            "amount": [10_000, 20_000, 30_000],
            "funded_amount": [10_000, 20_000, 30_000],
            "outstanding_principal": [9_000, 18_000, 25_000],
            "current_balance": [9_000, 18_000, 25_000],
            "interest_rate": [0.12, 0.15, 0.18],
            "apr": [0.12, 0.15, 0.18],
            "term_days": [360, 720, 1080],
            "status": ["active", "active", "defaulted"],
            "origination_date": ["2024-01-15", "2024-02-20", "2024-03-10"],
            "days_past_due": [0, 15, 95],
            "default_flag": [0, 0, 1],
            "country": ["SV", "SV", "SV"],
            "sector": ["gov", "edu", "gov"],
            "originator": ["O1", "O1", "O1"],
            "source_channel": ["web", "branch", "web"],
            "dpd": [0, 15, 95],
            "tpv": [10_000, 20_000, 30_000],
            "advisory_channel": ["web", "branch", "web"],
            "kam_hunter": ["KAM1", "KAM2", "KAM1"],
            "kam_farmer": ["KAM3", "KAM3", "KAM4"],
            "last_payment_amount": [900, 950, 1100],
            "total_payment_received": [4500, 9500, 8800],
            "capital_collected": [4000, 8500, 7500],
            "total_scheduled": [5400, 11400, 13200],
            "credit_line": ["A", "B", "A"],
        }
    )


class TestPortfolioMart:
    def test_build_returns_dataframe(self, loan_df: pd.DataFrame):
        result = build_portfolio(loan_df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(loan_df)


class TestFinanceMart:
    def test_build_returns_dataframe(self, loan_df: pd.DataFrame):
        result = build_finance(loan_df)
        assert isinstance(result, pd.DataFrame)


class TestSalesMart:
    def test_build_returns_dataframe(self, loan_df: pd.DataFrame):
        leads = pd.DataFrame(
            {
                "lead_id": ["S1", "S2"],
                "created_at": ["2024-01-01", "2024-02-01"],
                "owner": ["KAM1", "KAM2"],
                "stage": ["won", "lost"],
                "source_channel": ["web", "branch"],
                "sector": ["gov", "gov"],
                "country": ["SV", "SV"],
                "requested_ticket": [10000, 20000],
                "approved_ticket": [10000, 0],
                "funded_flag": [1, 0],
            }
        )
        result = build_sales(leads)
        assert isinstance(result, pd.DataFrame)


class TestMarketingMart:
    def test_build_returns_dataframe(self, loan_df: pd.DataFrame):
        result = build_marketing(loan_df)
        assert isinstance(result, pd.DataFrame)


class TestCollectionsMart:
    def test_build_returns_dataframe(self, loan_df: pd.DataFrame):
        result = build_collections(loan_df)
        assert isinstance(result, pd.DataFrame)


class TestTreasuryMart:
    def test_build_returns_dataframe(self, loan_df: pd.DataFrame):
        result = build_treasury(loan_df)
        assert isinstance(result, (pd.DataFrame, dict))


class TestBuildAllMarts:
    def test_returns_dict_with_keys(self, loan_df: pd.DataFrame):
        leads_df = pd.DataFrame(
            {
                "lead_id": ["S1", "S2"],
                "created_at": ["2024-01-01", "2024-02-01"],
                "owner": ["KAM1", "KAM2"],
                "stage": ["won", "lost"],
                "source_channel": ["web", "branch"],
                "sector": ["gov", "gov"],
                "country": ["SV", "SV"],
                "requested_ticket": [10000, 20000],
                "approved_ticket": [10000, 0],
                "funded_flag": [1, 0],
            }
        )
        bundle = {"loans": loan_df, "leads": leads_df}
        result = build_all_marts(bundle)
        assert isinstance(result, dict)
        expected_keys = {"portfolio_mart", "finance_mart", "sales_mart"}
        assert expected_keys.issubset(set(result.keys()))
