from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

# Re-exporting real implementations from src/analytics package
from src.analytics import (calculate_quality_score, portfolio_kpis,
                           project_growth, standardize_numeric)

ROOT = tuple(Path(__file__).resolve().parents)[1]
DASHBOARD_JSON = ROOT / "exports" / "complete_kpi_dashboard.json"

from python.config import settings

CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
    """View Visual"""

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
    """View Visual"""

    if df.empty:
        return 0

    completeness = 1 - df.isna().mean().mean()
    return int(round(max(0.0, min(1.0, completeness)) * 100))


def load_dashboard_metrics() -> Dict[str, Any]:
    """Load dashboard metrics from JSON file."""
    if not DASHBOARD_JSON.exists():
        return {}
    try:
        with open(DASHBOARD_JSON, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}


def get_growth_metrics() -> Dict[str, Any]:
    """Get growth metrics from dashboard."""
    data = load_dashboard_metrics()
    return data.get("growth_metrics", {})


def portfolio_kpis(df: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
    """View Visual"""

    required = set(settings.analytics.required_columns)

    if df.empty:
        empty_metrics: Dict[str, float] = {
            "delinquency_rate": 0.0,
            "portfolio_yield": 0.0,
            "average_ltv": 0.0,
            "average_dti": 0.0,
        }
        return empty_metrics, df

    _assert_required_columns(df, required)

    work = df.copy()
    work["ltv_ratio"] = np.where(
        work["appraised_value"] > 0,
        work["loan_amount"] / work["appraised_value"],
        np.nan,
    )
    monthly_income = work["borrower_income"] / 12
    work["dti_ratio"] = np.where(
        monthly_income > 0,
        work["monthly_debt"] / monthly_income,
        np.nan,
    )

    delinquent_statuses = settings.analytics.delinquent_statuses
    total_principal = work["principal_balance"].sum()
    if total_principal > 0:
        delinquent_mask = (
            work["loan_status"].astype(str).str.lower().isin(delinquent_statuses)
        )
        delinquent_principal = work.loc[delinquent_mask, "principal_balance"].sum()
        delinquency_rate = float(delinquent_principal / total_principal)
    else:
        delinquency_rate = 0.0

    weighted_interest = (work["interest_rate"] * work["principal_balance"]).sum()
    portfolio_yield = (
        float(weighted_interest / total_principal) if total_principal else 0.0
    )

    avg_ltv = work["ltv_ratio"].mean()
    avg_dti = work["dti_ratio"].mean()

    metrics = {
        "delinquency_rate": delinquency_rate,
        "portfolio_yield": portfolio_yield,
        "average_ltv": float(avg_ltv) if pd.notna(avg_ltv) else 0.0,
        "average_dti": float(avg_dti) if pd.notna(avg_dti) else 0.0,
    }
    return metrics, work


def _assert_required_columns(df: pd.DataFrame, required: set) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loan_volume: float,
    target_loan_volume: float,
    periods: int = 6,
) -> pd.DataFrame:
    """Project portfolio yield and loan volume over a monthly horizon."""

    if periods < 2:
        raise ValueError("periods must be at least 2 to create a projection range")

    schedule = pd.date_range(pd.Timestamp.now().normalize(), periods=periods, freq="MS")
    projection = pd.DataFrame(
        {
            "month": schedule,
            "yield": np.linspace(current_yield, target_yield, periods),
            "loan_volume": np.linspace(
                current_loan_volume, target_loan_volume, periods
            ),
        }
    )
    return projection.assign(month=lambda d: d["month"].dt.strftime("%b %Y"))
