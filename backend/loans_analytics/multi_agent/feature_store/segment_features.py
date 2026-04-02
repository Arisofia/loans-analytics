from __future__ import annotations

import pandas as pd


def build_segment_features(portfolio_mart: pd.DataFrame) -> pd.DataFrame:
    if portfolio_mart.empty:
        return pd.DataFrame(columns=["segment", "loan_count", "avg_apr", "avg_dpd"])

    df = portfolio_mart.copy()
    df["segment"] = df["dpd_bucket"].fillna("unknown")

    grouped = (
        df.groupby("segment")
        .agg(
            loan_count=("loan_id", "count"),
            avg_apr=("apr", "mean"),
            avg_dpd=("days_past_due", "mean"),
        )
        .reset_index()
    )
    return grouped
