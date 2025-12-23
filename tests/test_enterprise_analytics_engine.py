import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.enterprise_analytics_engine import (
    LoanAnalyticsEngine,
    LoanAnalyticsConfig,
    LoanPosition,
    PortfolioKPIs,
    calculate_monthly_payment,
    calculate_portfolio_kpis,
    expected_loss,
    portfolio_interest_and_risk,
)


def test_monthly_payment_matches_finance_formula():
    loan = LoanPosition(principal=100_000, annual_interest_rate=0.12, term_months=36)
    payment = calculate_monthly_payment(loan)

    monthly_rate = loan.annual_interest_rate / 12
    expected_payment = (monthly_rate * loan.principal) / (1 - math.pow(1 + monthly_rate, -loan.term_months))

    assert payment == pytest.approx(expected_payment, rel=1e-8)


def test_portfolio_interest_and_risk_tracks_defaults():
    prime = LoanPosition(principal=50_000, annual_interest_rate=0.08, term_months=24, default_probability=0.01)
    near_prime = LoanPosition(principal=75_000, annual_interest_rate=0.14, term_months=36, default_probability=0.05)
    subprime = LoanPosition(principal=40_000, annual_interest_rate=0.2, term_months=18, default_probability=0.12)

    monthly_interest, portfolio_loss = portfolio_interest_and_risk(
        loans=[prime, near_prime, subprime], loss_given_default=0.45
    )

    expected_interest = (
        prime.principal * (prime.annual_interest_rate / 12)
        + near_prime.principal * (near_prime.annual_interest_rate / 12)
        + subprime.principal * (subprime.annual_interest_rate / 12)
    )

    assert monthly_interest == pytest.approx(expected_interest)
    assert portfolio_loss == pytest.approx(
        expected_loss(prime, 0.45) + expected_loss(near_prime, 0.45) + expected_loss(subprime, 0.45)
    )


def test_invalid_inputs_raise_value_errors():
    with pytest.raises(ValueError):
        LoanPosition(principal=0, annual_interest_rate=0.05, term_months=12)

    with pytest.raises(ValueError):
        LoanPosition(principal=10_000, annual_interest_rate=-0.01, term_months=12)

    with pytest.raises(ValueError):
        LoanPosition(principal=10_000, annual_interest_rate=0.05, term_months=0)

    with pytest.raises(ValueError):
        LoanPosition(principal=10_000, annual_interest_rate=0.05, term_months=12, default_probability=1.5)

    valid_loan = LoanPosition(principal=10_000, annual_interest_rate=0.05, term_months=12)
    with pytest.raises(ValueError):
        expected_loss(valid_loan, loss_given_default=1.2)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3", "L4"],
            "principal": [100000, 50000, 75000, 60000],
            "interest_rate": [0.12, 0.08, 0.10, 0.09],
            "term_months": [24, 18, 24, 12],
            "origination_date": [
                "2023-01-15",
                "2023-02-10",
                "2022-12-05",
                "2023-04-20",
            ],
            "status": ["current", "30dpd", "defaulted", "current"],
            "outstanding_principal": [80000, 30000, 0, 40000],
            "days_in_arrears": [0, 35, 120, 0],
            "charge_off_amount": [0, 0, 50000, 0],
            "recoveries": [0, 0, 10000, 0],
            "paid_principal": [12000, 8000, 5000, 10000],
            "region": ["LATAM", "LATAM", "EMEA", "LATAM"],
            "product": ["SME", "SME", "Corporate", "SME"],
        }
    )


