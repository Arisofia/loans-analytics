from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

# DPD bucket boundaries (inclusive lower, exclusive upper)
_DPD_BUCKETS = [
    ("current", 0, 1),
    ("1_30", 1, 31),
    ("31_60", 31, 61),
    ("61_90", 61, 91),
    ("90_plus", 91, None),
]

_TRANSITIONS = [
    ("current_to_1_30", "current", "1_30"),
    ("1_30_to_31_60", "1_30", "31_60"),
    ("31_60_to_61_90", "31_60", "61_90"),
    ("61_90_to_90_plus", "61_90", "90_plus"),
]


def _assign_dpd_bucket(dpd_series: pd.Series) -> pd.Series:
    """Return a bucket label string for each DPD value."""
    dpd = pd.to_numeric(dpd_series, errors="coerce").fillna(0).clip(lower=0)
    result = pd.Series("current", index=dpd.index, dtype=str)
    for label, lo, hi in _DPD_BUCKETS:
        mask = dpd >= lo if hi is None else (dpd >= lo) & (dpd < hi)
        result[mask] = label
    return result


def compute_roll_rates(
    portfolio_t0: pd.DataFrame,
    portfolio_t1: Optional[pd.DataFrame] = None,
    loan_id_col: str = "loan_id",
    dpd_col: str = "days_past_due",
    balance_col: str = "outstanding_principal",
) -> Dict[str, Any]:
    """Compute DPD bucket distribution and roll-rate migration matrix.

    When only ``portfolio_t0`` is provided the function returns the balance
    breakdown by DPD bucket (snapshot metrics).  When ``portfolio_t1`` is also
    supplied, a balance-weighted transition matrix is computed showing the
    percentage of each bucket's balance that migrated to another bucket between
    the two observation dates.

    Parameters
    ----------
    portfolio_t0:
        Portfolio snapshot at period T0.  Must contain ``loan_id_col``,
        ``dpd_col`` and ``balance_col``.
    portfolio_t1:
        Portfolio snapshot at period T1 (one period later).  Must share the
        same ``loan_id_col`` as ``portfolio_t0``.
    loan_id_col:
        Primary key column present in both snapshots.
    dpd_col:
        Days-past-due column name.
    balance_col:
        Outstanding principal / balance column name.

    Returns
    -------
    dict with keys:
    - ``bucket_distribution``: per-bucket balance and share (from T0)
    - ``roll_rate_matrix``: transition info per bucket pair (only when T1 given)
    - ``snapshot_only``: True when no T1 was provided
    """
    if portfolio_t0.empty:
        return {"bucket_distribution": {}, "roll_rate_matrix": {}, "snapshot_only": True}

    # ── Bucket distribution from T0 ─────────────────────────────────────────
    df0 = portfolio_t0[[loan_id_col, dpd_col, balance_col]].copy()
    df0[balance_col] = pd.to_numeric(df0[balance_col], errors="coerce").fillna(0)
    df0["_bucket"] = _assign_dpd_bucket(df0[dpd_col])

    bucket_totals = df0.groupby("_bucket")[balance_col].sum()
    total_balance = float(bucket_totals.sum()) or 1.0

    bucket_distribution: Dict[str, Any] = {}
    for label, _lo, _hi in _DPD_BUCKETS:
        bal = float(bucket_totals.get(label, 0.0))
        bucket_distribution[label] = {
            "balance_usd": round(bal, 2),
            "pct_of_portfolio": round(bal / total_balance * 100, 2),
        }

    # ── Roll-rate matrix (requires T1) ──────────────────────────────────────
    roll_rate_matrix: Dict[str, Any] = {}
    snapshot_only = portfolio_t1 is None or portfolio_t1.empty

    if not snapshot_only:
        if portfolio_t1 is None:
            raise ValueError("portfolio_t1 is None")
        df1 = portfolio_t1[[loan_id_col, dpd_col, balance_col]].copy()
        df1[balance_col] = pd.to_numeric(df1[balance_col], errors="coerce").fillna(0)
        df1["_bucket_t1"] = _assign_dpd_bucket(df1[dpd_col])

        df0 = df0.rename(columns={balance_col: "_bal_t0", "_bucket": "_bucket_t0"})
        df1 = df1.rename(columns={balance_col: "_bal_t1"})
        merged = df0.merge(df1[[loan_id_col, "_bucket_t1", "_bal_t1"]], on=loan_id_col, how="inner")

        for transition_key, from_bucket, to_bucket in _TRANSITIONS:
            from_mask = merged["_bucket_t0"] == from_bucket
            from_bal = float(merged.loc[from_mask, "_bal_t0"].sum())
            moved_mask = from_mask & (merged["_bucket_t1"] == to_bucket)
            to_bal = float(merged.loc[moved_mask, "_bal_t1"].sum())

            roll_rate_matrix[transition_key] = {
                "from_bucket": from_bucket,
                "to_bucket": to_bucket,
                "from_balance": round(from_bal, 2),
                "to_balance": round(to_bal, 2),
                "roll_rate_pct": round(to_bal / from_bal * 100, 2) if from_bal > 0 else 0.0,
            }

    return {
        "bucket_distribution": bucket_distribution,
        "roll_rate_matrix": roll_rate_matrix,
        "snapshot_only": snapshot_only,
        "total_portfolio_balance_usd": round(total_balance, 2),
    }


def build_cohort_default_curve(portfolio_mart: pd.DataFrame) -> pd.DataFrame:
    if portfolio_mart.empty:
        return pd.DataFrame(columns=["cohort", "default_rate"])
    return (
        portfolio_mart.groupby("cohort", dropna=False)["default_flag"]
        .mean()
        .reset_index(name="default_rate")
    )


def build_vintage_quality_summary(portfolio_mart: pd.DataFrame) -> pd.DataFrame:
    if portfolio_mart.empty:
        return pd.DataFrame(columns=["vintage", "par30_proxy"])
    return (
        portfolio_mart.assign(par30_flag=portfolio_mart["days_past_due"].fillna(0) >= 30)
        .groupby("vintage", dropna=False)["par30_flag"]
        .mean()
        .reset_index(name="par30_proxy")
    )
