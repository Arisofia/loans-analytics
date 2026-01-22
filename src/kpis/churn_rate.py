from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context


class ChurnRateCalculator(KPICalculator):
    """Annual Customer Churn Rate (2024 vs 2025)."""

    METADATA = KPIMetadata(
        name="ChurnRate",
        description="Percentage of 2024 customers not returning in 2025",
        formula="(count(cust_2024 NOT IN cust_2025) / count(cust_2024)) * 100",
        unit="%",
        data_sources=["loan_data"],
        owner="Growth",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        date_col = (
            "disbursement_date"
            if "disbursement_date" in df.columns
            else "Disbursement Date"
        )
        cust_col = "customer_id" if "customer_id" in df.columns else "Customer ID"

        if date_col not in df.columns or cust_col not in df.columns:
            raise ValueError(f"Missing columns for ChurnRate: {date_col}, {cust_col}")

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        cust_2024 = set(df[df[date_col].dt.year == 2024][cust_col].unique())
        cust_2025 = set(df[df[date_col].dt.year == 2025][cust_col].unique())

        if not cust_2024:
            return 0.0, create_context(
                self.METADATA.formula,
                rows_processed=len(df),
                reason="No customers in 2024",
            )

        churned = cust_2024 - cust_2025
        value = (len(churned) / len(cust_2024)) * 100.0

        return float(value), create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            customers_2024=len(cust_2024),
            customers_2025=len(cust_2025),
            churned_count=len(churned),
        )


def calculate_churn_rate(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Churn Rate calculation."""
    return ChurnRateCalculator().calculate(df)
