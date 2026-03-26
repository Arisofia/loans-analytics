from __future__ import annotations

import pandas as pd


def compute_net_yield(finance_mart: pd.DataFrame) -> float:
    if finance_mart.empty:
        return 0.0
    income = finance_mart["interest_income"].sum() + finance_mart["fee_income"].sum()
    debt = finance_mart["debt_balance"].sum()
    if debt == 0:
        return 0.0
    return float(income / debt)


def compute_spread(finance_mart: pd.DataFrame) -> float:
    if finance_mart.empty:
        return 0.0
    income = finance_mart["interest_income"].sum() + finance_mart["fee_income"].sum()
    cost = finance_mart["funding_cost"].sum()
    debt = finance_mart["debt_balance"].sum()
    if debt == 0:
        return 0.0
    return float((income - cost) / debt)
