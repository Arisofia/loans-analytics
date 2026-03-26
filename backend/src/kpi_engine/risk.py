"""Risk metrics — PAR, NPL, expected loss, roll rates, vintage curves.

All computations use real portfolio data from marts.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Basel-style DPD → PD mapping (calibrated to portfolio history)
_DPD_TO_PD: List[tuple] = [
    (0, Decimal("0.005")),
    (30, Decimal("0.05")),
    (60, Decimal("0.15")),
    (90, Decimal("0.35")),
    (180, Decimal("0.70")),
    (999999, Decimal("1.00")),
]

_DEFAULT_LGD = Decimal("0.10")  # 10% from business_parameters.yml


def compute_par(portfolio: pd.DataFrame) -> Dict[str, float]:
    """Compute PAR 1-30, 31-60, 61-90, 90+ from portfolio mart."""
    balance = pd.to_numeric(portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
    dpd = pd.to_numeric(portfolio.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    total = balance.sum()
    if total <= 0:
        return {"par_30": 0.0, "par_60": 0.0, "par_90": 0.0, "total_balance": 0.0}

    return {
        "par_30": float((balance[dpd >= 30].sum() / total) * 100),
        "par_60": float((balance[dpd >= 60].sum() / total) * 100),
        "par_90": float((balance[dpd >= 90].sum() / total) * 100),
        "total_balance": float(total),
    }


def compute_npl(portfolio: pd.DataFrame) -> Dict[str, float]:
    """NPL ratio: dpd >= 30 OR status in (delinquent, defaulted)."""
    balance = pd.to_numeric(portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
    dpd = pd.to_numeric(portfolio.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    status = portfolio.get("status", pd.Series(dtype=str)).str.lower()
    total = balance.sum()
    if total <= 0:
        return {"npl_ratio": 0.0, "npl_balance": 0.0}

    npl_mask = (dpd >= 30) | status.isin(["delinquent", "defaulted"])
    npl_bal = balance[npl_mask].sum()
    return {
        "npl_ratio": float((npl_bal / total) * 100),
        "npl_balance": float(npl_bal),
        "npl_count": int(npl_mask.sum()),
    }


def compute_default_rate(portfolio: pd.DataFrame) -> Dict[str, float]:
    """Default rate by count: defaulted / total."""
    status = portfolio.get("status", pd.Series(dtype=str)).str.lower()
    total = len(portfolio)
    if total == 0:
        return {"default_rate": 0.0}
    defaulted = (status == "defaulted").sum()
    return {
        "default_rate": float((defaulted / total) * 100),
        "defaulted_count": int(defaulted),
        "total_count": total,
    }


def compute_expected_loss(portfolio: pd.DataFrame, lgd: Decimal = _DEFAULT_LGD) -> Dict[str, Any]:
    """Basel EL = PD × LGD × EAD.  PD derived from DPD buckets."""
    dpd = pd.to_numeric(portfolio.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    balance = pd.to_numeric(portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
    status = portfolio.get("status", pd.Series(dtype=str)).str.lower()

    def _dpd_to_pd(d: float, s: str) -> Decimal:
        if s == "defaulted":
            return Decimal("1.0")
        for threshold, pd_val in _DPD_TO_PD:
            if d <= threshold:
                return pd_val
        return Decimal("1.0")

    pds = [_dpd_to_pd(d, s) for d, s in zip(dpd, status)]
    els = [float(pd_val * lgd * Decimal(str(b))) for pd_val, b in zip(pds, balance)]

    total_el = sum(els)
    total_ead = float(balance.sum())
    weighted_pd = float(sum(pds) / len(pds)) * 100 if pds else 0.0

    return {
        "total_expected_loss_usd": round(total_el, 2),
        "expected_loss_rate_pct": round((total_el / total_ead * 100) if total_ead > 0 else 0, 4),
        "weighted_avg_pd_pct": round(weighted_pd, 4),
        "lgd_assumed_pct": float(lgd * 100),
        "total_ead_usd": round(total_ead, 2),
        "loan_count": len(portfolio),
    }


def compute_roll_rates(portfolio: pd.DataFrame) -> Dict[str, Any]:
    """DPD bucket distribution and transition analysis."""
    dpd = pd.to_numeric(portfolio.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    balance = pd.to_numeric(portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)

    buckets = {
        "current": (dpd == 0),
        "1_30": (dpd >= 1) & (dpd <= 30),
        "31_60": (dpd >= 31) & (dpd <= 60),
        "61_90": (dpd >= 61) & (dpd <= 90),
        "91_180": (dpd >= 91) & (dpd <= 180),
        "180_plus": (dpd > 180),
    }

    total_balance = balance.sum()
    distribution = {}
    for name, mask in buckets.items():
        bucket_bal = float(balance[mask].sum())
        distribution[name] = {
            "count": int(mask.sum()),
            "balance": round(bucket_bal, 2),
            "share_pct": round((bucket_bal / total_balance * 100) if total_balance > 0 else 0, 2),
        }

    return {
        "bucket_distribution": distribution,
        "total_portfolio_balance": round(float(total_balance), 2),
    }


def compute_vintage_analysis(portfolio: pd.DataFrame) -> Dict[str, Any]:
    """Vintage analysis — default and delinquency rates by origination cohort."""
    if "origination_date" not in portfolio.columns:
        return {"vintages": [], "summary": "No origination_date available"}

    df = portfolio.copy()
    df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce")
    df = df.dropna(subset=["origination_date"])
    if df.empty:
        return {"vintages": [], "summary": "No valid origination dates"}

    df["vintage"] = df["origination_date"].dt.to_period("M").astype(str)
    dpd = pd.to_numeric(df.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    status = df.get("status", pd.Series(dtype=str)).str.lower()
    balance = pd.to_numeric(df.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)

    vintages = []
    for vintage, group in df.groupby("vintage"):
        g_dpd = pd.to_numeric(group.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
        g_status = group.get("status", pd.Series(dtype=str)).str.lower()
        g_bal = pd.to_numeric(group.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
        n = len(group)
        vintages.append({
            "vintage": str(vintage),
            "loan_count": n,
            "total_balance": round(float(g_bal.sum()), 2),
            "default_rate_pct": round(float((g_status == "defaulted").sum() / n * 100), 2) if n > 0 else 0,
            "par30_rate_pct": round(float((g_dpd >= 30).sum() / n * 100), 2) if n > 0 else 0,
            "avg_dpd": round(float(g_dpd.mean()), 1),
        })

    return {"vintages": vintages, "vintage_count": len(vintages)}


def compute_cost_of_risk(portfolio: pd.DataFrame) -> Dict[str, float]:
    """Cost of Risk = NPL ratio × LGD."""
    npl = compute_npl(portfolio)
    return {
        "cost_of_risk_pct": round(npl["npl_ratio"] * float(_DEFAULT_LGD), 4),
        "npl_ratio_pct": npl["npl_ratio"],
        "lgd_pct": float(_DEFAULT_LGD * 100),
    }


def compute_cure_rate(collections: pd.DataFrame) -> Dict[str, float]:
    """Cure rate: delinquent loans with recent payment / total delinquent."""
    status = collections.get("status", pd.Series(dtype=str)).str.lower()
    delinquent_mask = status.isin(["delinquent"])
    total_delinquent = delinquent_mask.sum()
    if total_delinquent == 0:
        return {"cure_rate_pct": 0.0, "total_delinquent": 0}

    payment = pd.to_numeric(
        collections.get("last_payment_amount", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    cured = ((delinquent_mask) & (payment > 0)).sum()
    return {
        "cure_rate_pct": round(float(cured / total_delinquent * 100), 2),
        "cured_count": int(cured),
        "total_delinquent": int(total_delinquent),
    }
