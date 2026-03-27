"""Loan-level features derived from portfolio mart.

Every feature is computed from the canonical DataFrame produced by
``backend.src.marts.builder.build_all_marts`` — no mock data.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

import pandas as pd


def _d(v: Any) -> Decimal:
    try:
        return Decimal(str(v)) if v is not None and str(v) not in ("", "nan", "None") else Decimal(0)
    except Exception:
        return Decimal(0)


def build_loan_features(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Add derived loan-level columns used by agents.

    Returns a *copy* — the original mart is not mutated.
    """
    df = portfolio.copy()

    # DPD bucket
    if "dpd" in df.columns:
        df["dpd_bucket"] = pd.cut(
            pd.to_numeric(df["dpd"], errors="coerce").fillna(0),
            bins=[-1, 0, 30, 60, 90, 180, float("inf")],
            labels=["current", "1-30", "31-60", "61-90", "91-180", "180+"],
        )
    else:
        df["dpd_bucket"] = "current"

    # Utilization ratio (credit_line vs amount)
    if "credit_line" in df.columns and "amount" in df.columns:
        cl = pd.to_numeric(df["credit_line"], errors="coerce").fillna(0)
        amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["utilization_ratio"] = (amt / cl.replace(0, float("nan"))).fillna(0).clip(0, 2)
    else:
        df["utilization_ratio"] = 0.0

    # Days since origination
    if "origination_date" in df.columns:
        orig = pd.to_datetime(df["origination_date"], errors="coerce")
        df["days_since_origination"] = (pd.Timestamp.now() - orig).dt.days.fillna(0).astype(int)
    else:
        df["days_since_origination"] = 0

    # Payment coverage ratio
    if "total_payment_received" in df.columns and "amount" in df.columns:
        pay = pd.to_numeric(df["total_payment_received"], errors="coerce").fillna(0)
        amt = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["payment_coverage"] = (pay / amt.replace(0, float("nan"))).fillna(0)
    else:
        df["payment_coverage"] = 0.0

    # Is government sector (boolean)
    if "government_sector" in df.columns:
        df["is_government"] = df["government_sector"].fillna("").astype(str).str.strip().str.upper().isin(["SI", "YES", "TRUE", "1"])
    else:
        df["is_government"] = False

    return df


def get_feature_summary(features_df: pd.DataFrame) -> Dict[str, Any]:
    """Aggregate feature statistics for agents."""
    summary: Dict[str, Any] = {
        "total_loans": len(features_df),
    }
    if "dpd_bucket" in features_df.columns:
        summary["dpd_distribution"] = features_df["dpd_bucket"].value_counts().to_dict()
    if "utilization_ratio" in features_df.columns:
        summary["avg_utilization"] = float(features_df["utilization_ratio"].mean())
    if "payment_coverage" in features_df.columns:
        summary["avg_payment_coverage"] = float(features_df["payment_coverage"].mean())
    if "is_government" in features_df.columns:
        summary["government_pct"] = float(features_df["is_government"].mean())
    return summary
