from __future__ import annotations

import pandas as pd

from python.validation import safe_numeric


_PRIMARY_REQUIRED_COLUMNS = ["dpd_90_plus_usd", "total_receivable_usd"]
_FALLBACK_REQUIRED_COLUMNS = ["days_past_due", "outstanding_balance"]
_TOTAL_EXPOSURE_CANDIDATES = ["total_receivable_usd", "principal_amount", "amount", "loan_amount"]


def _validate_series(series: pd.Series, label: str) -> None:
    if series.isna().any():
        raise ValueError(f"{label} contains invalid values")
    if (series < 0).any():
        raise ValueError(f"{label} contains negative values")


def _calculate_primary(df: pd.DataFrame) -> float:
    dpd_90_plus = safe_numeric(df["dpd_90_plus_usd"])
    total_receivable = safe_numeric(df["total_receivable_usd"])

    _validate_series(dpd_90_plus, "dpd_90_plus_usd")
    _validate_series(total_receivable, "total_receivable_usd")

    total_receivable_sum = total_receivable.sum()
    if total_receivable_sum == 0:
        return 0.0

    par_90 = dpd_90_plus.sum() / total_receivable_sum * 100.0
    return round(float(par_90), 2)


def _calculate_fallback(df: pd.DataFrame) -> float:
    days_past_due = safe_numeric(df["days_past_due"])
    outstanding_balance = safe_numeric(df["outstanding_balance"])

    _validate_series(days_past_due, "days_past_due")
    _validate_series(outstanding_balance, "outstanding_balance")

    total_exposure = None
    for col in _TOTAL_EXPOSURE_CANDIDATES:
        if col in df.columns:
            total_exposure = safe_numeric(df[col])
            _validate_series(total_exposure, col)
            break

    if total_exposure is None:
        total_exposure = outstanding_balance

    exposure_sum = total_exposure.sum()
    if exposure_sum == 0:
        return 0.0

    par_90_balance = outstanding_balance[days_past_due >= 90].sum()
    par_90 = par_90_balance / exposure_sum * 100.0
    return round(float(par_90), 2)


def calculate_par_90(df: pd.DataFrame | None) -> float:
    if df is None or df.shape[0] == 0:
        return 0.0

    has_primary = all(col in df.columns for col in _PRIMARY_REQUIRED_COLUMNS)
    if has_primary:
        return _calculate_primary(df)

    has_fallback = all(col in df.columns for col in _FALLBACK_REQUIRED_COLUMNS)
    if has_fallback:
        return _calculate_fallback(df)

    missing = [
        col
        for col in _PRIMARY_REQUIRED_COLUMNS
        if col not in df.columns
    ]
    raise ValueError("Missing required columns for PAR 90 calculation: " + ", ".join(missing))
