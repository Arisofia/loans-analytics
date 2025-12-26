from typing import Any, Dict, Tuple

import pandas as pd

from python.kpis.base import KPICalculator, KPIMetadata, safe_numeric, create_context


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

        null_count = df["dpd_90_plus_usd"].isnull().sum() if "dpd_90_plus_usd" in df else 0

        dpd = safe_numeric(df.get("dpd_90_plus_usd", pd.Series())).sum()
        total_receivable = safe_numeric(df.get("total_receivable_usd", pd.Series())).sum()

        if total_receivable == 0:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                null_count=int(null_count),
                reason="Zero total receivable",
            )

        value = round((dpd / total_receivable) * 100.0, 2)
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
