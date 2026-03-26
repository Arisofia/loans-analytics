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
            "monto_desembolsado": [10_000, 20_000, 30_000],
            "saldo_actual": [9_000, 18_000, 25_000],
            "tasa_interes": [0.12, 0.15, 0.18],
            "plazo_meses": [12, 24, 36],
            "estado": ["active", "active", "defaulted"],
            "fecha_desembolso": ["2024-01-15", "2024-02-20", "2024-03-10"],
            "kam_hunter": ["KAM1", "KAM2", "KAM1"],
            "kam_farmer": ["KAM3", "KAM3", "KAM4"],
            "canal_origen": ["web", "branch", "web"],
            "dias_mora": [0, 15, 95],
            "cuota_mensual": [900, 950, 1100],
            "pagos_realizados": [5, 10, 8],
            "pagos_esperados": [5, 12, 12],
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
        result = build_sales(loan_df)
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
        result = build_all_marts(loan_df)
        assert isinstance(result, dict)
        expected_keys = {"portfolio", "finance", "sales", "marketing", "collections", "treasury"}
        assert expected_keys.issubset(set(result.keys()))
