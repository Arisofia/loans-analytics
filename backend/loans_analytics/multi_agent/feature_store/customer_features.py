from __future__ import annotations

import pandas as pd


def build_customer_features(portfolio_mart: pd.DataFrame) -> pd.DataFrame:
    if portfolio_mart.empty or "customer_id" not in portfolio_mart.columns:
        return pd.DataFrame(columns=["customer_id", "loan_count", "total_funded", "avg_dpd"])

    grouped = (
        portfolio_mart.groupby("customer_id")
        .agg(
            loan_count=("loan_id", "count"),
            total_funded=("funded_amount", "sum"),
            avg_dpd=("days_past_due", "mean"),
        )
        .reset_index()
    )
    return grouped
