from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.data_normalization import (COL_DPD_90_PLUS,
                                          COL_OUTSTANDING_AMOUNT,
                                          normalize_columns)
from src.utils.numeric import safe_numeric


class PAR90Calculator(KPICalculator):
    """Portfolio at Risk > 90 days (PAR 90)."""

    METADATA = KPIMetadata(
        name="PAR90",
        description="Percentage of portfolio delinquent beyond 90 days",
        formula="SUM(dpd_90_plus_usd) / SUM(total_receivable_usd) * 100",
        unit="%",
        data_sources=["cascade.loan_status"],
        threshold_warning=3.0,
        threshold_critical=5.0,
        owner="CRO",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.shape[0] == 0:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=0,
                reason="Empty DataFrame",
            )

        # Standardize columns
        working_df = normalize_columns(df)

        null_count = (
            working_df[COL_DPD_90_PLUS].isnull().sum() if COL_DPD_90_PLUS in working_df else 0
        )

        dpd = safe_numeric(working_df.get(COL_DPD_90_PLUS, pd.Series())).sum()
        total_receivable = safe_numeric(working_df.get(COL_OUTSTANDING_AMOUNT, pd.Series())).sum()

        if total_receivable == 0:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                null_count=int(null_count),
                reason="Zero total receivable",
            )

        value = (dpd / total_receivable) * 100.0
        return value, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            null_count=int(null_count),
            dpd_sum=float(dpd),
            total_receivable_sum=float(total_receivable),
        )


def calculate_par_90(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for PAR90 calculation."""
    calculator = PAR90Calculator()
    return calculator.calculate(df)
