from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import (KPICalculator, KPIMetadata, create_context,
                           safe_numeric)


class CollectionRateCalculator(KPICalculator):
    """Effective Collection Rate."""

    METADATA = KPIMetadata(
        name="CollectionRate",
        description="Collections as percentage of receivables outstanding",
        formula="SUM(cash_available) / SUM(total_eligible) * 100",
        unit="%",
        data_sources=["cascade.collections"],
        threshold_warning=1.5,
        threshold_critical=1.0,
        owner="CFO",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.shape[0] == 0:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=0,
                reason="Empty DataFrame",
            )

        null_count = 0
        if "cash_available_usd" in df:
            null_count += df["cash_available_usd"].isnull().sum()
        if "total_eligible_usd" in df:
            null_count += df["total_eligible_usd"].isnull().sum()

        cash = safe_numeric(df.get("cash_available_usd", pd.Series())).sum()
        eligible = safe_numeric(df.get("total_eligible_usd", pd.Series())).sum()

        if eligible == 0:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                null_count=int(null_count),
                reason="Zero total eligible",
            )

        value = round((cash / eligible) * 100.0, 2)
        return value, create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            null_count=int(null_count),
            cash_sum=float(cash),
            eligible_sum=float(eligible),
        )


def calculate_collection_rate(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Legacy interface for collection rate calculation."""
    calculator = CollectionRateCalculator()
    return calculator.calculate(df)
