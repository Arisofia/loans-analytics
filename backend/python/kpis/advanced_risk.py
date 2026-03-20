from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd

from backend.python.kpis._column_utils import (
    first_matching_column as _first_existing_column,
    resolve_dpd_heuristic,
    to_numeric_safe as _to_numeric,
)
from backend.python.kpis.ssot_asset_quality import calculate_asset_quality_metrics


def _safe_pct(numerator: float | Decimal, denominator: float | Decimal) -> Decimal:
    """Calculate percentage using Decimal for precision. Return as Decimal."""
    num_dec = Decimal(str(numerator)) if isinstance(numerator, float) else Decimal(numerator)
    denom_dec = Decimal(str(denominator)) if isinstance(denominator, float) else Decimal(denominator)
    if denom_dec <= 0:
        return Decimal('0')
    return (num_dec / denom_dec) * Decimal('100')


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
    return resolve_dpd_heuristic(df)


def _build_dpd_bucket(
    bucket_name: str,
    mask: pd.Series,
    balance: pd.Series,
    total_balance: Decimal,
) -> dict[str, float | int | str]:
    bucket_balance = Decimal(str(balance[mask].sum()))
    balance_share = _safe_pct(bucket_balance, total_balance)
    return {
        "bucket": bucket_name,
        "loan_count": int(mask.sum()),
        "balance": round(float(bucket_balance), 2),
        "balance_share_pct": round(float(balance_share), 2),
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


def _status_series(df: pd.DataFrame) -> pd.Series:
    status_col = _first_existing_column(df, ["status", "loan_status", "current_status"])
    if status_col is None:
        return pd.Series(["active"] * len(df), index=df.index, dtype=str)
    return df[status_col].astype(str).str.lower().fillna("active")


def _calculate_ssot_par_metrics(balance: pd.Series, dpd: pd.Series, status: pd.Series) -> dict[str, float]:
    """Calculate PAR metrics via SSOT formula engine and return rounded floats."""
    values = calculate_asset_quality_metrics(
        balance,
        dpd,
        actor="advanced_risk",
        metric_aliases=("par30", "par60", "par90"),
        status=status,
    )
    return {
        "par30": round(values.get("par30", 0.0), 2),
        "par60": round(values.get("par60", 0.0), 2),
        "par90": round(values.get("par90", 0.0), 2),
    }


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
    status = _status_series(df)
    default_mask = _build_default_mask(df, dpd)
    borrower_id = _resolve_identifier(
        df,
        ["borrower_id", "customer_id", "Customer ID_cust", "borrower_name"],
    )
    # Use Decimal for all monetary aggregations
    total_balance = Decimal(str(balance.sum()))
    total_loans = int(len(df))

    try:
        par_metrics = _calculate_ssot_par_metrics(balance, dpd, status)
        par30 = par_metrics["par30"]
        par60 = par_metrics["par60"]
        par90 = par_metrics["par90"]
    except Exception:
        # Compatibility fallback during staged consolidation.
        par30_pct = _safe_pct(Decimal(str(balance[dpd >= 30].sum())), total_balance)
        par60_pct = _safe_pct(Decimal(str(balance[dpd >= 60].sum())), total_balance)
        par90_pct = _safe_pct(Decimal(str(balance[dpd >= 90].sum())), total_balance)
        par30 = round(float(par30_pct), 2)
        par60 = round(float(par60_pct), 2)
        par90 = round(float(par90_pct), 2)
    
    default_count = Decimal(str(default_mask.sum()))
    default_rate_pct = _safe_pct(default_count, Decimal(str(total_loans)))
    default_rate = round(float(default_rate_pct), 2)

    collected = _resolve_series(df, ["last_payment_amount", "payment_amount", "payments_collected"])
    scheduled = _resolve_series(df, ["total_scheduled", "scheduled_amount", "payments_due"])
    collected_sum = Decimal(str(collected.sum()))
    scheduled_sum = Decimal(str(scheduled.sum()))
    collections_coverage_pct = _safe_pct(collected_sum, scheduled_sum)
    collections_coverage = round(float(collections_coverage_pct), 2)

    fee = _resolve_series(df, ["origination_fee", "fee_amount"])
    fee_taxes = _resolve_series(df, ["origination_fee_taxes", "fee_taxes"])
    fee_sum = Decimal(str((fee + fee_taxes).sum()))
    principal_sum = Decimal(str(principal.sum()))
    fee_yield_pct = _safe_pct(fee_sum, principal_sum)
    fee_yield = round(float(fee_yield_pct), 2)
    
    interest_yield_pct = _safe_pct(Decimal(str((interest_rate * balance).sum())), total_balance)
    interest_yield = float(interest_yield_pct)  # Keep as Decimal for addition
    total_yield = round(float(Decimal(str(interest_yield)) + Decimal(str(fee_yield))), 2)

    recovery = _resolve_series(df, ["recovery_value", "Recovery Value", "recovery_amount"])
    default_balance = Decimal(str(balance[default_mask].sum()))
    recovery_sum = Decimal(str(recovery[default_mask].sum())) if default_mask.any() else Decimal(str(recovery.sum()))
    recovery_rate_pct = _safe_pct(recovery_sum, default_balance)
    recovery_rate = round(float(recovery_rate_pct), 2)

    exposure_by_borrower = pd.DataFrame({"borrower_id": borrower_id, "balance": balance})
    exposure_by_borrower = exposure_by_borrower.groupby("borrower_id", dropna=False)[
        "balance"
    ].sum()
    if total_balance > 0 and not exposure_by_borrower.empty:
        shares = exposure_by_borrower / float(total_balance)
        concentration_hhi = round(float((Decimal(str(shares.pow(2).sum())) * Decimal('10000'))), 2)
    else:
        concentration_hhi = 0.0

    loans_per_borrower = borrower_id.value_counts(dropna=False)
    repeat_borrowers = int((loans_per_borrower > 1).sum())
    repeat_borrower_pct = _safe_pct(Decimal(str(repeat_borrowers)), Decimal(str(len(loans_per_borrower))))
    repeat_borrower_rate = round(float(repeat_borrower_pct), 2)

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
