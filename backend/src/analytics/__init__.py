"""COMPATIBILITY_ONLY — Legacy analytics helpers.

This module provides utility functions (standardize_numeric, calculate_quality_score,
portfolio_kpis, project_growth) retained for backward compatibility and test support.

It is NOT the KPI Single Source of Truth.  Canonical KPI formulas live in:
  - backend.python.kpis.ssot_asset_quality  (PAR, NPL, asset-quality)
  - backend.python.kpis.engine              (KPIEngineV2)
  - backend.python.kpis.health_score        (portfolio health scoring)

Do NOT add new financial math here.  Any new metric must be added to the
canonical KPI engine and routed through the SSoT layer.

FINANCIAL PRECISION NOTE
------------------------
All monetary aggregation paths in this module use Decimal arithmetic.
Float is intentionally excluded from production financial paths:
  - principal_sum / delinquent_principal: accumulated as Decimal, no float
    arithmetic performed on monetary balances at any point.
  - delinquency_rate / portfolio_yield: Decimal ratio converted to float only
    at the final return boundary (dimensionless display values).
  - average_ltv / average_dti: dimensionless ratios accumulated as Decimal,
    converted to float for display only — not used in settlement or provisioning.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

from backend.python.config.mype_rules import MYPEBusinessRules

_ZERO = Decimal("0")


def standardize_numeric(series: pd.Series) -> pd.Series:
    """Coerce a mixed-type Series to float for DataFrame enrichment only.

    The float output feeds enriched DataFrames for display and ratio columns
    (LTV, DTI).  Monetary sums in portfolio_kpis() use independent Decimal
    accumulators and never perform float arithmetic on monetary values directly.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype(float)
    cleaned = (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "<NA>": pd.NA})
        .str.replace(",", "", regex=False)
        .str.replace(r"[$€£¥₽%]", "", regex=True)
        .str.replace(r"\s+", "", regex=True)
        .str.replace(r"[^0-9\-.]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce").astype(float)


def calculate_quality_score(df: pd.DataFrame) -> float:
    """Return completeness score (0–100) as a display-only float percentage."""
    if df.empty or len(df.columns) == 0:
        return 0.0
    total_cells = int(df.shape[0] * df.shape[1])
    if total_cells == 0:
        return 0.0
    non_null_cells = int(df.notna().sum().sum())
    if non_null_cells == 0:
        return 0.0
    return round(non_null_cells / total_cells * 100, 1)


def portfolio_kpis(df: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    """Compute portfolio-level KPIs using Decimal arithmetic for all monetary paths.

    Returns
    -------
    metrics : dict[str, float]
        delinquency_rate — balance-weighted delinquency ratio (dimensionless)
        portfolio_yield  — balance-weighted gross yield (dimensionless)
        average_ltv      — mean loan-to-value ratio (dimensionless)
        average_dti      — mean debt-to-income ratio (dimensionless)
    enriched : pd.DataFrame
        Input DataFrame with ltv_ratio and dti_ratio columns appended.

    FINANCIAL PRECISION CONTRACT
    ----------------------------
    principal_sum, delinquent_principal, and weighted_interest are accumulated
    as Decimal.  No float arithmetic is performed on monetary values.  The final
    dict values are dimensionless ratios cast to float only at the return boundary.
    """
    required = [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "principal_balance",
        "interest_rate",
        "loan_status",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    if df.empty:
        return (
            {
                "delinquency_rate": 0.0,
                "portfolio_yield": 0.0,
                "average_ltv": 0.0,
                "average_dti": 0.0,
            },
            df.copy(),
        )

    enriched = df.copy()
    for col in [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "principal_balance",
        "interest_rate",
    ]:
        enriched[col] = standardize_numeric(enriched[col])

    # ── LTV ratio (display only — not a monetary value) ───────────────────────
    with np.errstate(divide="ignore", invalid="ignore"):
        enriched["ltv_ratio"] = enriched["loan_amount"] / enriched[
            "appraised_value"
        ].replace(0, np.nan)

    # ── DTI ratio (display only — not a monetary value) ───────────────────────
    income_positive = enriched["borrower_income"] > 0
    enriched["dti_ratio"] = np.nan
    enriched.loc[income_positive, "dti_ratio"] = enriched.loc[
        income_positive, "monthly_debt"
    ] / (enriched.loc[income_positive, "borrower_income"] / 12.0)

    # ── Monetary aggregation — Decimal accumulators, no float arithmetic ──────
    principal_series = enriched["principal_balance"].dropna()

    principal_sum_dec: Decimal = _ZERO
    for val in principal_series:
        principal_sum_dec += Decimal(str(val))

    if principal_sum_dec <= _ZERO:
        delinquency_rate = 0.0
        portfolio_yield = 0.0
    else:
        delinquent_mask = enriched["loan_status"].astype(str).str.lower().eq("delinquent")
        delinquent_principal_dec: Decimal = _ZERO
        for val in enriched.loc[delinquent_mask, "principal_balance"].dropna():
            delinquent_principal_dec += Decimal(str(val))

        # Convert to float only at the return boundary — no intermediate float math.
        delinquency_rate = float(delinquent_principal_dec / principal_sum_dec)

        # Weighted interest: sum(balance_i * rate_i) / sum(balance_i)
        # Both operands are Decimal; no float multiplication on monetary values.
        weighted_interest_dec: Decimal = _ZERO
        for idx in enriched.index:
            bal = enriched.at[idx, "principal_balance"]
            rate = enriched.at[idx, "interest_rate"]
            if not (pd.isna(bal) or pd.isna(rate)):
                weighted_interest_dec += Decimal(str(bal)) * Decimal(str(rate))

        portfolio_yield = float(weighted_interest_dec / principal_sum_dec)

    # ── Ratio averages (dimensionless, display only) ───────────────────────────
    ltv_clean = enriched["ltv_ratio"].dropna()
    if ltv_clean.empty:
        average_ltv = 0.0
    else:
        ltv_sum = sum(Decimal(str(v)) for v in ltv_clean)
        average_ltv = float(ltv_sum / Decimal(str(len(ltv_clean))))

    dti_clean = enriched["dti_ratio"].dropna()
    if dti_clean.empty:
        average_dti = 0.0
    else:
        dti_sum = sum(Decimal(str(v)) for v in dti_clean)
        average_dti = float(dti_sum / Decimal(str(len(dti_clean))))

    metrics: dict[str, float] = {
        "delinquency_rate": delinquency_rate,
        "portfolio_yield": portfolio_yield,
        "average_ltv": average_ltv,
        "average_dti": average_dti,
    }
    return (metrics, enriched)


def project_growth(
    start_yield: float,
    end_yield: float,
    start_loan_volume: float,
    end_loan_volume: float,
    periods: int = 6,
) -> pd.DataFrame:
    """Build a linear growth projection DataFrame for display / scenario use only.

    The yield and volume columns are projection floats, not settled monetary
    figures.  They must not be used as inputs to ledger or provisioning logic.
    """
    if periods < 2:
        raise ValueError("periods must be at least 2")
    base_month = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )
    months = pd.date_range(base_month, periods=periods, freq="MS")
    projection = pd.DataFrame(
        {
            "month": months.strftime("%b %Y"),
            "yield": np.linspace(float(start_yield), float(end_yield), periods),
            "loan_volume": np.linspace(
                float(start_loan_volume), float(end_loan_volume), periods
            ),
        }
    )
    return projection


__all__ = [
    "MYPEBusinessRules",
    "calculate_quality_score",
    "portfolio_kpis",
    "project_growth",
    "standardize_numeric",
]
