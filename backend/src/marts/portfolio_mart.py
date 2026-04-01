from __future__ import annotations

import pandas as pd


DPD_BUCKETS = [
    (-1, "current"),
    (0, "current"),
    (1, "1_30"),
    (31, "31_60"),
    (61, "61_90"),
    (91, "90_plus"),
]


def _dpd_bucket(days_past_due: int | float | None) -> str:
    if days_past_due is None or pd.isna(days_past_due):
        return "unknown"
    if days_past_due <= 0:
        return "current"
    if days_past_due <= 30:
        return "1_30"
    if days_past_due <= 60:
        return "31_60"
    if days_past_due <= 90:
        return "61_90"
    return "90_plus"


def build_portfolio_mart(loans_df: pd.DataFrame) -> pd.DataFrame:
    df = loans_df.copy()

    df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce", format="mixed")
    df["origination_month"] = df["origination_date"].dt.to_period("M").astype(str)
    df["cohort"] = df["origination_month"]
    df["vintage"] = df["origination_month"]
    dpd_series = pd.to_numeric(df["days_past_due"], errors="coerce")
    df["dpd_bucket"] = dpd_series.map(_dpd_bucket)

    required_columns = [
        "loan_id",
        "customer_id",
        "origination_date",
        "origination_month",
        "cohort",
        "vintage",
        "funded_amount",
        "outstanding_principal",
        "apr",
        "term_days",
        "days_past_due",
        "dpd_bucket",
        "default_flag",
        "country",
        "sector",
        "originator",
        "source_channel",
        "segment",
        "kam_hunter",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    return df[required_columns].drop_duplicates(subset=["loan_id"])


build = build_portfolio_mart
