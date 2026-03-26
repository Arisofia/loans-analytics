from __future__ import annotations

import pandas as pd


def compute_par30(portfolio_mart: pd.DataFrame) -> float:
    if portfolio_mart.empty:
        return 0.0
    total = portfolio_mart["outstanding_principal"].fillna(0).sum()
    if total == 0:
        return 0.0
    overdue = portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 30,
        "outstanding_principal",
    ].sum()
    return float(overdue / total)


def compute_par60(portfolio_mart: pd.DataFrame) -> float:
    if portfolio_mart.empty:
        return 0.0
    total = portfolio_mart["outstanding_principal"].fillna(0).sum()
    if total == 0:
        return 0.0
    overdue = portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 60,
        "outstanding_principal",
    ].sum()
    return float(overdue / total)


def compute_par90(portfolio_mart: pd.DataFrame) -> float:
    if portfolio_mart.empty:
        return 0.0
    total = portfolio_mart["outstanding_principal"].fillna(0).sum()
    if total == 0:
        return 0.0
    overdue = portfolio_mart.loc[
        portfolio_mart["days_past_due"].fillna(0) >= 90,
        "outstanding_principal",
    ].sum()
    return float(overdue / total)


def compute_expected_loss(portfolio_mart: pd.DataFrame) -> float:
    df = portfolio_mart.copy()
    if "pd" not in df.columns:
        df["pd"] = 0.03
    if "lgd" not in df.columns:
        df["lgd"] = 0.45
    if "ead" not in df.columns:
        df["ead"] = df["outstanding_principal"].fillna(0)
    return float((df["pd"] * df["lgd"] * df["ead"]).sum())
