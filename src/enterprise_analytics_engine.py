"""Portfolio analytics utilities for credit KPIs and risk metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple


@dataclass(frozen=True)
class LoanPosition:
    principal: float
    annual_interest_rate: float
    term_months: int
    default_probability: float = 0.0

    def __post_init__(self) -> None:
        if self.principal <= 0:
            raise ValueError("Principal must be greater than zero.")
        if self.annual_interest_rate < 0:
            raise ValueError("Annual interest rate cannot be negative.")
        if self.term_months <= 0:
            raise ValueError("Term months must be greater than zero.")
        if not 0 <= self.default_probability <= 1:
            raise ValueError("Default probability must be between 0 and 1.")


def _monthly_interest_rate(loan: LoanPosition) -> float:
    """Return the monthly interest rate as a decimal."""

    return loan.annual_interest_rate / 12


def calculate_monthly_payment(loan: LoanPosition) -> float:
    """Return the amortized monthly payment for a fixed-rate loan."""
    monthly_rate = _monthly_interest_rate(loan)
    if monthly_rate == 0:
        return loan.principal / loan.term_months

    numerator = monthly_rate * loan.principal
    denominator = 1 - (1 + monthly_rate) ** (-loan.term_months)
    return numerator / denominator


def expected_loss(loan: LoanPosition, loss_given_default: float) -> float:
    """Compute expected loss for a single loan position."""
    if not 0 <= loss_given_default <= 1:
        raise ValueError("Loss given default must be between 0 and 1.")

    exposure_at_default = loan.principal
    return exposure_at_default * loan.default_probability * loss_given_default


def portfolio_interest_and_risk(
    loans: Sequence[LoanPosition], loss_given_default: float
) -> Tuple[float, float]:
    """
    Aggregate expected first-month interest and expected loss across a portfolio.

    Returns:
        A tuple with (expected_monthly_interest, expected_loss_value).
    """
    expected_interest = 0.0
    aggregated_loss = 0.0

    for loan in loans:
        expected_interest += loan.principal * _monthly_interest_rate(loan)
        aggregated_loss += expected_loss(loan, loss_given_default)

    return expected_interest, aggregated_loss


@dataclass(frozen=True)
class PortfolioKPIs:
    """Aggregate indicators for portfolio performance and risk."""

    exposure: float
    weighted_rate: float
    weighted_term_months: float
    weighted_default_probability: float
    expected_monthly_payment: float
    expected_monthly_interest: float
    expected_loss: float
    expected_loss_rate: float
    interest_yield_rate: float
    risk_adjusted_return: float


def calculate_portfolio_kpis(
    loans: Sequence[LoanPosition], loss_given_default: float
) -> PortfolioKPIs:
    """
    Compute weighted averages and expected first-month cash flows for a portfolio.

    The calculation returns exposure, weighted rate and term (principal weighted),
    expected total monthly payment, first-month interest, and expected loss.
    """

    exposure = 0.0
    weighted_rate = 0.0
    weighted_term = 0.0
    weighted_default_probability = 0.0
    expected_payment = 0.0
    expected_interest = 0.0
    aggregated_loss = 0.0

    for loan in loans:
        exposure += loan.principal
        weighted_rate += loan.annual_interest_rate * loan.principal
        weighted_term += loan.term_months * loan.principal
        weighted_default_probability += loan.default_probability * loan.principal
        monthly_payment = calculate_monthly_payment(loan)
        expected_payment += monthly_payment
        expected_interest += loan.principal * _monthly_interest_rate(loan)
        aggregated_loss += expected_loss(loan, loss_given_default)

    if exposure == 0:
        return PortfolioKPIs(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    expected_loss_rate = aggregated_loss / exposure
    interest_yield_rate = expected_interest / exposure
    risk_adjusted_return = (expected_interest - aggregated_loss) / exposure
    weighted_default_prob = weighted_default_probability / exposure

    return PortfolioKPIs(
        exposure=exposure,
        weighted_rate=weighted_rate / exposure,
        weighted_term_months=weighted_term / exposure,
        weighted_default_probability=weighted_default_prob,
        expected_monthly_payment=expected_payment,
        expected_monthly_interest=expected_interest,
        expected_loss=aggregated_loss,
        expected_loss_rate=expected_loss_rate,
        interest_yield_rate=interest_yield_rate,
        risk_adjusted_return=risk_adjusted_return,
    )
