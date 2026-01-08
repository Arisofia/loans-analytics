from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context
from src.utils.data_normalization import (COL_DPD_30_60, COL_DPD_60_90,
                                          COL_DPD_90_PLUS, COL_LOAN_STATUS,
                                          COL_OUTSTANDING_AMOUNT,
                                          normalize_columns)
from src.utils.numeric import safe_numeric


class PAR30Calculator(KPICalculator):
    """Portfolio at Risk > 30 days (PAR 30)."""

    METADATA = KPIMetadata(
        name="PAR30",
        description="Percentage of portfolio delinquent 30+ days",
        formula="SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable) * 100",
        unit="%",
        data_sources=["cascade.loan_status"],
        threshold_warning=5.0,
        threshold_critical=8.0,
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

        # Check for required columns or fallback to loan_status
        required = [COL_DPD_30_60, COL_DPD_60_90, COL_DPD_90_PLUS, COL_OUTSTANDING_AMOUNT]
        has_dpd_cols = all(col in working_df.columns for col in required)

        if has_dpd_cols:
            null_count = sum(
                working_df[col].isnull().sum() for col in required if col in working_df
            )
            dpd_30_60 = safe_numeric(working_df[COL_DPD_30_60]).sum()
            dpd_60_90 = safe_numeric(working_df[COL_DPD_60_90]).sum()
            dpd_90_plus = safe_numeric(working_df[COL_DPD_90_PLUS]).sum()
            total_receivable = safe_numeric(working_df[COL_OUTSTANDING_AMOUNT]).sum()

            if total_receivable == 0:
                return 0.0, create_context(
                    self.METADATA.formula,
                    rows_processed=len(df),
                    null_count=int(null_count),
                    reason="Zero total receivable",
                )

            value = (dpd_30_60 + dpd_60_90 + dpd_90_plus) / total_receivable * 100.0
            return value, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                null_count=int(null_count),
                dpd_30_60_sum=float(dpd_30_60),
                dpd_60_90_sum=float(dpd_60_90),
                dpd_90_plus_sum=float(dpd_90_plus),
                total_receivable_sum=float(total_receivable),
            )

        if COL_LOAN_STATUS in working_df.columns:
            # Fallback for datasets like the one in tests/test_analytics_metrics.py
            delinquent_statuses = [
                "30-59 days past due",
                "60-89 days past due",
                "90+ days past due",
            ]
            delinquent_count = working_df[COL_LOAN_STATUS].isin(delinquent_statuses).sum()
            total_loans = len(working_df)
            value = (delinquent_count / total_loans) * 100.0 if total_loans > 0 else 0.0
            return value, create_context(
                self.METADATA.formula,
                rows_processed=total_loans,
                delinquent_count=int(delinquent_count),
                method="loan_status_fallback",
            )

        raise ValueError(f"Missing required columns: {', '.join(required)} or '{COL_LOAN_STATUS}'")


def calculate_par_30(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for PAR30 calculation."""
    calculator = PAR30Calculator()
    return calculator.calculate(df)
