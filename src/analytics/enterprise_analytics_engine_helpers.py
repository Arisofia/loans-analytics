from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LoanPosition:
    principal: float
    annual_interest_rate: float
    term_months: int
    default_probability: float = 0.0

    def __post_init__(self):
        if self.principal <= 0:
            raise ValueError("Principal must be positive")
        if self.annual_interest_rate < 0:
            raise ValueError("Interest rate cannot be negative")
        if self.term_months <= 0:
            raise ValueError("Term months must be positive")
        if not (0.0 <= self.default_probability <= 1.0):
            raise ValueError("Default probability must be between 0 and 1")


@dataclass(frozen=True)
class PortfolioKPIs:
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


def calculate_monthly_payment(loan: LoanPosition) -> float:
    r = loan.annual_interest_rate / 12
    n = loan.term_months
    if r == 0 or n == 0:
        return loan.principal / n if n else 0.0
    return (r * loan.principal) / (1 - (1 + r) ** -n)


def expected_loss(loan: LoanPosition, loss_given_default: float) -> float:
    if not (0.0 <= loss_given_default <= 1.0):
        raise ValueError("Loss given default must be between 0 and 1")
    return loan.principal * loan.default_probability * loss_given_default


def portfolio_interest_and_risk(loans: List[LoanPosition], loss_given_default: float):
    # Simple interest expectation based on tests
    total_interest = sum(
        loan.principal * (loan.annual_interest_rate / 12) for loan in loans
    )
    total_loss = sum(expected_loss(loan, loss_given_default) for loan in loans)
    return total_interest, total_loss


def calculate_portfolio_kpis(
    loans: List[LoanPosition], loss_given_default: float
) -> PortfolioKPIs:
    exposure = sum(loan.principal for loan in loans)
    weighted_rate = (
        sum(loan.annual_interest_rate * loan.principal for loan in loans) / exposure
        if exposure
        else 0.0
    )
    weighted_term_months = (
        sum(loan.term_months * loan.principal for loan in loans) / exposure
        if exposure
        else 0.0
    )
    weighted_default_probability = (
        sum(loan.default_probability * loan.principal for loan in loans) / exposure
        if exposure
        else 0.0
    )
    expected_monthly_payment = sum(calculate_monthly_payment(loan) for loan in loans)
    # Corrected to simple monthly interest on principal to match test expectations
    expected_monthly_interest = sum(
        loan.principal * (loan.annual_interest_rate / 12) for loan in loans
    )
    expected_loss_value = sum(expected_loss(loan, loss_given_default) for loan in loans)
    expected_loss_rate = expected_loss_value / exposure if exposure else 0.0
    interest_yield_rate = (expected_monthly_interest / exposure) if exposure else 0.0
    risk_adjusted_return = (
        (expected_monthly_interest - expected_loss_value) / exposure
        if exposure
        else 0.0
    )
    return PortfolioKPIs(
        exposure=exposure,
        weighted_rate=weighted_rate,
        weighted_term_months=weighted_term_months,
        weighted_default_probability=weighted_default_probability,
        expected_monthly_payment=expected_monthly_payment,
        expected_monthly_interest=expected_monthly_interest,
        expected_loss=expected_loss_value,
        expected_loss_rate=expected_loss_rate,
        interest_yield_rate=interest_yield_rate,
        risk_adjusted_return=risk_adjusted_return,
    )
