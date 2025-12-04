<<<<<<< HEAD
from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd


=======
import numpy as np
import pandas as pd

>>>>>>> upstream/main
CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
<<<<<<< HEAD
    cleaned = (
        series.astype(str).str.strip()
=======
    if pd.api.types.is_numeric_dtype(series):
        return series

    cleaned = (
        series.astype(str)
        .str.strip()
>>>>>>> upstream/main
        .str.replace(CURRENCY_SYMBOLS, "", regex=True)
        .str.replace(",", "", regex=False)
        .replace({"": np.nan, "nan": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


<<<<<<< HEAD
def calculate_quality_score(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    penalty = df.isna().mean().sum() * 10
    score = max(0, min(100, 100 - penalty))
    return int(round(score))


def _assert_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    if missing := set(required) - set(df.columns):
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")


def portfolio_kpis(df: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
    required = {
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "loan_status",
        "principal_balance",
        "interest_rate",
    }
    _assert_required_columns(df, required)

    work = df.copy()
    work["ltv_ratio"] = np.where(
        work["appraised_value"] > 0,
        (work["loan_amount"] / work["appraised_value"]) * 100,
        np.nan,
    )
    monthly_income = work["borrower_income"] / 12
    work["dti_ratio"] = np.where(
        monthly_income > 0,
        (work["monthly_debt"] / monthly_income) * 100,
        np.nan,
    )

    delinquent_statuses = {"30-59 days past due", "60-89 days past due", "90+ days past due"}
    total_loans = len(work)
    delinquent_count = work["loan_status"].isin(delinquent_statuses).sum()
    delinquency_rate = (delinquent_count / total_loans) * 100 if total_loans else 0.0

    total_principal = work["principal_balance"].sum()
    weighted_interest = (work["interest_rate"] * work["principal_balance"]).sum()
    portfolio_yield = (weighted_interest / total_principal) * 100 if total_principal else 0.0

    metrics = {
        "delinquency_rate": delinquency_rate,
        "portfolio_yield": portfolio_yield,
        "average_ltv": 0.0
        if work.empty
        else float(np.nan_to_num(work["ltv_ratio"].mean(), nan=0.0)),
        "average_dti": 0.0
        if work.empty
        else float(np.nan_to_num(work["dti_ratio"].mean(), nan=0.0)),
    }
    return metrics, work


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loans: float,
    target_loans: float,
    periods: int = 6,
) -> pd.DataFrame:
    if periods < 2:
        raise ValueError("periods must be at least 2 to create a projection range")
    months = pd.date_range(start=pd.Timestamp.now().normalize(), periods=periods, freq="MS")
    projection = pd.DataFrame(
        {
            "month": months,
            "yield": np.linspace(current_yield, target_yield, periods),
            "loan_volume": np.linspace(current_loans, target_loans, periods),
        }
    )
    return projection.assign(month=lambda d: d["month"].dt.strftime("%b %Y"))
=======
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


def _assert_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in df.columns]
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
    enriched["ltv_ratio"] = enriched["loan_amount"] / enriched["appraised_value"]
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

    average_ltv = enriched["ltv_ratio"].mean() if not enriched["ltv_ratio"].empty else 0.0
    average_dti = float(np.nan_to_num(enriched["dti_ratio"].mean(skipna=True), nan=0.0))

    metrics = {
        "delinquency_rate": float(delinquency_rate),
        "portfolio_yield": float(portfolio_yield),
        "average_ltv": float(average_ltv) if not np.isnan(average_ltv) else 0.0,
        "average_dti": average_dti,
    }
    return metrics, enriched
>>>>>>> upstream/main
