from __future__ import annotations

import pandas as pd


def compute_avg_ticket(sales_mart: pd.DataFrame) -> float:
    if sales_mart.empty or "approved_ticket" not in sales_mart.columns:
        return 0.0
    return float(sales_mart["approved_ticket"].dropna().mean() or 0.0)


def compute_win_rate(sales_mart: pd.DataFrame) -> float:
    if sales_mart.empty:
        return 0.0
    total = len(sales_mart)
    if total == 0:
        return 0.0
    wins = int(sales_mart["funded_flag"].fillna(False).sum())
    return float(wins / total)


def compute_contribution_margin(finance_mart: pd.DataFrame) -> float:
    if finance_mart.empty:
        return 0.0
    return float(finance_mart["gross_margin"].sum())
