from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Iterable, Sequence

import pandas as pd

getcontext().rounding = ROUND_HALF_UP


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def calculate_par(
    balances_at_risk: Decimal | float | int,
    total_portfolio: Decimal | float | int,
    dpd_threshold: int = 30,
) -> Decimal:
    del dpd_threshold
    total = _to_decimal(total_portfolio)
    if total <= 0:
        raise ValueError("Sum(outstanding_balance) must be > 0")
    risk = _to_decimal(balances_at_risk)
    pct = (risk / total) * Decimal("100")
    return pct.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def calculate_npl(
    df: pd.DataFrame,
    *,
    balance_col: str = "outstanding_principal",
    dpd_col: str = "days_past_due",
    status_col: str = "loan_status",
) -> Decimal:
    if df.empty:
        raise ValueError("received an empty dataset")
    bal = pd.to_numeric(df[balance_col], errors="coerce")
    dpd = pd.to_numeric(df[dpd_col], errors="coerce").fillna(0)
    status = df[status_col].astype(str).str.lower().fillna("")
    total = Decimal(str(bal.fillna(0).sum()))
    if total <= 0:
        raise ValueError("Sum(outstanding_balance) must be > 0")
    npl_mask = (dpd >= 90) | status.str.contains("default")
    npl_bal = Decimal(str(bal.where(npl_mask, 0).fillna(0).sum()))
    return ((npl_bal / total) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class KPIFormulaEngine:
    """Minimal compatibility evaluator for legacy KPI patch points."""

    def __init__(self, df: pd.DataFrame, *, actor: str = "system") -> None:
        self.df = df
        self.actor = actor

    def calculate_kpi(self, kpi_name: str) -> dict[str, float]:
        result = calculate_asset_quality_metrics(
            balance=self.df.get(
                "outstanding_principal", self.df.get("balance", pd.Series(dtype=float))
            ),
            dpd=self.df.get("days_past_due", self.df.get("dpd", pd.Series(dtype=float))),
            status=self.df.get("loan_status", self.df.get("status", pd.Series(dtype=str))),
            actor=self.actor,
            metric_aliases=(kpi_name,),
        )
        return {"value": float(result.get(kpi_name, result.get(_normalize_alias(kpi_name), 0.0)))}


def _normalize_alias(alias: str) -> str:
    key = alias.lower().replace("_", "")
    mapping = {
        "par30": "par30",
        "par_30": "par30",
        "par60": "par60",
        "par_60": "par60",
        "par90": "par90",
        "par_90": "par90",
        "npl90": "npl90",
        "npl_90": "npl90",
        "npl180": "npl180",
        "npl_180": "npl180",
        "defaultrate": "default_rate",
        "default_rate": "default_rate",
    }
    return mapping.get(key, key)


def calculate_asset_quality_metrics(
    balance: Iterable[object],
    dpd: Iterable[object],
    *,
    status: Iterable[object] | None = None,
    actor: str = "system",
    metric_aliases: Sequence[str] = ("par30", "par60", "par90"),
) -> dict[str, float]:
    del actor
    balance_series = pd.to_numeric(pd.Series(balance), errors="coerce")
    dpd_series = pd.to_numeric(pd.Series(dpd), errors="coerce")
    if balance_series.empty or dpd_series.empty:
        raise ValueError("received an empty dataset")
    if balance_series.isna().any():
        raise ValueError("Invalid numeric values detected in 'outstanding_balance'")

    total = Decimal(str(balance_series.sum()))
    if total <= 0:
        raise ValueError("Sum(outstanding_balance) must be > 0")

    if status is None:
        status_series = pd.Series(["active"] * len(balance_series), dtype="string")
    else:
        status_series = pd.Series(status).astype("string").str.lower().fillna("active")

    def _par(threshold: int) -> float:
        bal = Decimal(str(balance_series.where(dpd_series.fillna(0) >= threshold, 0).sum()))
        return float(
            ((bal / total) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    def _npl(threshold: int) -> float:
        mask = (dpd_series.fillna(0) >= threshold) | status_series.str.contains("default")
        bal = Decimal(str(balance_series.where(mask, 0).sum()))
        return float(
            ((bal / total) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    default_mask = (dpd_series.fillna(0) >= 90) | status_series.str.contains("default")
    default_bal = Decimal(str(balance_series.where(default_mask, 0).sum()))
    default_rate = float(
        ((default_bal / total) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )

    canonical = {
        "par30": _par(30),
        "par60": _par(60),
        "par90": _par(90),
        "npl90": _npl(90),
        "npl180": _npl(180),
        "default_rate": default_rate,
    }

    result: dict[str, float] = {}
    for raw_alias in metric_aliases:
        normalized = _normalize_alias(raw_alias)
        if normalized in canonical:
            result[raw_alias] = canonical[normalized]
    return result


__all__ = [
    "KPIFormulaEngine",
    "calculate_asset_quality_metrics",
    "calculate_npl",
    "calculate_par",
]
