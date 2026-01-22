from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.numeric import safe_numeric


class WeightedAPRCalculator(KPICalculator):
    """Weighted Average Interest Rate (APR)."""

    METADATA = KPIMetadata(
        name="WeightedAPR",
        description="Weighted average interest rate by disbursement amount",
        formula="SUM(interest_rate_apr * disbursement_amount) / SUM(disbursement_amount) * 100",
        unit="%",
        data_sources=["loan_data"],
        owner="Finance",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        apr_col = (
            "interest_rate_apr"
            if "interest_rate_apr" in df.columns
            else "Interest Rate APR"
        )
        disb_col = (
            "disbursement_amount"
            if "disbursement_amount" in df.columns
            else "Disbursement Amount"
        )

        if apr_col not in df.columns or disb_col not in df.columns:
            # Try other common names
            if "interest_rate" in df.columns:
                apr_col = "interest_rate"
            if "disburse_principal" in df.columns:
                disb_col = "disburse_principal"

        if apr_col not in df.columns or disb_col not in df.columns:
            raise ValueError(f"Missing columns for WeightedAPR: {apr_col}, {disb_col}")

        apr = safe_numeric(df[apr_col])
        disb = safe_numeric(df[disb_col])

        total_disb = disb.sum()
        if total_disb == 0:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                reason="Zero total disbursement",
            )

        weighted_apr = (apr * disb).sum() / total_disb

        # If APR is already in decimal (e.g. 0.15 for 15%), and we want %, we might need to multiply by 100
        # The snippet says * 100 at the end, implying it expects result in percentage points.
        value = float(weighted_apr * 100.0)

        return value, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            total_disbursement=float(total_disb),
            apr_column=apr_col,
            disbursement_column=disb_col,
        )


def calculate_weighted_apr(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Weighted APR calculation."""
    return WeightedAPRCalculator().calculate(df)
