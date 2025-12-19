from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd

from python.analytics import (
  calculate_quality_score as _calculate_quality_score,
  portfolio_kpis as _portfolio_kpis,
  project_growth as _project_growth,
  standardize_numeric as _standardize_numeric,
)


CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
    """Compatibility wrapper around python.analytics.safe_numeric."""
    return _standardize_numeric(series)


def calculate_quality_score(df: pd.DataFrame) -> float:
    """Return completeness score between 0 and 100."""
    return _calculate_quality_score(df)


def portfolio_kpis(df: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Delegate KPI calculation to the consolidated analytics module."""
    return _portfolio_kpis(df)


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loan_volume: float,
    target_loan_volume: float,
    periods: int = 6,
) -> pd.DataFrame:
    """Generate a simple growth projection for dashboard visualizations."""
    return _project_growth(
        current_yield=current_yield,
        target_yield=target_yield,
        current_loan_volume=current_loan_volume,
        target_loan_volume=target_loan_volume,
        periods=periods,
    )
