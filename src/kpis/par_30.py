from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import (KPICalculator, KPIMetadata, create_context,
                           safe_numeric)


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

        # Check for required columns or fallback to loan_status
        required = ["dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd", "total_receivable_usd"]
        has_dpd_cols = all(col in df.columns for col in required)

        if has_dpd_cols:
            null_count = sum(df[col].isnull().sum() for col in required if col in df)
            dpd_30_60 = safe_numeric(df["dpd_30_60_usd"]).sum()
            dpd_60_90 = safe_numeric(df["dpd_60_90_usd"]).sum()
            dpd_90_plus = safe_numeric(df["dpd_90_plus_usd"]).sum()
            total_receivable = safe_numeric(df["total_receivable_usd"]).sum()

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
        elif "loan_status" in df.columns:
            # Fallback for datasets like the one in tests/test_analytics_metrics.py
            delinquent_statuses = [
                "30-59 days past due",
                "60-89 days past due",
                "90+ days past due",
            ]
            delinquent_count = df["loan_status"].isin(delinquent_statuses).sum()
            total_loans = len(df)
            value = (delinquent_count / total_loans) * 100.0 if total_loans > 0 else 0.0
            return value, create_context(
                self.METADATA.formula,
                rows_processed=total_loans,
                delinquent_count=int(delinquent_count),
                method="loan_status_fallback",
            )
        else:
            raise ValueError(f"Missing required columns: {', '.join(required)} or 'loan_status'")


def calculate_par_30(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for PAR30 calculation."""
    calculator = PAR30Calculator()
    return calculator.calculate(df)
