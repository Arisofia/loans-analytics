from __future__ import annotations

import pandas as pd

from python.validation import safe_numeric


_REQUIRED_COLUMNS = ["dpd_90_plus_usd", "total_receivable_usd"]


def _validate_series(series: pd.Series, label: str) -> None:
    if series.isna().any():
        raise ValueError(f"{label} contains invalid values")
    if (series < 0).any():
        raise ValueError(f"{label} contains negative values")


def calculate_par_90(df: pd.DataFrame | None) -> float:
    if df is None or df.shape[0] == 0:
        return 0.0

    missing = [col for col in _REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns for PAR 90 calculation: " + ", ".join(missing)
        )

    dpd_90_plus = safe_numeric(df["dpd_90_plus_usd"])
    total_receivable = safe_numeric(df["total_receivable_usd"])

    _validate_series(dpd_90_plus, "dpd_90_plus_usd")
    _validate_series(total_receivable, "total_receivable_usd")

    total_receivable_sum = total_receivable.sum()
    if total_receivable_sum == 0:
        return 0.0

    par_90 = dpd_90_plus.sum() / total_receivable_sum * 100.0
    return round(float(par_90), 2)
