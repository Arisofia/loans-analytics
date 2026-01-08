from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.numeric import safe_numeric


class RecurrenceCalculator(KPICalculator):
    """Revenue Recurrence (Interest share of total cash)."""

    METADATA = KPIMetadata(
        name="Recurrence",
        description="Interest payments as percentage of total cash revenue",
        formula="cash_interest / (cash_interest + cash_fee + cash_other) * 100",
        unit="%",
        data_sources=["historic_real_payment"],
        owner="Finance",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        int_col = (
            "true_interest_payment"
            if "true_interest_payment" in df.columns
            else "True Interest Payment"
        )
        fee_col = "true_fee_payment" if "true_fee_payment" in df.columns else "True Fee Payment"
        oth_col = (
            "true_other_payment" if "true_other_payment" in df.columns else "True Other Payment"
        )

        if int_col not in df.columns:
            # Try normalized
            int_col, fee_col, oth_col = "cash_interest_usd", "cash_fee_usd", "cash_other_usd"

        if int_col not in df.columns:
            raise ValueError(f"Missing columns for Recurrence: {int_col}")

        cash_interest = safe_numeric(df[int_col]).sum()
        cash_fee = safe_numeric(df.get(fee_col, pd.Series([0.0]))).sum()
        cash_other = safe_numeric(df.get(oth_col, pd.Series([0.0]))).sum()

        total_cash = cash_interest + cash_fee + cash_other

        if total_cash == 0:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=len(df), reason="Zero total cash revenue"
            )

        value = (cash_interest / total_cash) * 100.0

        return float(value), create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            cash_interest=float(cash_interest),
            total_cash=float(total_cash),
        )


def calculate_recurrence(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Recurrence calculation."""
    return RecurrenceCalculator().calculate(df)
