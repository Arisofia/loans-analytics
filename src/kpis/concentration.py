from typing import Any, Dict, Tuple

import pandas as pd

from src.kpis.base import KPICalculator, KPIMetadata, create_context


class ConcentrationCalculator(KPICalculator):
    """Customer Concentration (Top 10)."""

    METADATA = KPIMetadata(
        name="ConcentrationTop10",
        description="Top 10 customers as percentage of total portfolio disbursement",
        formula="SUM(top_10_customer_disbursement) / SUM(total_disbursement) * 100",
        unit="%",
        data_sources=["loan_data"],
        owner="Risk",
    )

    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        if df is None or df.empty:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=0, reason="Empty DataFrame"
            )

        cust_col = "customer_id" if "customer_id" in df.columns else "Customer ID"
        disb_col = (
            "disbursement_amount" if "disbursement_amount" in df.columns else "Disbursement Amount"
        )

        if cust_col not in df.columns or disb_col not in df.columns:
            if "customer_id" not in df.columns:
                cust_col = "client_id"
            if "disburse_principal" in df.columns:
                disb_col = "disburse_principal"

        if cust_col not in df.columns or disb_col not in df.columns:
            raise ValueError(f"Missing columns for Concentration: {cust_col}, {disb_col}")

        # Group by customer
        cust_disb = df.groupby(cust_col)[disb_col].sum().sort_values(ascending=False)
        total_disb = cust_disb.sum()

        if total_disb == 0:
            return 0.0, create_context(
                self.METADATA.formula, rows_processed=len(df), reason="Zero total disbursement"
            )

        top_10_sum = cust_disb.head(10).sum()
        value = (top_10_sum / total_disb) * 100.0

        return float(value), create_context(
            self.METADATA.formula,
            rows_processed=len(df),
            total_customers=len(cust_disb),
            top_10_sum=float(top_10_sum),
            total_disbursement=float(total_disb),
        )


def calculate_concentration_top10(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Standard interface for Concentration Top 10 calculation."""
    return ConcentrationCalculator().calculate(df)
