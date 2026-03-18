from __future__ import annotations

from decimal import Decimal

import pandas as pd

from backend.python.validation import safe_decimal, validate_numeric_bounds


def calculate_par_30(df: pd.DataFrame | None) -> Decimal:
    """
    Calculate Portfolio at Risk (30+ days) as a percentage of receivables.
    Formula: SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable) * 100
    Returns 0.0 if input is empty or total receivable is zero.
    Raises ValueError if required columns are missing.
    Negative receivables are not allowed.
    """
    if df is None or df.shape[0] == 0:
        return Decimal("0.00")
    # Validate required columns
    required = [
        "dpd_30_60_usd",
        "dpd_60_90_usd",
        "dpd_90_plus_usd",
        "total_receivable_usd",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns for PAR 30 calculation: " f"{', '.join(missing)}"
        )
    # Validate non-negative receivables
    bounds = validate_numeric_bounds(df, columns=["total_receivable_usd"])
    if not bounds.get("total_receivable_usd_non_negative", True):
        raise ValueError("Negative receivable amounts detected.")

    dpd_30_60 = sum(safe_decimal(val) for val in df["dpd_30_60_usd"])
    dpd_60_90 = sum(safe_decimal(val) for val in df["dpd_60_90_usd"])
    dpd_90_plus = sum(safe_decimal(val) for val in df["dpd_90_plus_usd"])
    total_receivable = sum(safe_decimal(val) for val in df["total_receivable_usd"])

    if total_receivable == 0:
        return Decimal("0.00")

    par_30 = (dpd_30_60 + dpd_60_90 + dpd_90_plus) / total_receivable * Decimal("100.0")
    # Standardize to 2 decimal places
    return par_30.quantize(Decimal("0.01"))