def test_portfolio_kpis_surfaces_weighted_metrics():
    loans = [
        LoanPosition(principal=100_000, annual_interest_rate=0.09, term_months=24, default_probability=0.02),
        LoanPosition(principal=50_000, annual_interest_rate=0.12, term_months=36, default_probability=0.04),
    ]

    kpis = calculate_portfolio_kpis(loans, loss_given_default=0.4)

    expected_exposure = sum(loan.principal for loan in loans)
    weighted_rate = (
        loans[0].annual_interest_rate * loans[0].principal + loans[1].annual_interest_rate * loans[1].principal
    ) / expected_exposure
    weighted_term = (
        loans[0].term_months * loans[0].principal + loans[1].term_months * loans[1].principal
    ) / expected_exposure
    weighted_default_probability = (
        loans[0].default_probability * loans[0].principal
        + loans[1].default_probability * loans[1].principal
    ) / expected_exposure
    expected_interest = sum(loan.principal * (loan.annual_interest_rate / 12) for loan in loans)
    expected_loss_value = sum(expected_loss(loan, 0.4) for loan in loans)

    assert isinstance(kpis, PortfolioKPIs)
    assert kpis.exposure == expected_exposure
    assert kpis.weighted_rate == pytest.approx(weighted_rate)
    assert kpis.weighted_term_months == pytest.approx(weighted_term)
    assert kpis.weighted_default_probability == pytest.approx(weighted_default_probability)
    assert kpis.expected_monthly_interest == pytest.approx(expected_interest)
    assert kpis.expected_monthly_payment == pytest.approx(
        calculate_monthly_payment(loans[0]) + calculate_monthly_payment(loans[1])
    )
    assert kpis.expected_loss == pytest.approx(expected_loss_value)
    assert kpis.expected_loss_rate == pytest.approx(expected_loss_value / expected_exposure)
    assert kpis.interest_yield_rate == pytest.approx(expected_interest / expected_exposure)
    assert kpis.risk_adjusted_return == pytest.approx(
        (expected_interest - expected_loss_value) / expected_exposure
    )


def test_portfolio_kpis_compute_expected_values_engine():
    engine = LoanAnalyticsEngine(sample_frame(), config=LoanAnalyticsConfig(currency="EUR"))
    kpis = engine.portfolio_kpis()

    assert kpis["currency"] == "EUR"
    assert pytest.approx(kpis["total_outstanding"], rel=1e-6) == 150000
    assert pytest.approx(kpis["total_principal"], rel=1e-6) == 285000
    assert pytest.approx(kpis["weighted_interest_rate"], rel=1e-6) == 0.104
    assert pytest.approx(kpis["non_performing_loan_ratio"], rel=1e-6) == 0
    assert pytest.approx(kpis["default_rate"], rel=1e-6) == 0.25
    assert pytest.approx(kpis["loss_given_default"], rel=1e-6) == 0.8
    assert pytest.approx(kpis["prepayment_rate"], rel=1e-6) == pytest.approx(35000 / 285000)
    assert kpis["repayment_velocity"] > 1


def test_prepare_data_validates_structure_and_dates():
    base = sample_frame()
    missing_cols = base.drop(columns=["interest_rate"])

    with pytest.raises(ValueError):
        LoanAnalyticsEngine(missing_cols)

    invalid_date = base.copy()
    invalid_date.loc[0, "origination_date"] = "not-a-date"
    with pytest.raises(ValueError):
        LoanAnalyticsEngine(invalid_date)


def test_prepare_data_rejects_non_numeric_values():
    base = sample_frame()
    base["principal"] = base["principal"].astype(object)
    base.loc[0, "principal"] = "one hundred"

    with pytest.raises(ValueError):
        LoanAnalyticsEngine(base)


def test_prepare_data_rejects_missing_numeric_values_by_default():
    base = sample_frame()
    base.loc[2, "outstanding_principal"] = None

    with pytest.raises(ValueError):
        LoanAnalyticsEngine(base)


