from __future__ import annotations

import pandas as pd


def build_finance_mart(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    df = portfolio_df.copy()
    df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce")
    df["as_of_month"] = df["origination_date"].dt.to_period("M").astype(str)

    rate_col = "interest_rate" if "interest_rate" in df.columns else None
    if rate_col is not None:
        df["_interest_income"] = df["outstanding_principal"].fillna(0) * df[rate_col].fillna(0) / 12
        df["_fee_income"] = df["funded_amount"].fillna(0) * df[rate_col].fillna(0) * 0.05 / 12
    else:
        df["_interest_income"] = df["outstanding_principal"].fillna(0) * 0.02
        df["_fee_income"] = df["funded_amount"].fillna(0) * 0.005

    grouped = (
        df.groupby("as_of_month", dropna=False)
        .agg(
            interest_income=("_interest_income", "sum"),
            fee_income=("_fee_income", "sum"),
            funding_cost=("funded_amount", "sum"),
            provision_expense=("default_flag", "sum"),
            debt_balance=("outstanding_principal", "sum"),
        )
        .reset_index()
    )

    grouped["funding_cost"] = grouped["funding_cost"] * 0.01
    grouped["provision_expense"] = grouped["provision_expense"] * 100.0
    grouped["gross_margin"] = (
        grouped["interest_income"]
        + grouped["fee_income"]
        - grouped["funding_cost"]
        - grouped["provision_expense"]
    )
    grouped["ebitda_proxy"] = grouped["gross_margin"]
    grouped["equity_balance"] = grouped["debt_balance"] * 0.35

    ordered = [
        "as_of_month",
        "interest_income",
        "fee_income",
        "funding_cost",
        "gross_margin",
        "provision_expense",
        "ebitda_proxy",
        "debt_balance",
        "equity_balance",
    ]
    return grouped[ordered]


build = build_finance_mart
