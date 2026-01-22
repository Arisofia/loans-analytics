from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.kpis.base import (KPICalculator, KPIMetadata, create_context,
                           safe_numeric)


class LTVCalculator(KPICalculator):
    """Loan-to-Value (LTV) Ratio."""

    METADATA = KPIMetadata(
        name="LTV",
        description="Average ratio of loan amount to appraised value",
        formula="AVG(loan_amount / appraised_value) * 100",
        unit="%",
        data_sources=["loan_data"],
        threshold_warning=80.0,
        threshold_critical=90.0,
        owner="Risk",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        required = ["loan_amount", "appraised_value"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        loan_amount = safe_numeric(df["loan_amount"])
        appraised_value = safe_numeric(df["appraised_value"])

        # Element-wise LTV
        ltv_values = np.where(
            appraised_value > 0,
            (loan_amount / appraised_value) * 100.0,
            np.nan,
        )
        ltv_series = pd.Series(ltv_values)

        avg_ltv = float(ltv_series.mean())

        return avg_ltv, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            avg_loan_amount=float(loan_amount.mean()),
            avg_appraised_value=float(appraised_value.mean()),
        )


def calculate_ltv(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for LTV calculation."""
    return LTVCalculator().calculate(df)
