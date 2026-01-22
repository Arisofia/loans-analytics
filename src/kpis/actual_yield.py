from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.numeric import safe_numeric


class ActualYieldCalculator(KPICalculator):
    """Actual Portfolio Yield (Cash-based)."""

    METADATA = KPIMetadata(
        name="ActualYield",
        description="Actual interest revenue yield based on cash collections",
        formula="total_interest_paid / avg_aum * 100",
        unit="%",
        data_sources=["historic_real_payment", "loan_data"],
        owner="Finance",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        interest_paid_col = (
            "true_interest_payment"
            if "true_interest_payment" in df.columns
            else "True Interest Payment"
        )
        aum_col = (
            "outstanding_loan_value"
            if "outstanding_loan_value" in df.columns
            else "Outstanding Loan Value"
        )

        # Fallback to normalized columns if needed
        if interest_paid_col not in df.columns:
            interest_paid_col = "cash_interest_usd"
        if aum_col not in df.columns:
            aum_col = "outstanding_balance_usd"

        if interest_paid_col not in df.columns or aum_col not in df.columns:
            raise ValueError(
                f"Missing columns for ActualYield: {interest_paid_col}, {aum_col}"
            )

        total_interest = safe_numeric(df[interest_paid_col]).sum()
        avg_aum = safe_numeric(df[aum_col]).mean()

        if avg_aum == 0:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=len(df), reason="Zero average AUM"
            )

        yield_val = (total_interest / avg_aum) * 100.0

        return float(yield_val), create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            total_interest_paid=float(total_interest),
            average_aum=float(avg_aum),
        )


def calculate_actual_yield(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Actual Yield calculation."""
    return ActualYieldCalculator().calculate(df)
