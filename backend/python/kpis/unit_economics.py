"""Unit economics and advanced credit quality KPIs.

Provides compute functions for metrics not covered by the existing
advanced_risk / catalog_processor modules:

- NPL ratio     : Non-performing loan balance as % of total portfolio
- LGD           : Loss Given Default (1 - recovery_rate)
- Cost of Risk  : Expected credit loss % = NPL * LGD / 100
- NIM           : Net Interest Margin (gross yield - funding cost)
- Payback Period: CAC recovery time = CAC / monthly_ARPU
- Cure Rate     : Proxy % of delinquent loans showing payment activity
- DPD Migration : Bucket distribution with action recommendation
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from python.logging_config import get_logger

logger = get_logger(__name__)


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 4)


def _resolve_balance(df: pd.DataFrame) -> pd.Series:
    col = _first_col(
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
    if col is None:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    return _to_num(df[col])


def _resolve_dpd(df: pd.DataFrame) -> pd.Series:
    dpd_col = _first_col(df, ["days_past_due", "dpd", "dpd_days"])
    if dpd_col:
        return _to_num(df[dpd_col]).clip(lower=0)
    status_col = _first_col(df, ["loan_status", "status", "current_status"])
    if not status_col:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    status = df[status_col].astype(str).str.lower()
    dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
    dpd = dpd.mask(status.str.contains(r"90\+|default|charged", regex=True, na=False), 100.0)
    dpd = dpd.mask(status.str.contains(r"60-89|60\+", regex=True, na=False), 75.0)
    dpd = dpd.mask(status.str.contains(r"30-59|30\+", regex=True, na=False), 45.0)
    return dpd


def _resolve_default_mask(df: pd.DataFrame, dpd: pd.Series) -> pd.Series:
    status_col = _first_col(df, ["loan_status", "status", "current_status"])
    mask = dpd > 90
    if status_col:
        status = df[status_col].astype(str).str.lower()
        mask = mask | status.str.contains(r"default|charged|90\+", regex=True, na=False)
    return mask


def calculate_npl_ratio(df: pd.DataFrame) -> dict[str, Any]:
    """Non-Performing Loan ratio.

    NPL = SUM(balance WHERE dpd > 90 OR status = default) / SUM(total_balance) * 100

    Returns dict with npl_ratio, npl_balance, total_balance, npl_loan_count, formula.
    """
    if df.empty:
        return {
            "npl_ratio": 0.0,
            "npl_balance": 0.0,
            "total_balance": 0.0,
            "npl_loan_count": 0,
            "formula": "SUM(balance WHERE dpd > 90 OR status = default) / SUM(balance) * 100",
        }

    balance = _resolve_balance(df)
    dpd = _resolve_dpd(df)
    default_mask = _resolve_default_mask(df, dpd)
    npl_mask = (dpd > 90) | default_mask

    total_balance = float(balance.sum())
    npl_balance = float(balance[npl_mask].sum())
    npl_loan_count = int(npl_mask.sum())
    npl_ratio = _safe_pct(npl_balance, total_balance)

    logger.debug("NPL ratio=%.4f%%, balance=%.2f, count=%d", npl_ratio, npl_balance, npl_loan_count)
    return {
        "npl_ratio": npl_ratio,
        "npl_balance": round(npl_balance, 2),
        "total_balance": round(total_balance, 2),
        "npl_loan_count": npl_loan_count,
        "formula": "SUM(balance WHERE dpd > 90 OR status = default) / SUM(balance) * 100",
    }


def calculate_lgd(df: pd.DataFrame) -> dict[str, Any]:
    """Loss Given Default.

    LGD = (defaulted_balance - recovered_amount) / defaulted_balance * 100
         = (1 - recovery_rate) * 100

    Returns dict with lgd_pct, recovery_rate_pct, defaulted_balance, recovered_amount, formula.
    """
    empty_result: dict[str, Any] = {
        "lgd_pct": 0.0,
        "recovery_rate_pct": 0.0,
        "defaulted_balance": 0.0,
        "recovered_amount": 0.0,
        "formula": "(defaulted_balance - recovered_amount) / defaulted_balance * 100",
    }
    if df.empty:
        return empty_result

    balance = _resolve_balance(df)
    dpd = _resolve_dpd(df)
    default_mask = _resolve_default_mask(df, dpd)
    defaulted_balance = float(balance[default_mask].sum())

    if defaulted_balance <= 0:
        return empty_result

    recovery_col = _first_col(df, ["recovery_value", "Recovery Value", "recovery_amount"])
    if recovery_col:
        recovery = _to_num(df[recovery_col])
        recovered = float(recovery[default_mask].sum())
    else:
        collected_col = _first_col(df, ["last_payment_amount", "payment_amount"])
        recovered = float(_to_num(df[collected_col])[default_mask].sum()) if collected_col else 0.0

    recovery_rate = _safe_pct(recovered, defaulted_balance)
    lgd = max(0.0, round(100.0 - recovery_rate, 4))

    logger.debug("LGD=%.4f%%, recovery_rate=%.4f%%", lgd, recovery_rate)
    return {
        "lgd_pct": lgd,
        "recovery_rate_pct": round(recovery_rate, 4),
        "defaulted_balance": round(defaulted_balance, 2),
        "recovered_amount": round(recovered, 2),
        "formula": "(defaulted_balance - recovered_amount) / defaulted_balance * 100",
    }


def calculate_cost_of_risk(df: pd.DataFrame) -> dict[str, Any]:
    """Cost of Risk (CoR).

    CoR = NPL_ratio * LGD / 100
    Represents expected credit loss as a % of total portfolio balance.

    Returns dict with cost_of_risk_pct, npl_ratio, lgd_pct, expected_loss_balance, formula.
    """
    if df.empty:
        return {
            "cost_of_risk_pct": 0.0,
            "npl_ratio": 0.0,
            "lgd_pct": 0.0,
            "expected_loss_balance": 0.0,
            "formula": "NPL_ratio * LGD / 100",
        }

    npl_data = calculate_npl_ratio(df)
    lgd_data = calculate_lgd(df)
    npl_ratio = npl_data["npl_ratio"]
    lgd_pct = lgd_data["lgd_pct"]
    cor = round((npl_ratio * lgd_pct) / 100.0, 4)

    logger.debug("Cost of Risk=%.4f%%, NPL=%.4f%%, LGD=%.4f%%", cor, npl_ratio, lgd_pct)
    return {
        "cost_of_risk_pct": cor,
        "npl_ratio": npl_ratio,
        "lgd_pct": lgd_pct,
        "expected_loss_balance": round(npl_data["total_balance"] * cor / 100.0, 2),
        "formula": "NPL_ratio * LGD / 100",
    }


def calculate_nim(df: pd.DataFrame, funding_cost_rate: float = 0.08) -> dict[str, Any]:
    """Net Interest Margin.

    NIM = (Weighted Interest Income Rate - Funding Cost Rate) * 100
    funding_cost_rate: annualized cost of funds as decimal (default 8%).

    Returns dict with nim_pct, gross_yield_pct, funding_cost_pct, interest_income,
    total_balance, formula.
    """
    funding_cost_pct = round(funding_cost_rate * 100.0, 4)
    if df.empty:
        return {
            "nim_pct": 0.0,
            "gross_yield_pct": 0.0,
            "funding_cost_pct": funding_cost_pct,
            "interest_income": 0.0,
            "total_balance": 0.0,
            "formula": "(gross_yield_rate - funding_cost_rate) * 100",
        }

    balance = _resolve_balance(df)
    total_balance = float(balance.sum())
    if total_balance <= 0:
        return {
            "nim_pct": 0.0,
            "gross_yield_pct": 0.0,
            "funding_cost_pct": funding_cost_pct,
            "interest_income": 0.0,
            "total_balance": 0.0,
            "formula": "(gross_yield_rate - funding_cost_rate) * 100",
        }

    rate_col = _first_col(df, ["interest_rate", "interest_rate_apr"])
    if rate_col:
        rates = _to_num(df[rate_col])
        median_rate = float(rates[rates > 0].median()) if (rates > 0).any() else 0.0
        if median_rate > 1.0:
            rates = rates / 100.0
        interest_income = float((rates * balance).sum())
    else:
        interest_income = 0.0

    gross_yield = _safe_pct(interest_income, total_balance)
    nim = round(gross_yield - funding_cost_pct, 4)

    logger.debug(
        "NIM=%.4f%%, gross_yield=%.4f%%, funding_cost=%.4f%%",
        nim,
        gross_yield,
        funding_cost_pct,
    )
    return {
        "nim_pct": nim,
        "gross_yield_pct": round(gross_yield, 4),
        "funding_cost_pct": funding_cost_pct,
        "interest_income": round(interest_income, 2),
        "total_balance": round(total_balance, 2),
        "formula": "(gross_yield_rate - funding_cost_rate) * 100",
    }


def calculate_payback_period(cac: float, monthly_arpu: float) -> dict[str, Any]:
    """CAC Payback Period.

    Payback (months) = CAC / monthly_ARPU

    Returns dict with payback_months (None if inputs are zero), cac, monthly_arpu, formula.
    """
    if monthly_arpu <= 0 or cac <= 0:
        return {
            "payback_months": None,
            "cac": round(cac, 2),
            "monthly_arpu": round(monthly_arpu, 2),
            "formula": "CAC / monthly_ARPU",
        }
    payback = round(cac / monthly_arpu, 2)
    logger.debug("Payback period=%.2f months, CAC=%.2f, ARPU=%.2f", payback, cac, monthly_arpu)
    return {
        "payback_months": payback,
        "cac": round(cac, 2),
        "monthly_arpu": round(monthly_arpu, 2),
        "formula": "CAC / monthly_ARPU",
    }


def calculate_cure_rate(df: pd.DataFrame) -> dict[str, Any]:
    """Cure Rate (proxy).

    Proxy = delinquent loans with last_payment_amount > 0 / total_delinquent * 100.
    A true cure rate requires two consecutive period snapshots (T-1 → T).

    Returns dict with cure_rate_pct, delinquent_count, curing_count, formula, note.
    """
    if df.empty:
        return {
            "cure_rate_pct": 0.0,
            "delinquent_count": 0,
            "curing_count": 0,
            "formula": "delinquent_with_recent_payment / total_delinquent * 100",
            "note": "Proxy metric: requires T/T-1 snapshots for precise cure rate",
        }

    dpd = _resolve_dpd(df)
    delinquent_mask = dpd > 0
    delinquent_count = int(delinquent_mask.sum())

    if delinquent_count == 0:
        return {
            "cure_rate_pct": 0.0,
            "delinquent_count": 0,
            "curing_count": 0,
            "formula": "delinquent_with_recent_payment / total_delinquent * 100",
            "note": "Proxy metric: requires T/T-1 snapshots for precise cure rate",
        }

    collected_col = _first_col(df, ["last_payment_amount", "payment_amount"])
    if collected_col:
        collected = _to_num(df[collected_col])
        curing_mask = delinquent_mask & (collected > 0)
    else:
        curing_mask = pd.Series([False] * len(df), index=df.index)

    curing_count = int(curing_mask.sum())
    cure_rate = _safe_pct(float(curing_count), float(delinquent_count))

    logger.debug(
        "Cure rate=%.4f%%, delinquent=%d, curing=%d",
        cure_rate,
        delinquent_count,
        curing_count,
    )
    return {
        "cure_rate_pct": round(cure_rate, 4),
        "delinquent_count": delinquent_count,
        "curing_count": curing_count,
        "formula": "delinquent_with_recent_payment / total_delinquent * 100",
        "note": "Proxy metric: requires T/T-1 snapshots for precise cure rate",
    }


def calculate_dpd_migration_risk(df: pd.DataFrame) -> list[dict[str, Any]]:
    """DPD Bucket Distribution with action recommendation.

    Each bucket carries a risk_level flag and a recommended_action to turn
    portfolio data into operational decisions.

    Returns list of dicts: bucket, loan_count, balance, balance_share_pct,
    risk_level, recommended_action.
    """
    if df.empty:
        return []

    balance = _resolve_balance(df)
    dpd = _resolve_dpd(df)
    total_balance = float(balance.sum())

    buckets_def: list[tuple[str, pd.Series, str, str]] = [
        ("current", dpd <= 0, "low", "Monitor – no immediate action"),
        (
            "dpd_1_30",
            (dpd > 0) & (dpd <= 30),
            "medium",
            "Trigger early collection contact (SMS / call)",
        ),
        (
            "dpd_31_60",
            (dpd > 30) & (dpd <= 60),
            "high",
            "Escalate collection intensity – send formal notice",
        ),
        (
            "dpd_61_90",
            (dpd > 60) & (dpd <= 90),
            "critical",
            "Activate legal / field team and restructure review",
        ),
        (
            "dpd_90_plus",
            dpd > 90,
            "critical",
            "Full provision write-off candidate – activate recovery workflow",
        ),
    ]

    rows: list[dict[str, Any]] = []
    for bucket_name, mask, risk_level, recommended_action in buckets_def:
        bucket_balance = float(balance[mask].sum())
        rows.append(
            {
                "bucket": bucket_name,
                "loan_count": int(mask.sum()),
                "balance": round(bucket_balance, 2),
                "balance_share_pct": round(_safe_pct(bucket_balance, total_balance), 4),
                "risk_level": risk_level,
                "recommended_action": recommended_action,
            }
        )
    return rows


def calculate_all_unit_economics(
    df: pd.DataFrame,
    funding_cost_rate: float = 0.08,
    cac: float = 0.0,
    monthly_arpu: float = 0.0,
) -> dict[str, Any]:
    """Calculate all unit-economics KPIs in a single call.

    Args:
        df: Loan-level DataFrame.
        funding_cost_rate: Annualized cost of funds as decimal (default 8%).
        cac: Customer acquisition cost (USD) used for payback period.
        monthly_arpu: Monthly average revenue per user (USD) for payback period.

    Returns:
        Dict with keys: npl, lgd, cost_of_risk, nim, payback, cure_rate, dpd_migration.
    """
    if df.empty:
        return {
            "npl": calculate_npl_ratio(pd.DataFrame()),
            "lgd": calculate_lgd(pd.DataFrame()),
            "cost_of_risk": calculate_cost_of_risk(pd.DataFrame()),
            "nim": calculate_nim(pd.DataFrame(), funding_cost_rate),
            "payback": calculate_payback_period(cac, monthly_arpu),
            "cure_rate": calculate_cure_rate(pd.DataFrame()),
            "dpd_migration": [],
        }

    return {
        "npl": calculate_npl_ratio(df),
        "lgd": calculate_lgd(df),
        "cost_of_risk": calculate_cost_of_risk(df),
        "nim": calculate_nim(df, funding_cost_rate),
        "payback": calculate_payback_period(cac, monthly_arpu),
        "cure_rate": calculate_cure_rate(df),
        "dpd_migration": calculate_dpd_migration_risk(df),
    }
