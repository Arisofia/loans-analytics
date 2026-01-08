from typing import Optional, TypedDict


class FinancialRow(TypedDict):
    """Typed representation of a financial row for PAR/Portfolio analysis."""

    loan_id: str
    measurement_date: str
    total_receivable_usd: float
    total_eligible_usd: float
    discounted_balance_usd: float
    cash_available_usd: float
    dpd_0_7_usd: float
    dpd_7_30_usd: float
    dpd_30_60_usd: float
    dpd_60_90_usd: float
    dpd_90_plus_usd: float
    currency: str


class TransactionRow(TypedDict):
    """Typed representation of a financial transaction with IBAN."""

    transaction_id: str
    amount: float
    currency: str
    iban: str
    timestamp: str
    status: str
    counterparty_name: Optional[str]
