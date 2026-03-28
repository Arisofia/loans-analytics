from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def _series_or_zero(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return pd.Series(0.0, index=df.index, dtype=float)


def _first_present(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def build_finance_mart(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    df = portfolio_df.copy()
    df["origination_date"] = pd.to_datetime(df.get("origination_date"), errors="coerce")
    df["as_of_month"] = df["origination_date"].dt.to_period("M").astype(str)

    outstanding = _series_or_zero(df, "outstanding_principal")
    funded = _series_or_zero(df, "funded_amount")

    interest_income_col = _first_present(df, ["interest_income", "interest_income_usd"])
    fee_income_col = _first_present(df, ["fee_income", "fee_income_usd", "origination_fee"])
    funding_cost_col = _first_present(df, ["funding_cost", "funding_cost_usd", "interest_expense"])
    provision_col = _first_present(df, ["provision_expense", "expected_loss", "provision_expense_usd"])

    if interest_income_col:
        df["_interest_income"] = _series_or_zero(df, interest_income_col)
    else:
        rate_col = _first_present(df, ["interest_rate", "tasainteres", "apr"])
        if rate_col:
            rate = pd.to_numeric(df[rate_col], errors="coerce").fillna(0.0)
            df["_interest_income"] = outstanding * rate / 12
        else:
            logger.warning("finance_mart: missing interest rate and interest income columns; defaulting interest_income to 0")
            df["_interest_income"] = 0.0

    if fee_income_col:
        df["_fee_income"] = _series_or_zero(df, fee_income_col)
    else:
        fee_rate_col = _first_present(df, ["origination_fee_rate", "fee_rate"])
        if fee_rate_col:
            fee_rate = pd.to_numeric(df[fee_rate_col], errors="coerce").fillna(0.0)
            df["_fee_income"] = funded * fee_rate
        else:
            df["_fee_income"] = 0.0

    if funding_cost_col:
        df["_funding_cost"] = _series_or_zero(df, funding_cost_col)
    else:
        cof_col = _first_present(df, ["cost_of_funds_rate", "funding_rate"])
        if cof_col:
            cof_rate = pd.to_numeric(df[cof_col], errors="coerce").fillna(0.0)
            df["_funding_cost"] = funded * cof_rate / 12
        else:
            logger.warning("finance_mart: missing funding cost columns; defaulting funding_cost to 0")
            df["_funding_cost"] = 0.0

    if provision_col:
        df["_provision_expense"] = _series_or_zero(df, provision_col)
    else:
        default_flag = _series_or_zero(df, "default_flag")
        lgd = pd.to_numeric(df.get("lgd", pd.Series(0.45, index=df.index)), errors="coerce").fillna(0.45)
        df["_provision_expense"] = default_flag * outstanding * lgd

    grouped = (
        df.groupby("as_of_month", dropna=False)
        .agg(
            interest_income=("_interest_income", "sum"),
            fee_income=("_fee_income", "sum"),
            funding_cost=("_funding_cost", "sum"),
            provision_expense=("_provision_expense", "sum"),
            debt_balance=("outstanding_principal", "sum"),
        )
        .reset_index()
    )

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
