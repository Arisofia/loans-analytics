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


def test_portfolio_kpis_surfaces_weighted_metrics():
    loss_given_default = 0.4
    loans = [
        LoanPosition(principal=100_000, annual_interest_rate=0.09, term_months=24, default_probability=0.02),
        LoanPosition(principal=50_000, annual_interest_rate=0.12, term_months=36, default_probability=0.04),
    ]

    kpis = calculate_portfolio_kpis(loans, loss_given_default=loss_given_default)

    expected_exposure = sum(loan.principal for loan in loans)
    weighted_rate = (
        loans[0].annual_interest_rate * loans[0].principal + loans[1].annual_interest_rate * loans[1].principal
    ) / expected_exposure
    weighted_term = (
        loans[0].term_months * loans[0].principal + loans[1].term_months * loans[1].principal
    ) / expected_exposure
    weighted_default_probability = (
        loans[0].default_probability * loans[0].principal + loans[1].default_probability * loans[1].principal
    ) / expected_exposure
    expected_interest = sum(loan.principal * (loan.annual_interest_rate / 12) for loan in loans)
    expected_loss_value = sum(expected_loss(loan, loss_given_default) for loan in loans)

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


def test_calculate_portfolio_kpis_single_loan_reduces_to_loan_kpis():
    """For a single loan, portfolio KPIs should collapse to that loan's characteristics."""
    loss_given_default = 0.4
    loan = LoanPosition(
        principal=10_000,
        annual_interest_rate=0.08,
        term_months=24,
        default_probability=0.05,
    )

    kpis = calculate_portfolio_kpis([loan], loss_given_default=loss_given_default)

    assert kpis.exposure == pytest.approx(loan.principal)
    assert kpis.weighted_rate == pytest.approx(loan.annual_interest_rate)
    assert kpis.weighted_term_months == pytest.approx(loan.term_months)
    assert kpis.weighted_default_probability == pytest.approx(loan.default_probability)

    expected_monthly_interest = loan.principal * (loan.annual_interest_rate / 12)
    assert kpis.expected_monthly_interest == pytest.approx(expected_monthly_interest)

    expected_loss_value = loan.principal * loan.default_probability * loss_given_default
    assert kpis.expected_loss == pytest.approx(expected_loss_value)


def test_calculate_portfolio_kpis_varying_lgd_affects_expected_loss():
    """Changing LGD should monotonically change portfolio expected loss."""
    loans = [
        LoanPosition(
            principal=10_000,
            annual_interest_rate=0.12,
            term_months=24,
            default_probability=0.05,
        ),
        LoanPosition(
            principal=5_000,
            annual_interest_rate=0.10,
            term_months=12,
            default_probability=0.02,
        ),
    ]

    kpis_lgd_low = calculate_portfolio_kpis(loans, loss_given_default=0.1)
    kpis_lgd_high = calculate_portfolio_kpis(loans, loss_given_default=0.9)

    assert kpis_lgd_low.exposure == pytest.approx(kpis_lgd_high.exposure)
    assert kpis_lgd_high.expected_loss > kpis_lgd_low.expected_loss


def test_calculate_portfolio_kpis_extreme_values_remain_finite():
    """Extreme principals / rates / PDs should not overflow or produce non-finite KPIs."""
    loans = [
        LoanPosition(
            principal=1_000_000_000,
            annual_interest_rate=0.0001,
            term_months=360,
            default_probability=1e-6,
        ),
        LoanPosition(
            principal=750_000_000,
            annual_interest_rate=0.35,
            term_months=12,
            default_probability=0.9,
        ),
    ]

    kpis = calculate_portfolio_kpis(loans, loss_given_default=0.9)

    assert math.isfinite(kpis.exposure)
    assert math.isfinite(kpis.expected_loss)
    assert math.isfinite(kpis.weighted_rate)
    assert math.isfinite(kpis.expected_monthly_interest)
