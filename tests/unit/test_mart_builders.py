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




    def test_uses_real_financial_columns_when_present(self, loan_df: pd.DataFrame):
        loan_df = loan_df.copy()
        loan_df["interest_income"] = [100.0, 200.0, 300.0]
        loan_df["fee_income"] = [10.0, 20.0, 30.0]
        loan_df["funding_cost"] = [25.0, 25.0, 25.0]

        result = build_finance(loan_df)

        assert result["interest_income"].sum() == pytest.approx(600.0)
        assert result["fee_income"].sum() == pytest.approx(60.0)
        assert result["funding_cost"].sum() == pytest.approx(75.0)

    def test_missing_rate_and_interest_income_raises(self, loan_df: pd.DataFrame):
        loan_df = loan_df.drop(columns=["interest_rate", "apr"])

        with pytest.raises(ValueError, match="requires interest_rate"):
            build_finance(loan_df)

    @pytest.mark.parametrize(
        "interest_values, fee_values, funding_values",
        [
            (
                [100.0, 200.0, 300.0],
                [10.0, 20.0, 30.0],
                [25.0, 25.0, 25.0],
            )
        ],
    )
    def test_uses_usd_financial_columns_when_base_missing(
        self,
        loan_df: pd.DataFrame,
        interest_values,
        fee_values,
        funding_values,
    ):
        loan_df = loan_df.copy()

        # Ensure base-name columns are absent so *_usd is selected by _first_present
        loan_df = loan_df.drop(
            columns=[
                "interest_income",
                "fee_income",
                "funding_cost",
    def test_no_rate_does_not_use_placeholder_multipliers(self, loan_df: pd.DataFrame):
        loan_df = loan_df.copy()

        # Drop all rate-like columns and any pre-populated financial result columns
        loan_df = loan_df.drop(
            columns=[
                "interest_rate",
                "tasainteres",
                "apr",
                "origination_fee_rate",
                "fee_rate",
                "cost_of_funds_rate",
                "funding_rate",
                "interest_income",
                "fee_income",
                "funding_cost",
                "provision_expense",
            ],
            errors="ignore",
        )

        loan_df["interest_income_usd"] = interest_values
        loan_df["fee_income_usd"] = fee_values
        loan_df["funding_cost_usd"] = funding_values

        result = build_finance(loan_df)

        assert result["interest_income"].sum() == pytest.approx(sum(interest_values))
        assert result["fee_income"].sum() == pytest.approx(sum(fee_values))
        assert result["funding_cost"].sum() == pytest.approx(sum(funding_values))

    @pytest.mark.parametrize(
        "origination_fee, interest_expense, expected_loss",
        [
            (
                [5.0, 10.0, 15.0],
                [20.0, 20.0, 20.0],
                [1.0, 2.0, 3.0],
            )
        ],
    )
    def test_uses_alternate_financial_columns_when_present(
        self,
        loan_df: pd.DataFrame,
        origination_fee,
        interest_expense,
        expected_loss,
    ):
        loan_df = loan_df.copy()

        # Remove other alternative columns so _first_present selects the intended ones
        loan_df = loan_df.drop(
            columns=[
                "fee_income",
                "fee_income_usd",
                "funding_cost",
                "funding_cost_usd",
                "interest_income",
                "interest_income_usd",
                "expected_loss_usd",
            ],
            errors="ignore",
        )

        loan_df["origination_fee"] = origination_fee
        loan_df["interest_expense"] = interest_expense
        loan_df["expected_loss"] = expected_loss

        result = build_finance(loan_df)

        # origination_fee should map into aggregated fee_income
        assert result["fee_income"].sum() == pytest.approx(sum(origination_fee))
        # interest_expense should map into aggregated funding_cost
        assert result["funding_cost"].sum() == pytest.approx(sum(interest_expense))
        # expected_loss should flow through to expected_loss aggregate
        assert result["expected_loss"].sum() == pytest.approx(sum(expected_loss))
        # Ensure no defaults so provision should also be zero in the fallback path
        loan_df["default_flag"] = 0

        result = build_finance(loan_df)

        assert result["interest_income"].sum() == pytest.approx(0.0)
        assert result["fee_income"].sum() == pytest.approx(0.0)
        assert result["funding_cost"].sum() == pytest.approx(0.0)
        assert result["provision_expense"].sum() == pytest.approx(0.0)


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
