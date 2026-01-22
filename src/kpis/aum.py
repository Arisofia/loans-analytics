from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.numeric import safe_numeric


class AUMCalculator(KPICalculator):
    """Assets Under Management (AUM)."""

    METADATA = KPIMetadata(
        name="AUM",
        description="Total outstanding balance of active (Current) loans",
        formula="SUM(outstanding_loan_value WHERE loan_status == 'Current')",
        unit="USD",
        data_sources=["loan_data"],
        owner="Finance",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        # Handle both raw and normalized column names
        status_col = "loan_status" if "loan_status" in df.columns else "status"
        balance_col = (
            "outstanding_loan_value"
            if "outstanding_loan_value" in df.columns
            else (
                "outstanding_balance_usd"
                if "outstanding_balance_usd" in df.columns
                else (
                    "total_receivable_usd"
                    if "total_receivable_usd" in df.columns
                    else "balance"
                )
            )
        )

        if status_col not in df.columns or balance_col not in df.columns:
            # Fallback to sum of all outstanding balance if status not available
            if balance_col in df.columns:
                value = float(safe_numeric(df[balance_col]).sum())
                return value, create_context(
                    self.METADATA.formula,
                    rows_processed=len(df),
                    balance_column=balance_col,
                    status_filtered=False,
                )
            raise ValueError(f"Missing required columns for AUM: {balance_col}")

        active_mask = df[status_col].astype(str).str.lower() == "current"
        active_loans = df[active_mask]
        value = float(safe_numeric(active_loans[balance_col]).sum())

        return value, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            active_loans_count=int(active_mask.sum()),
            status_column=status_col,
            balance_column=balance_col,
        )


def calculate_aum(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for AUM calculation."""
    return AUMCalculator().calculate(df)
