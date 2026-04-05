from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, getcontext
from collections.abc import Sequence
import pandas as pd
from backend.loans_analytics.kpis.formula_engine import KPIFormulaEngine

# Enforce decimal context at import time — not at function call time.
# Any module-level misconfiguration of the decimal context is caught immediately.
_CTX = getcontext()
if _CTX.rounding != ROUND_HALF_UP:
    raise RuntimeError(
        f"FATAL: Decimal rounding mode is '{_CTX.rounding}', expected ROUND_HALF_UP. "
        "Call decimal.getcontext().rounding = ROUND_HALF_UP before importing this module."
    )

_METRIC_ALIAS_TO_ID: dict[str, str] = {
    "par30": "par_30",
    "par_30": "par_30",
    "par60": "par_60",
    "par_60": "par_60",
    "par90": "par_90",
    "par_90": "par_90",
    "npl": "npl",
    "npl90": "npl_90_proxy",
    "npl_90_ratio": "npl_90_proxy",
    "npl180": "npl_180_proxy",
    # "default_rate" in the SSOT context is the balance-weighted severe-default
    # exposure rate (dpd>=180 OR status=defaulted). This is NOT the same as the
    # catalog COUNT-based default_rate (COUNT(status=defaulted)/COUNT(loans)*100).
    # The SSOT "default_rate" is used by the engine dispatch table and is the
    # correct metric for provisioning and ECL calculations.
    # For the COUNT-based version, use KPIService._calculate_default_rate().
    "default_rate": "npl_180_proxy",
    "default_rate_by_balance": "npl_180_proxy",
}
# ── NPL Doctrine ──────────────────────────────────────────────────────────────
# NPL (Non-Performing Loan) follows Basel-II/III: a loan is non-performing when
# it is 90 or more days past due OR when its status has been classified as
# "defaulted" by the credit officer. DPD < 90 is early/moderate delinquency and
# is captured by PAR30 / PAR60 — NOT by NPL.
#
# Mapping:
#   npl        → dpd >= 90 OR status = 'defaulted'
#   npl_90_proxy → dpd >= 90 (pure days-past-due criterion, no status override)
#   npl_180_proxy→ dpd >= 180 OR status = 'defaulted'  (severe NPL)
#
# PAR30 / PAR60 / PAR90 remain strictly DPD-threshold metrics (no status gate).
# ──────────────────────────────────────────────────────────────────────────────

_ASSET_QUALITY_REGISTRY = {
    "version": "asset-quality-ssot-1.4",
    "asset_quality_kpis": {
        "par_30": {
            "formula": "SUM(outstanding_balance WHERE dpd >= 30) / SUM(outstanding_balance) * 100",
            "unit": "percentage",
        },
        "par_60": {
            "formula": "SUM(outstanding_balance WHERE dpd >= 60) / SUM(outstanding_balance) * 100",
            "unit": "percentage",
        },
        "par_90": {
            "formula": "SUM(outstanding_balance WHERE dpd >= 90) / SUM(outstanding_balance) * 100",
            "unit": "percentage",
        },
        # NPL = severe delinquency per Basel-II/III: 90+ DPD or explicitly defaulted.
        # Prior value (dpd >= 30) was semantically wrong — that is PAR30.
        "npl": {
            "formula": (
                "SUM(outstanding_balance WHERE dpd >= 90 OR status = 'defaulted')"
                " / SUM(outstanding_balance) * 100"
            ),
            "unit": "percentage",
        },
        "npl_90_proxy": {
            "formula": "SUM(outstanding_balance WHERE dpd >= 90) / SUM(outstanding_balance) * 100",
            "unit": "percentage",
        },
        "npl_180_proxy": {
            "formula": (
                "SUM(outstanding_balance WHERE dpd >= 180 OR status = 'defaulted')"
                " / SUM(outstanding_balance) * 100"
            ),
            "unit": "percentage",
        },
    },
}


def _to_numeric_strict(series: pd.Series, *, field_name: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        bad_rows = [int(idx) for idx in numeric[numeric.isna()].index[:5]]
        raise ValueError(
            f"CRITICAL: Invalid numeric values detected in '{field_name}' at rows {bad_rows}. "
            f"Please remediate source data before KPI calculation."
        )
    return numeric.astype(float)


def _normalize_status_for_ssot(status: pd.Series) -> pd.Series:
    normalized = status.astype(str).str.lower().fillna("unknown")
    normalized = normalized.mask(normalized.str.contains("default", na=False), "defaulted")
    normalized = normalized.mask(normalized.str.contains("delinq", na=False), "delinquent")
    return normalized


def calculate_asset_quality_metrics(
    balance: pd.Series,
    dpd: pd.Series,
    *,
    actor: str,
    metric_aliases: Sequence[str],
    status: pd.Series | None = None,
) -> dict[str, float]:
    normalized_df = pd.DataFrame(
        {
            "outstanding_balance": _to_numeric_strict(balance, field_name="outstanding_balance"),
            "dpd": _to_numeric_strict(dpd, field_name="dpd"),
            "status": (
                _normalize_status_for_ssot(status)
                if status is not None
                else pd.Series(["active"] * len(balance), index=balance.index, dtype=str)
            ),
        }
    )
    if normalized_df.empty:
        raise ValueError(
            "CRITICAL: Asset-quality KPI computation received an empty dataset. "
            "Provide at least one valid loan record."
        )
    if float(normalized_df["outstanding_balance"].sum()) <= 0:
        raise ValueError("CRITICAL: Sum(outstanding_balance) must be > 0 for asset-quality KPIs.")
    engine = KPIFormulaEngine(normalized_df, actor=actor, registry_data=_ASSET_QUALITY_REGISTRY)
    values: dict[str, float] = {}
    for alias in metric_aliases:
        metric_id = _METRIC_ALIAS_TO_ID.get(alias)
        if metric_id is None:
            continue
        values[alias] = float(engine.calculate_kpi(metric_id)["value"])
    return values


def calculate_par(
    balances_at_risk: Decimal,
    total_portfolio: Decimal,
    dpd_threshold: int = 30,
) -> Decimal:
    """PAR (Portfolio at Risk) as a percentage, computed from aggregate balance figures.

    PAR = (balances_at_risk / total_portfolio) * 100, rounded to 3dp ROUND_HALF_UP.
    This is the scalar variant for cases where the caller has already aggregated
    outstanding balances by DPD bucket. Use ``calculate_asset_quality_metrics`` when
    working with a loan-level DataFrame.
    """
    if total_portfolio <= 0:
        raise ValueError(
            f"calculate_par: total_portfolio must be > 0 (got {total_portfolio})"
        )
    ratio = (balances_at_risk / total_portfolio * Decimal("100")).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    return ratio


def calculate_npl(
    df: "pd.DataFrame",
    balance_col: str = "balance",
    dpd_col: str = "dpd",
    status_col: str = "status",
) -> Decimal:
    """NPL percentage per Basel II/III: DPD >= 90 OR status = 'defaulted'.

    Returns
    -------
    Decimal — NPL% rounded to 2dp ROUND_HALF_UP.
    """
    total = Decimal(str(df[balance_col].sum()))
    if total <= 0:
        raise ValueError("calculate_npl: sum of balances must be > 0")
    npl_mask = (df[dpd_col] >= 90) | (df[status_col].str.lower() == "defaulted")
    npl_balance = Decimal(str(df.loc[npl_mask, balance_col].sum()))
    return (npl_balance / total * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
