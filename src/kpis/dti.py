from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context, safe_numeric


class DTICalculator(KPICalculator):
    """Debt-to-Income (DTI) Ratio."""

    METADATA = KPIMetadata(
        name="DTI",
        description="Average ratio of monthly debt to monthly income",
        formula="AVG(monthly_debt / (borrower_income / 12)) * 100",
        unit="%",
        data_sources=["loan_data"],
        threshold_warning=36.0,
        threshold_critical=43.0,
        owner="Underwriting",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        required = ["monthly_debt", "borrower_income"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        monthly_debt = safe_numeric(df["monthly_debt"])
        monthly_income = safe_numeric(df["borrower_income"]) / 12.0

        # Element-wise DTI
        dti_values = np.where(
            monthly_income > 0,
            (monthly_debt / monthly_income) * 100.0,
            np.nan,
        )
        dti_series = pd.Series(dti_values)

        avg_dti = float(dti_series.mean())

        return avg_dti, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            avg_monthly_debt=float(monthly_debt.mean()),
            avg_monthly_income=float(monthly_income.mean()),
        )


def calculate_dti(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for DTI calculation."""
    return DTICalculator().calculate(df)
