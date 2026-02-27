from __future__ import annotations

from typing import Any

import pandas as pd


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _to_numeric(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


def _normalize_interest_rate(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    clean = series.copy()
    # Support both decimal (0.35) and percentage (35.0) formats.
    median = clean.median()
    if pd.notna(median) and median > 1.0:
        clean = clean / 100.0
    return clean


def _extract_dpd(df: pd.DataFrame) -> pd.Series:
    dpd_col = _first_existing_column(df, ["days_past_due", "dpd", "dpd_days"])
    if dpd_col:
        return _to_numeric(df[dpd_col]).clip(lower=0)

    status_col = _first_existing_column(df, ["loan_status", "status", "current_status"])
    if not status_col:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)

    status = df[status_col].astype(str).str.lower()
    dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
    dpd = dpd.mask(status.str.contains(r"90\+|default|charged", regex=True, na=False), 100.0)
    dpd = dpd.mask(status.str.contains(r"60-89|60\+", regex=True, na=False), 75.0)
    dpd = dpd.mask(status.str.contains(r"30-59|30\+", regex=True, na=False), 45.0)
    return dpd


def _build_dpd_bucket(
    bucket_name: str,
    mask: pd.Series,
    balance: pd.Series,
    total_balance: float,
) -> dict[str, float | int | str]:
    bucket_balance = float(balance[mask].sum())
    return {
        "bucket": bucket_name,
        "loan_count": int(mask.sum()),
        "balance": round(bucket_balance, 2),
        "balance_share_pct": round(_safe_pct(bucket_balance, total_balance), 2),
    }


def _build_default_mask(df: pd.DataFrame, dpd: pd.Series) -> pd.Series:
    status_col = _first_existing_column(df, ["loan_status", "status", "current_status"])
    if status_col:
        status = df[status_col].astype(str).str.lower()
        return status.str.contains(r"default|charged", regex=True, na=False)
    return dpd > 90


def _resolve_series(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    col = _first_existing_column(df, candidates)
    if col is None:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return _to_numeric(df[col])


def _resolve_identifier(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    col = _first_existing_column(df, candidates)
    if col is not None:
        return df[col].astype(str).fillna("")
    loan_col = _first_existing_column(df, ["loan_id", "id"])
    if loan_col is not None:
        return df[loan_col].astype(str).fillna("")
    return pd.Series([f"loan-{idx + 1}" for idx in range(len(df))], index=df.index)


def _build_credit_quality_index(df: pd.DataFrame) -> float:
    score_col = _first_existing_column(df, ["credit_score", "equifax_score", "Equifax Score"])
    if not score_col:
        return 0.0

    scores = _to_numeric(df[score_col])
    scores = scores[scores > 0]
    if scores.empty:
        return 0.0

    avg_score = float(scores.mean())
    quality_index = ((avg_score - 300.0) / 550.0) * 100.0
    return round(max(0.0, min(100.0, quality_index)), 2)


def calculate_advanced_risk_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "par30": 0.0,
            "par60": 0.0,
            "par90": 0.0,
            "default_rate": 0.0,
            "collections_coverage": 0.0,
            "fee_yield": 0.0,
            "total_yield": 0.0,
            "recovery_rate": 0.0,
            "concentration_hhi": 0.0,
            "repeat_borrower_rate": 0.0,
            "credit_quality_index": 0.0,
            "total_loans": 0,
            "dpd_buckets": [],
        }

    balance = _resolve_series(
        df,
        [
            "principal_balance",
            "outstanding_balance",
            "outstanding_loan_value",
            "amount",
            "principal_amount",
            "loan_amount",
        ],
    )
    principal = _resolve_series(df, ["loan_amount", "principal_amount", "amount"])
    interest_rate = _normalize_interest_rate(
        _resolve_series(df, ["interest_rate", "interest_rate_apr"])
    )
    dpd = _extract_dpd(df)
    default_mask = _build_default_mask(df, dpd)
    borrower_id = _resolve_identifier(
        df,
        ["borrower_id", "customer_id", "Customer ID_cust", "borrower_name"],
    )
    total_balance = float(balance.sum())
    total_loans = int(len(df))

    par30 = round(_safe_pct(float(balance[dpd > 30].sum()), total_balance), 2)
    par60 = round(_safe_pct(float(balance[dpd > 60].sum()), total_balance), 2)
    par90 = round(_safe_pct(float(balance[dpd > 90].sum()), total_balance), 2)
    default_rate = round(_safe_pct(float(default_mask.sum()), float(total_loans)), 2)

    collected = _resolve_series(df, ["last_payment_amount", "payment_amount", "payments_collected"])
    scheduled = _resolve_series(df, ["total_scheduled", "scheduled_amount", "payments_due"])
    collections_coverage = round(_safe_pct(float(collected.sum()), float(scheduled.sum())), 2)

    fee = _resolve_series(df, ["origination_fee", "fee_amount"])
    fee_taxes = _resolve_series(df, ["origination_fee_taxes", "fee_taxes"])
    fee_yield = round(_safe_pct(float((fee + fee_taxes).sum()), float(principal.sum())), 2)
    interest_yield = _safe_pct(float((interest_rate * balance).sum()), total_balance)
    total_yield = round(interest_yield + fee_yield, 2)

    recovery = _resolve_series(df, ["recovery_value", "Recovery Value", "recovery_amount"])
    default_balance = float(balance[default_mask].sum())
    recovery_numerator = (
        float(recovery[default_mask].sum()) if default_mask.any() else float(recovery.sum())
    )
    recovery_rate = round(_safe_pct(recovery_numerator, default_balance), 2)

    exposure_by_borrower = pd.DataFrame({"borrower_id": borrower_id, "balance": balance})
    exposure_by_borrower = exposure_by_borrower.groupby("borrower_id", dropna=False)[
        "balance"
    ].sum()
    if total_balance > 0 and not exposure_by_borrower.empty:
        shares = exposure_by_borrower / total_balance
        concentration_hhi = round(float((shares.pow(2).sum()) * 10000.0), 2)
    else:
        concentration_hhi = 0.0

    loans_per_borrower = borrower_id.value_counts(dropna=False)
    repeat_borrowers = int((loans_per_borrower > 1).sum())
    repeat_borrower_rate = round(
        _safe_pct(float(repeat_borrowers), float(len(loans_per_borrower))), 2
    )

    dpd_buckets = [
        _build_dpd_bucket("current", dpd <= 0, balance, total_balance),
        _build_dpd_bucket("1_30", (dpd > 0) & (dpd <= 30), balance, total_balance),
        _build_dpd_bucket("31_60", (dpd > 30) & (dpd <= 60), balance, total_balance),
        _build_dpd_bucket("61_90", (dpd > 60) & (dpd <= 90), balance, total_balance),
        _build_dpd_bucket("90_plus", dpd > 90, balance, total_balance),
    ]

    return {
        "par30": par30,
        "par60": par60,
        "par90": par90,
        "default_rate": default_rate,
        "collections_coverage": collections_coverage,
        "fee_yield": fee_yield,
        "total_yield": total_yield,
        "recovery_rate": recovery_rate,
        "concentration_hhi": concentration_hhi,
        "repeat_borrower_rate": repeat_borrower_rate,
        "credit_quality_index": _build_credit_quality_index(df),
        "total_loans": total_loans,
        "dpd_buckets": dpd_buckets,
    }
