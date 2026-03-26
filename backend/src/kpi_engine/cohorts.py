from __future__ import annotations

import pandas as pd


def build_cohort_default_curve(portfolio_mart: pd.DataFrame) -> pd.DataFrame:
    if portfolio_mart.empty:
        return pd.DataFrame(columns=["cohort", "default_rate"])
    grouped = (
        portfolio_mart.groupby("cohort", dropna=False)["default_flag"]
        .mean()
        .reset_index(name="default_rate")
    )
    return grouped


def build_vintage_quality_summary(portfolio_mart: pd.DataFrame) -> pd.DataFrame:
    if portfolio_mart.empty:
        return pd.DataFrame(columns=["vintage", "par30_proxy"])
    grouped = (
        portfolio_mart.assign(par30_flag=portfolio_mart["days_past_due"].fillna(0) >= 30)
        .groupby("vintage", dropna=False)["par30_flag"]
        .mean()
        .reset_index(name="par30_proxy")
    )
    return grouped
