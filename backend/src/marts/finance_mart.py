from __future__ import annotations

import logging
import pandas as pd

_REQUIRED_BASE_COLUMNS = ("origination_date", "outstanding_principal")
logger = logging.getLogger(__name__)


def _series_or_zero(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return pd.Series(0.0, index=df.index, dtype=float)


def _zero_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series(0.0, index=df.index, dtype=float)


def _first_present(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((col for col in candidates if col in df.columns), None)


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in _REQUIRED_BASE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"finance_mart requires base columns {_REQUIRED_BASE_COLUMNS}. Missing: {missing}"
        )


def _resolve_direct_or_rate(
    df: pd.DataFrame,
    *,
    direct_candidates: list[str],
    rate_candidates: list[str],
    base_amount: pd.Series,
    annualize: bool = False,
    warn_message: str,
) -> pd.Series:
    direct_col = _first_present(df, direct_candidates)
    if direct_col:
        return _series_or_zero(df, direct_col)
    rate_col = _first_present(df, rate_candidates)
    if not rate_col:
        logger.warning(warn_message)
        return _zero_series(df)
    rate = pd.to_numeric(df[rate_col], errors="coerce").fillna(0.0)
    denominator = 12 if annualize else 1
    return base_amount * rate / denominator


def _resolve_interest_income(df: pd.DataFrame, outstanding: pd.Series) -> pd.Series:
    interest_income_col = _first_present(df, ["interest_income", "interest_income_usd"])
    if interest_income_col:
        return _series_or_zero(df, interest_income_col)

    rate_col = _first_present(df, ["interest_rate", "tasainteres", "apr"])
    if not rate_col:
        raise ValueError(
            "finance_mart requires one of [interest_rate, tasainteres, apr] "
            "or an explicit [interest_income, interest_income_usd] column"
        )
    rate = pd.to_numeric(df[rate_col], errors="coerce").fillna(0.0)
    return outstanding * rate / 12


def _resolve_fee_income(df: pd.DataFrame, funded: pd.Series) -> pd.Series:
    return _resolve_direct_or_rate(
        df,
        direct_candidates=["fee_income", "fee_income_usd", "origination_fee"],
        rate_candidates=["origination_fee_rate", "fee_rate"],
        base_amount=funded,
        annualize=False,
        warn_message="finance_mart: missing fee income/rate inputs; defaulting fee income to 0.0",
    )


def _resolve_funding_cost(df: pd.DataFrame, funded: pd.Series) -> pd.Series:
    return _resolve_direct_or_rate(
        df,
        direct_candidates=["funding_cost", "funding_cost_usd", "interest_expense"],
        rate_candidates=["cost_of_funds_rate", "funding_rate"],
        base_amount=funded,
        annualize=True,
        warn_message="finance_mart: missing funding cost/rate inputs; defaulting funding_cost to 0.0",
    )


def _resolve_provision_expense(df: pd.DataFrame, outstanding: pd.Series) -> pd.Series:
    provision_col = _first_present(
        df, ["provision_expense", "provision_expense_usd", "expected_loss"]
    )
    if provision_col:
        return _series_or_zero(df, provision_col)

    default_flag_col = _first_present(df, ["default_flag", "is_default"])
    lgd_col = _first_present(df, ["lgd", "loss_given_default"])
    if not default_flag_col or not lgd_col:
        logger.warning(
            "finance_mart: missing provision/default inputs; defaulting provision_expense to 0.0"
        )
        return _zero_series(df)
    default_flag = pd.to_numeric(df[default_flag_col], errors="coerce").fillna(0.0)
    lgd = pd.to_numeric(df[lgd_col], errors="coerce").fillna(0.0)
    return outstanding * default_flag * lgd


def build_finance_mart(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """Build finance mart from source fields, failing fast when critical financial inputs are missing."""
    df = portfolio_df.copy()
    _validate_required_columns(df)

    df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce")
    if df["origination_date"].isna().all():
        raise ValueError("finance_mart requires at least one valid origination_date value")

    df["as_of_month"] = df["origination_date"].dt.to_period("M").astype(str)

    outstanding = _series_or_zero(df, "outstanding_principal")
    funded = _series_or_zero(df, "funded_amount")

    df["_interest_income"] = _resolve_interest_income(df, outstanding)
    df["_fee_income"] = _resolve_fee_income(df, funded)
    df["_funding_cost"] = _resolve_funding_cost(df, funded)
    df["_provision_expense"] = _resolve_provision_expense(df, outstanding)

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
