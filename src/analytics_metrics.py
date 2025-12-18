<<<<<<< HEAD
from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
    """Normalize numeric-looking series while preserving numeric dtypes."""

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


def calculate_quality_score(df: pd.DataFrame) -> int:
    """Return a 0-100 completeness score for the dataset."""

    if df.empty:
        return 0

    completeness = df.notna().mean().mean()
    score = int(round(completeness * 100))
    return max(0, min(100, score))


def _assert_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")


def portfolio_kpis(df: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
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
        income > 0,
        enriched["monthly_debt"] / (income / 12),
        np.nan,
    )

    total_principal = enriched["principal_balance"].sum()
    delinquent_mask = enriched["loan_status"].astype(str).str.lower().str.contains("delinquent")
    past_due_mask = enriched["loan_status"].astype(str).str.lower().str.contains("past due")
    delinquent_principal = enriched.loc[delinquent_mask | past_due_mask, "principal_balance"].sum()
    delinquency_rate = delinquent_principal / total_principal if total_principal else 0.0

    weighted_interest = (enriched["principal_balance"] * enriched["interest_rate"]).sum()
    portfolio_yield = weighted_interest / total_principal if total_principal else 0.0

    average_ltv = float(np.nanmean(enriched["ltv_ratio"])) if not enriched["ltv_ratio"].empty else 0.0
    if np.isnan(average_ltv):
        average_ltv = 0.0

    average_dti = float(np.nanmean(enriched["dti_ratio"])) if not enriched["dti_ratio"].empty else 0.0
    if np.isnan(average_dti):
        average_dti = 0.0

    metrics = {
        "delinquency_rate": float(delinquency_rate),
        "portfolio_yield": float(portfolio_yield),
        "average_ltv": average_ltv,
        "average_dti": average_dti,
    }
    return metrics, enriched


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loans: float,
    target_loans: float,
    periods: int = 6,
) -> pd.DataFrame:
    if periods < 2:
        raise ValueError("periods must be at least 2")

    months = pd.date_range(start=pd.Timestamp.now().normalize(), periods=periods, freq="MS")
    projection = pd.DataFrame(
        {
            "month": months.strftime("%b %Y"),
            "yield": np.linspace(current_yield, target_yield, periods),
            "loan_volume": np.linspace(current_loans, target_loans, periods),
        }
    )
    return projection
=======
>>>>>>> main
