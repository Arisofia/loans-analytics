"""Quality gates (v2 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class QualityResult:
    completeness: float
    freshness_hours: float


def compute_completeness(df, required_columns: list[str] | None = None) -> float:
    required = required_columns or []
    if not required:
        return 1.0

    try:
        row_count = len(df)
    except Exception:
        return 0.0

    if row_count == 0:
        return 1.0

    missing = 0
    for col in required:
        if not hasattr(df, "columns") or col not in df.columns:
            missing += row_count
            continue

        series = df[col]
        if hasattr(series, "isna"):
            missing += int(series.isna().sum())
        else:
            try:
                missing += sum(value is None for value in series)
            except Exception:
                missing += row_count

    total = row_count * len(required)
    if total <= 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (missing / total)))


def check_referential_integrity(df, key_columns: list[str] | None = None) -> bool:
    cols = key_columns or []
    if not cols:
        return True

    if not hasattr(df, "columns") or any(col not in df.columns for col in cols):
        return False

    try:
        if len(df) == 0:
            return True
        subset = df[cols]
        if hasattr(subset, "isna") and bool(subset.isna().any().any()):
            return False
        if hasattr(df, "duplicated") and bool(df.duplicated(subset=cols).any()):
            return False
    except Exception:
        return False

    return True


def compute_freshness_hours(as_of: datetime, now: datetime | None = None) -> float:
    now_dt = now or datetime.now(timezone.utc)
    delta = now_dt - as_of
    return delta.total_seconds() / 3600.0
