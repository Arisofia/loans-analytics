"""Data contracts and schemas using Pandera for Abaco Loans Analytics - Engineering Excellence Edition."""

from typing import Optional  # noqa: E402

import pandas as pd  # noqa: E402

try:
    import pandera as pandera_lib  # noqa: E402
    from pandera.typing import Series  # noqa: E402
except ImportError:

    class SchemaConfig:
        class DataFrameModel:
            pass

        @staticmethod
        def Field(*args, **kwargs):
            return None

        @staticmethod
        def check(*args, **kwargs):
            def decorator(fn):
                return fn

            return decorator

    class SeriesDef:
        def __class_getitem__(cls, item):
            return None


class LoanTapeSchema(pandera_lib.DataFrameModel):
    """Data contract for loan tape ingestion - Engineering Excellence Edition."""

    loan_id: Series[str] = pandera_lib.Field(unique=True, coerce=True)
    outstanding_balance: Series[float] = pandera_lib.Field(ge=0)  # Must be non-negative
    dpd: Series[int] = pandera_lib.Field(ge=0, le=3650)  # Sanity check
    disbursement_date: Series[pd.Timestamp] = pandera_lib.Field(nullable=True)

    # Optional fields for analytical depth
    loan_status: Optional[Series[str]] = pandera_lib.Field(
        isin=["Active", "Closed", "Default", "Collection"], nullable=True
    )
    interest_rate_apr: Optional[Series[float]] = pandera_lib.Field(ge=0, le=2.0, nullable=True)

    @pandera_lib.check("disbursement_date")
    @staticmethod
    def date_not_in_future(series: Series) -> Series:
        """Ensure disbursement dates are not in the future."""
        return series <= pd.Timestamp.now()

    class Config:
        strict = False  # Allow extra columns for now, but validate defined ones
        coerce = True


class FinancialMetricsSchema(pandera_lib.DataFrameModel):
    """Data contract for aggregate financial metrics."""

    total_outstanding: Series[float] = pandera_lib.Field(ge=0)
    avg_apr: Series[float] = pandera_lib.Field(ge=0, le=2.0)
    default_rate: Series[float] = pandera_lib.Field(ge=0, le=1.0)
    loan_count: Series[int] = pandera_lib.Field(ge=0)


def validate_loan_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate loan data against the LoanTapeSchema."""
    return LoanTapeSchema.validate(df)
