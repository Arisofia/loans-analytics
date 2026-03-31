from __future__ import annotations
from collections.abc import Sequence
import pandas as pd
from backend.python.kpis.formula_engine import KPIFormulaEngine

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
