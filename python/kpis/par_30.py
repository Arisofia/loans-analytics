from typing import Any, Dict, Tuple

import pandas as pd

from python.kpis.base import KPICalculator, KPIMetadata, create_context, safe_numeric


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

        required = ["dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd", "total_receivable_usd"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

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

        value = round((dpd_30_60 + dpd_60_90 + dpd_90_plus) / total_receivable * 100.0, 2)
        return value, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            null_count=int(null_count),
            dpd_30_60_sum=float(dpd_30_60),
            dpd_60_90_sum=float(dpd_60_90),
            dpd_90_plus_sum=float(dpd_90_plus),
            total_receivable_sum=float(total_receivable),
        )


def calculate_par_30(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for PAR30 calculation."""
    calculator = PAR30Calculator()
    return calculator.calculate(df)
