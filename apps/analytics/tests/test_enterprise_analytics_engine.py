"""
Unit tests for LoanAnalyticsEngine and analytics logic.
"""

import logging
import numpy as np
import pandas as pd

import pytest
from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine

  
@pytest.fixture
def portfolio_fixture():
    """Fixture for a sample loan portfolio DataFrame."""
    return pd.DataFrame({
        "loan_amount": [250000, 450000, 150000, 600000],
        "appraised_value": [300000, 500000, 160000, 0],
        "borrower_income": [80000, 120000, 60000, 0],
        "monthly_debt": [1500, 2500, 1000, 500],
        "loan_status": [
            "current",
            "30-59 days past due",
            "current",
            "90+ days past due"
        ],
        "interest_rate": [0.035, 0.042, 0.038, 0.045],
        "principal_balance": [240000, 440000, 145000, 590000],
    })


def test_initialization_requires_data():
    with pytest.raises(ValueError):
        LoanAnalyticsEngine(pd.DataFrame())


def test_validates_missing_columns():
    df = pd.DataFrame({"loan_amount": [100], "appraised_value": [120]})
    with pytest.raises(ValueError):
        LoanAnalyticsEngine(df)


def test_ltv_handles_zero_appraised_value(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    ltv = engine.compute_loan_to_value()
    assert np.isnan(ltv.iloc[-1]), (
        "Zero appraised value should not create inf or crash"
    )
    assert (ltv.dropna() > 0).all()


def test_dti_returns_series_with_index(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    dti = engine.compute_debt_to_income()
    assert isinstance(dti, pd.Series)
    assert list(dti.index) == list(portfolio_fixture.index)
    assert np.isnan(dti.iloc[-1])  # zero income


def test_risk_alerts_surface_high_risk_loans(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    alerts = engine.risk_alerts(ltv_threshold=80, dti_threshold=30)
    assert not alerts.empty
    assert {"ltv_ratio", "dti_ratio", "risk_score"}.issubset(alerts.columns)
    assert alerts["risk_score"].between(0, 1).all()


def test_run_full_analysis_includes_quality(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    summary = engine.run_full_analysis()
    expected_keys = {
        "portfolio_delinquency_rate_percent",
        "portfolio_yield_percent",
        "average_ltv_ratio_percent",
        "average_dti_ratio_percent",
        "data_quality_score",
        "average_null_ratio_percent",
        "invalid_numeric_ratio_percent",
    }
    assert expected_keys.issubset(summary.keys())
    
    # Regression assertions for KPI stability
    assert summary["portfolio_delinquency_rate_percent"] == 50.0
    assert abs(summary["portfolio_yield_percent"] - 4.165) < 0.001
    assert abs(summary["average_ltv_ratio_percent"] - 89.028) < 0.001
    assert summary["average_dti_ratio_percent"] == 22.5
    assert summary["data_quality_score"] <= 100


def test_coerces_invalid_numeric_values_and_reports_quality(portfolio_fixture):
    """Test coercion and quality reporting for invalid numeric values."""
    noisy_portfolio = portfolio_fixture.copy()
    noisy_portfolio["loan_amount"] = (
        noisy_portfolio["loan_amount"]
        .astype(object)
    )
    noisy_portfolio.loc[0, "loan_amount"] = "not-a-number"
    engine = LoanAnalyticsEngine(noisy_portfolio)
    quality = engine.data_quality_profile()
    ltv = engine.compute_loan_to_value()
    assert quality["invalid_numeric_ratio"] > 0
    assert np.isnan(ltv.iloc[0])


def test_source_dataframe_remains_unchanged_after_analysis(portfolio_fixture):
    original = portfolio_fixture.copy()
    engine = LoanAnalyticsEngine(portfolio_fixture)
    engine.run_full_analysis()
    pd.testing.assert_frame_equal(portfolio_fixture, original)


def test_compute_delinquency_rate(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    rate = engine.compute_delinquency_rate()
    assert rate == 50.0


def test_compute_portfolio_yield(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    yield_val = engine.compute_portfolio_yield()
    assert abs(yield_val - 4.165) < 0.001


def test_dti_excludes_nan_from_average(portfolio_fixture):
    engine = LoanAnalyticsEngine(portfolio_fixture)
    dti = engine.compute_debt_to_income()
    # 4 loans, 1 has zero income -> NaN. 3 valid.
    assert dti.notna().sum() == 3


def test_check_data_sanity_warns_on_high_interest_rate(portfolio_fixture, caplog):
    """Test that a warning is logged if interest rates appear to be percentages."""
    high_rate_portfolio = portfolio_fixture.copy()
    # Set a rate > 1.0 (e.g. 5.0%) to trigger warning
    high_rate_portfolio.loc[0, "interest_rate"] = 5.0
    
    with caplog.at_level(logging.WARNING):
        LoanAnalyticsEngine(high_rate_portfolio)
    
    assert "Max interest_rate is 5.0" in caplog.text
    assert "Ensure rates are ratios" in caplog.text
