from __future__ import annotations

import pandas as pd


def build_finance_mart(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    df = portfolio_df.copy()
    df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce")
    df["as_of_month"] = df["origination_date"].dt.to_period("M").astype(str)

    grouped = (
        df.groupby("as_of_month", dropna=False)
        .agg(
            interest_income=("funded_amount", "sum"),
            fee_income=("funded_amount", "sum"),
            funding_cost=("funded_amount", "sum"),
            provision_expense=("default_flag", "sum"),
            debt_balance=("outstanding_principal", "sum"),
        )
        .reset_index()
    )

    grouped["interest_income"] = grouped["interest_income"] * 0.02
    grouped["fee_income"] = grouped["fee_income"] * 0.005
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
