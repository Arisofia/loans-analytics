from __future__ import annotations

import numpy as np
import pandas as pd

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
