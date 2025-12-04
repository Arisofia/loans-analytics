import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.enterprise_analytics_engine import (  # noqa: E402
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

    monthly_interest, portfolio_loss = portfolio_interest_and_risk(loans=[prime, near_prime, subprime], loss_given_default=0.45)

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