def test_prepare_data_allows_explicit_numeric_fill_value():
    base = sample_frame()
    base.loc[2, "recoveries"] = None

    engine = LoanAnalyticsEngine(
        base, config=LoanAnalyticsConfig(numeric_missing_fill_value=0.0)
    )

    assert engine.data.loc[2, "recoveries"] == 0
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.enterprise_analytics_engine import (
    LoanAnalyticsEngine,
    LoanAnalyticsConfig,
    LoanPosition,
    PortfolioKPIs,
    calculate_monthly_payment,
    calculate_portfolio_kpis,
    expected_loss,
    portfolio_interest_and_risk,
)


def test_monthly_payment_matches_finance_formula():
    loan = LoanPosition(principal=100_000, annual_interest_rate=0.12, term_months=36)
    payment = calculate_monthly_payment(loan)

    monthly_rate = loan.annual_interest_rate / 12
    expected_payment = (monthly_rate * loan.principal) / (1 - math.pow(1 + monthly_rate, -loan.term_months))

    assert payment == pytest.approx(expected_payment, rel=1e-8)


def test_portfolio_interest_and_risk_tracks_defaults():
    prime = LoanPosition(principal=50_000, annual_interest_rate=0.08, term_months=24, default_probability=0.01)
    near_prime = LoanPosition(principal=75_000, annual_interest_rate=0.14, term_months=36, default_probability=0.05)
    subprime = LoanPosition(principal=40_000, annual_interest_rate=0.2, term_months=18, default_probability=0.12)

    monthly_interest, portfolio_loss = portfolio_interest_and_risk(
        loans=[prime, near_prime, subprime], loss_given_default=0.45
    )

    expected_interest = (
        prime.principal * (prime.annual_interest_rate / 12)
        + near_prime.principal * (near_prime.annual_interest_rate / 12)
        + subprime.principal * (subprime.annual_interest_rate / 12)
    )

    assert monthly_interest == pytest.approx(expected_interest)
    assert portfolio_loss == pytest.approx(
        expected_loss(prime, 0.45) + expected_loss(near_prime, 0.45) + expected_loss(subprime, 0.45)
    )


def test_invalid_inputs_raise_value_errors():
    with pytest.raises(ValueError):
        LoanPosition(principal=0, annual_interest_rate=0.05, term_months=12)

    with pytest.raises(ValueError):
        LoanPosition(principal=10_000, annual_interest_rate=-0.01, term_months=12)

    with pytest.raises(ValueError):
        LoanPosition(principal=10_000, annual_interest_rate=0.05, term_months=0)

    with pytest.raises(ValueError):
        LoanPosition(principal=10_000, annual_interest_rate=0.05, term_months=12, default_probability=1.5)

    valid_loan = LoanPosition(principal=10_000, annual_interest_rate=0.05, term_months=12)
    with pytest.raises(ValueError):
        expected_loss(valid_loan, loss_given_default=1.2)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3", "L4"],
            "principal": [100000, 50000, 75000, 60000],
            "interest_rate": [0.12, 0.08, 0.10, 0.09],
            "term_months": [24, 18, 24, 12],
            "origination_date": [
                "2023-01-15",
                "2023-02-10",
                "2022-12-05",
                "2023-04-20",
            ],
            "status": ["current", "30dpd", "defaulted", "current"],
            "outstanding_principal": [80000, 30000, 0, 40000],
            "days_in_arrears": [0, 35, 120, 0],
            "charge_off_amount": [0, 0, 50000, 0],
            "recoveries": [0, 0, 10000, 0],
            "paid_principal": [12000, 8000, 5000, 10000],
            "region": ["LATAM", "LATAM", "EMEA", "LATAM"],
            "product": ["SME", "SME", "Corporate", "SME"],
        }
    )


