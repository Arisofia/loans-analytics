from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd

from python.validation import find_column, safe_numeric

_COLLECTED_CANDIDATES = [
    "payments_collected_usd",
    "payments_collected",
    "collections_usd",
    "collection_amount_usd",
    "collection_amount",
    "amount_collected",
    "total_collected_usd",
    "total_collected",
    "cash_collected_usd",
    "cash_collected",
]
_DUE_CANDIDATES = [
    "payments_due_usd",
    "payments_due",
    "amount_due",
    "total_due_usd",
    "total_due",
    "scheduled_payment_usd",
    "scheduled_payment",
    "expected_payment_usd",
    "expected_payment",
    "total_receivable_usd",
    "total_receivable",
]


def _validate_series(series: pd.Series, label: str) -> None:
    if series.isna().any():
        raise ValueError(f"{label} contains invalid values")
    if (series < 0).any():
        raise ValueError(f"{label} contains negative values")


def calculate_collection_rate(df: pd.DataFrame | None) -> Tuple[float, Dict[str, Any]]:
    if df is None or df.shape[0] == 0:
        return 0.0, {"rows_processed": 0, "calculation_status": "empty_input"}

    collected_col = find_column(df, _COLLECTED_CANDIDATES)
    due_col = find_column(df, _DUE_CANDIDATES)

    missing = [
        name
        for name, column in (
            ("payments_collected", collected_col),
            ("payments_due", due_col),
        )
        if column is None
    ]
    if missing:
        return 0.0, {
            "rows_processed": len(df),
            "calculation_status": "missing_columns",
            "missing_columns": missing,
        }

    collected_series = safe_numeric(df[collected_col])
    due_series = safe_numeric(df[due_col])

    _validate_series(collected_series, collected_col)
    _validate_series(due_series, due_col)

    collected_total = collected_series.sum()
    due_total = due_series.sum()

    if due_total == 0:
        return 0.0, {
            "rows_processed": len(df),
            "collected_column": collected_col,
            "due_column": due_col,
            "calculation_status": "zero_due",
        }

    value = collected_total / due_total * 100.0
    return (
        round(float(value), 2),
        {
            "rows_processed": len(df),
            "collected_column": collected_col,
            "due_column": due_col,
            "collected_total": float(collected_total),
            "due_total": float(due_total),
        },
    )
