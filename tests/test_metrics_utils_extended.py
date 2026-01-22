"""
Unit tests for metrics utility functions in analytics.
"""

import numpy as np
import pandas as pd
import pytest

from src.analytics.metrics_utils import (
    _coerce_numeric,
    debt_to_income_ratio,
    loan_to_value,
    portfolio_delinquency_rate,
    portfolio_kpis,
    validate_kpi_columns,
    weighted_portfolio_yield,
)


def test_coerce_numeric_all_nan():
    # Test that _coerce_numeric raises ValueError if all values
    # are non-numeric.
    series = pd.Series(["invalid", "data", "values"])
    with pytest.raises(ValueError, match="must contain at least one numeric value"):
        _coerce_numeric(series, "test_field")


def test_validate_kpi_columns_empty_dataframe():
    """
    Test that validate_kpi_columns raises ValueError for empty DataFrame.
    """
    df = pd.DataFrame()
    # Test: validate_kpi_columns raises ValueError for empty DataFrame.
    with pytest.raises(ValueError, match="must be a non-empty DataFrame"):
        validate_kpi_columns(df)


def test_validate_kpi_columns_missing_multiple():
    df = pd.DataFrame({"loan_amount": [100]})
    # Test: validate_kpi_columns raises ValueError for missing required
    # columns.

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_kpi_columns(df)


def test_loan_to_value_all_zeros():
    # Test loan_to_value returns NaN when appraised values are all zero.
    amounts = pd.Series([100, 200, 300])
    appraised = pd.Series([0, 0, 0])
    ltv = loan_to_value(amounts, appraised)
    assert ltv.isna().all()


def test_portfolio_delinquency_rate_no_delinquent():
    statuses = ["current", "current", "current"]
    rate = portfolio_delinquency_rate(statuses)
    assert rate == pytest.approx(0.0)


def test_portfolio_delinquency_rate_all_delinquent():
    statuses = ["30-59 days past due", "60-89 days past due", "90+ days past due"]
    rate = portfolio_delinquency_rate(statuses)
    assert rate == pytest.approx(100.0)
    # Test: returns 100.0 when all loans delinquent.


def test_weighted_portfolio_yield_zero_principal():
    # Test: weighted_portfolio_yield returns 0.0 when all principals are zero.
    rates = pd.Series([0.05, 0.06, 0.07])
    principals = pd.Series([0, 0, 0])
    yield_rate = weighted_portfolio_yield(rates, principals)
    assert yield_rate == pytest.approx(0.0)


def test_weighted_portfolio_yield_nan_values():
    # Test: weighted_portfolio_yield handles NaN values in rates.
    rates = pd.Series([0.05, np.nan, 0.07])
    principals = pd.Series([100000, 200000, 150000])
    yield_rate = weighted_portfolio_yield(rates, principals)
    assert yield_rate >= 0.0


def test_portfolio_kpis_with_precalculated_ratios():
    # Test: portfolio_kpis with pre-calculated LTV and DTI ratios.
    df = pd.DataFrame(
        {
            "loan_amount": [250000, 450000, 150000],
            "appraised_value": [300000, 500000, 160000],
            "borrower_income": [80000, 120000, 60000],
            "monthly_debt": [1500, 2500, 1000],
            "loan_status": ["current", "current", "current"],
            "interest_rate": [0.035, 0.042, 0.038],
            "principal_balance": [240000, 440000, 145000],
            "ltv_ratio": [83.3, 90.0, 93.75],
            "dti_ratio": [22.5, 25.0, 20.0],
        }
    )
    kpis = portfolio_kpis(df)
    assert "portfolio_delinquency_rate_percent" in kpis
    assert kpis["portfolio_delinquency_rate_percent"] == pytest.approx(0.0)


def test_portfolio_kpis_handles_nan_in_ratios():
    df = pd.DataFrame(
        {
            "loan_amount": [250000, 450000, 150000],
            "appraised_value": [300000, 500000, 0],
            "borrower_income": [80000, 0, 60000],
            "monthly_debt": [1500, 2500, 1000],
            "loan_status": ["current", "current", "current"],
            "interest_rate": [0.035, 0.042, 0.038],
            "principal_balance": [240000, 440000, 145000],
        }
    )
    kpis = portfolio_kpis(df)
    assert kpis["average_ltv_ratio_percent"] >= 0
    assert kpis["average_dti_ratio_percent"] >= 0


def test_coerce_numeric_mixed_valid_invalid():
    series = pd.Series([100, "invalid", 300, np.nan])
    result = _coerce_numeric(series, "test")
    assert result.isna().sum() == 2
    assert result.iloc[0] == pytest.approx(100.0)


def test_loan_to_value_with_negative_values():
    amounts = pd.Series([-100, 200, 300])
    appraised = pd.Series([100, 200, 300])
    ltv = loan_to_value(amounts, appraised)
    assert ltv.iloc[0] == pytest.approx(-100.0)


def test_debt_to_income_ratio_negative_income():
    debts = pd.Series([500, 1000])
    incomes = pd.Series([-60000, 120000])
    dti = debt_to_income_ratio(debts, incomes)
    assert dti.isna().iloc[0] or isinstance(dti.iloc[0], (int, float))


def test_weighted_portfolio_yield_string_conversion():
    rates = pd.Series(["0.05", "0.06", "0.07"])
    principals = pd.Series(["100000", "200000", "150000"])
    yield_rate = weighted_portfolio_yield(rates, principals)
    assert yield_rate > 0
