from __future__ import annotations

import numpy as np
import pandas as pd
from collections.abc import Iterable

CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(CURRENCY_SYMBOLS, "", regex=True)
        .str.replace(",", "", regex=False)
        .replace({"": np.nan, "nan": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loan_volume: float,
    target_loan_volume: float,
    periods: int = 6,
) -> pd.DataFrame:
    if periods < 2:
        raise ValueError("periods must be at least 2")

    yields = np.linspace(current_yield, target_yield, periods)
    volumes = np.linspace(current_loan_volume, target_loan_volume, periods)
    schedule = pd.date_range(pd.Timestamp.now().normalize(), periods=periods, freq="MS")
    return pd.DataFrame({"date": schedule, "yield": yields, "loan_volume": volumes})


def calculate_quality_score(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    completeness = df.notna().mean().mean()
    return int(round(completeness * 100))


def _assert_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def portfolio_kpis(df: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    required_columns = [
        "loan_amount",
        "appraised_value",
        "monthly_debt",
        "borrower_income",
        "principal_balance",
        "interest_rate",
        "loan_status",
    ]

    if df.empty:
        empty_metrics = {
            "delinquency_rate": 0.0,
            "portfolio_yield": 0.0,
            "average_ltv": 0.0,
            "average_dti": 0.0,
        }
        return empty_metrics, df

    _assert_required_columns(df, required_columns)

    enriched = df.copy()
    enriched["ltv_ratio"] = np.where(
        enriched["appraised_value"] > 0,
        enriched["loan_amount"] / enriched["appraised_value"],
        np.nan,
    )
    income = enriched["borrower_income"]
    enriched["dti_ratio"] = np.where(
        income > 0, enriched["monthly_debt"] / (income / 12), np.nan
    )

    total_principal = enriched["principal_balance"].sum()
    delinquent_principal = enriched.loc[
        enriched["loan_status"].astype(str).str.lower() == "delinquent",
        "principal_balance",
    ].sum()
    delinquency_rate = delinquent_principal / total_principal if total_principal else 0.0

    weighted_interest = (enriched["principal_balance"] * enriched["interest_rate"]).sum()
    portfolio_yield = weighted_interest / total_principal if total_principal else 0.0

    average_ltv = enriched["ltv_ratio"].mean()
    average_dti = float(np.nan_to_num(enriched["dti_ratio"].mean(skipna=True), nan=0.0))

    metrics = {
        "delinquency_rate": float(delinquency_rate),
        "portfolio_yield": float(portfolio_yield),
        "average_ltv": 0.0 if np.isnan(average_ltv) else float(average_ltv),
        "average_dti": average_dti,
    }
    return metrics, enriched
