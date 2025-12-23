from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class LoanPosition:
    principal: float
    annual_interest_rate: float
    term_months: int
    default_probability: float = 0.0

    def __post_init__(self) -> None:
        if self.principal <= 0:
            raise ValueError("principal must be positive")
        if self.annual_interest_rate <= 0:
            raise ValueError("annual_interest_rate must be positive")
        if self.term_months <= 0:
            raise ValueError("term_months must be positive")
        if not (0.0 <= self.default_probability <= 1.0):
            raise ValueError("default_probability must be between 0 and 1")


@dataclass
class PortfolioKPIs:
    exposure: float
    weighted_rate: float
    weighted_term_months: float
    weighted_default_probability: float
    expected_monthly_interest: float
    expected_monthly_payment: float
    expected_loss: float
    expected_loss_rate: float
    interest_yield_rate: float
    risk_adjusted_return: float


def calculate_monthly_payment(loan: LoanPosition) -> float:
    monthly_rate = loan.annual_interest_rate / 12
    return (monthly_rate * loan.principal) / (1 - math.pow(1 + monthly_rate, -loan.term_months))


def expected_loss(loan: LoanPosition, loss_given_default: float) -> float:
    if not (0.0 <= loss_given_default <= 1.0):
        raise ValueError("loss_given_default must be between 0 and 1")
    return loan.principal * loan.default_probability * loss_given_default


def portfolio_interest_and_risk(loans: Iterable[LoanPosition], loss_given_default: float) -> tuple[float, float]:
    monthly_interest = sum(loan.principal * (loan.annual_interest_rate / 12) for loan in loans)
    portfolio_loss = sum(expected_loss(loan, loss_given_default) for loan in loans)
    return monthly_interest, portfolio_loss


def calculate_portfolio_kpis(loans: List[LoanPosition], loss_given_default: float) -> PortfolioKPIs:
    exposure = sum(loan.principal for loan in loans)
    if exposure == 0:
        raise ValueError("Total exposure cannot be zero")

    weighted_rate = sum(loan.annual_interest_rate * loan.principal for loan in loans) / exposure
    weighted_term = sum(loan.term_months * loan.principal for loan in loans) / exposure
    weighted_default_probability = (
        sum(loan.default_probability * loan.principal for loan in loans) / exposure
    )

    expected_monthly_interest, expected_loss_value = portfolio_interest_and_risk(loans, loss_given_default)
    expected_monthly_payment = sum(calculate_monthly_payment(loan) for loan in loans)
    expected_loss_rate = expected_loss_value / exposure
    interest_yield_rate = expected_monthly_interest / exposure
    risk_adjusted_return = (expected_monthly_interest - expected_loss_value) / exposure

    return PortfolioKPIs(
        exposure=exposure,
        weighted_rate=weighted_rate,
        weighted_term_months=weighted_term,
        weighted_default_probability=weighted_default_probability,
        expected_monthly_interest=expected_monthly_interest,
        expected_monthly_payment=expected_monthly_payment,
        expected_loss=expected_loss_value,
        expected_loss_rate=expected_loss_rate,
        interest_yield_rate=interest_yield_rate,
        risk_adjusted_return=risk_adjusted_return,
    )
