"""Data contracts and schemas using Pandera for Abaco Loans Analytics."""

from typing import List, Optional

import pandas as pd
import pandera as pa
from pandera.typing import Series


class LoanTapeSchema(pa.DataFrameModel):
    """Data contract for loan tape ingestion."""

    # Pandera Schema Fields
    loan_id: Series[str] = pa.Field(unique=True, coerce=True)
    outstanding_balance: Optional[Series[float]] = pa.Field(ge=0, nullable=True)
    dpd: Optional[Series[int]] = pa.Field(ge=0, le=3650, nullable=True)
    disbursement_date: Optional[Series[pd.Timestamp]] = pa.Field(nullable=True)
    loan_status: Optional[Series[str]] = pa.Field(
        isin=["Active", "Closed", "Default", "Collection", "Complete", "Defaulted"], nullable=True
    )
    interest_rate_apr: Optional[Series[float]] = pa.Field(ge=0, le=2.0, nullable=True)

    @pa.check("disbursement_date")
    @staticmethod
    def date_not_in_future(series: Series) -> Series:
        """Ensure disbursement dates are not in the future."""
        return series <= pd.Timestamp.now()

    class Config:
        strict = False
        coerce = True


class LoanTapeConstants:
    """Legacy Constants (Integrated)."""

    REQUIRED_COLUMNS: List[str] = [
        "loan_id",
        "period",
        "measurement_date",
        "total_receivable_usd",
        "total_eligible_usd",
        "discounted_balance_usd",
        "dpd_0_7_usd",
        "dpd_7_30_usd",
        "dpd_30_60_usd",
        "dpd_60_90_usd",
        "dpd_90_plus_usd",
    ]

    NUMERIC_COLUMNS: List[str] = [
        "total_receivable_usd",
        "total_eligible_usd",
        "discounted_balance_usd",
        "dpd_0_7_usd",
        "dpd_7_30_usd",
        "dpd_30_60_usd",
        "dpd_60_90_usd",
        "dpd_90_plus_usd",
        "cash_available_usd",
    ]

    ANALYTICS_COLUMNS: List[str] = [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "loan_status",
        "interest_rate",
        "principal_balance",
    ]


class FinancialMetricsSchema(pa.DataFrameModel):
    """Data contract for aggregate financial metrics."""

    total_outstanding: Series[float] = pa.Field(ge=0)
    avg_apr: Series[float] = pa.Field(ge=0, le=2.0)
    default_rate: Series[float] = pa.Field(ge=0, le=1.0)
    loan_count: Series[int] = pa.Field(ge=0)


def validate_loan_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate loan data against the LoanTapeSchema."""
    return LoanTapeSchema.validate(df)