def test_portfolio_kpis_surfaces_weighted_metrics():
    loans = [
        LoanPosition(principal=100_000, annual_interest_rate=0.09, term_months=24, default_probability=0.02),
        LoanPosition(principal=50_000, annual_interest_rate=0.12, term_months=36, default_probability=0.04),
    ]

    kpis = calculate_portfolio_kpis(loans, loss_given_default=0.4)

    expected_exposure = sum(loan.principal for loan in loans)
    weighted_rate = (
        loans[0].annual_interest_rate * loans[0].principal + loans[1].annual_interest_rate * loans[1].principal
    ) / expected_exposure
    weighted_term = (
        loans[0].term_months * loans[0].principal + loans[1].term_months * loans[1].principal
    ) / expected_exposure
    weighted_default_probability = (
        loans[0].default_probability * loans[0].principal
        + loans[1].default_probability * loans[1].principal
    ) / expected_exposure
    expected_interest = sum(loan.principal * (loan.annual_interest_rate / 12) for loan in loans)
    expected_loss_value = sum(expected_loss(loan, 0.4) for loan in loans)

    assert isinstance(kpis, PortfolioKPIs)
    assert kpis.exposure == expected_exposure
    assert kpis.weighted_rate == pytest.approx(weighted_rate)
    assert kpis.weighted_term_months == pytest.approx(weighted_term)
    assert kpis.weighted_default_probability == pytest.approx(weighted_default_probability)
    assert kpis.expected_monthly_interest == pytest.approx(expected_interest)
    assert kpis.expected_monthly_payment == pytest.approx(
        calculate_monthly_payment(loans[0]) + calculate_monthly_payment(loans[1])
    )
    assert kpis.expected_loss == pytest.approx(expected_loss_value)
    assert kpis.expected_loss_rate == pytest.approx(expected_loss_value / expected_exposure)
    assert kpis.interest_yield_rate == pytest.approx(expected_interest / expected_exposure)
    assert kpis.risk_adjusted_return == pytest.approx(
        (expected_interest - expected_loss_value) / expected_exposure
    )



def test_portfolio_kpis_compute_expected_values():
    engine = LoanAnalyticsEngine(sample_frame(), config=LoanAnalyticsConfig(currency="EUR"))
    kpis = engine.portfolio_kpis()

    assert kpis["currency"] == "EUR"
    assert pytest.approx(kpis["total_outstanding"], rel=1e-6) == 150000
    assert pytest.approx(kpis["total_principal"], rel=1e-6) == 285000
    assert pytest.approx(kpis["weighted_interest_rate"], rel=1e-6) == 0.104
    assert pytest.approx(kpis["non_performing_loan_ratio"], rel=1e-6) == 0
    assert pytest.approx(kpis["default_rate"], rel=1e-6) == 0.25
    assert pytest.approx(kpis["loss_given_default"], rel=1e-6) == 0.8
    assert pytest.approx(kpis["prepayment_rate"], rel=1e-6) == pytest.approx(35000 / 285000)
    assert kpis["repayment_velocity"] > 1


def test_prepare_data_validates_inputs():
    base = sample_frame()
    missing_cols = base.drop(columns=["interest_rate"])

    with pytest.raises(ValueError):
        LoanAnalyticsEngine(missing_cols)

    invalid_date = base.copy()
    invalid_date.loc[0, "origination_date"] = "not-a-date"
    with pytest.raises(ValueError):
        LoanAnalyticsEngine(invalid_date)


def test_prepare_data_rejects_non_numeric_values():
    base = sample_frame()
    base["principal"] = base["principal"].astype(object)
    base.loc[0, "principal"] = "one hundred"

    with pytest.raises(ValueError):
        LoanAnalyticsEngine(base)


def test_prepare_data_rejects_missing_numeric_values_by_default():
    base = sample_frame()
    base.loc[2, "outstanding_principal"] = None

    with pytest.raises(ValueError):
        LoanAnalyticsEngine(base)


def test_prepare_data_allows_explicit_numeric_fill_value():
    base = sample_frame()
    base.loc[2, "recoveries"] = None

    engine = LoanAnalyticsEngine(
        base, config=LoanAnalyticsConfig(numeric_missing_fill_value=0.0)
    )

    assert engine.data.loc[2, "recoveries"] == 0
