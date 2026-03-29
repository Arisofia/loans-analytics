from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from backend.python.kpis.formula_engine import KPIFormulaEngine

_METRIC_ALIAS_TO_ID: dict[str, str] = {
    "par30": "par_30",
    "par60": "par_60",
    "par90": "par_90",
    "npl": "npl_90_proxy",
    "npl_ratio": "npl_90_proxy",
    "npl90": "npl_90_proxy",
    "npl_90_ratio": "npl_90_proxy",
    "npl180": "npl_180_proxy",
    "default_rate": "default_rate_balance",
}
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
        "npl_90_proxy": {
            "formula": (
                "SUM(outstanding_balance WHERE dpd >= 90 OR status = 'defaulted')"
                " / SUM(outstanding_balance) * 100"
            ),
            "unit": "percentage",
        },
        "npl_180_proxy": {
            "formula": (
                "SUM(outstanding_balance WHERE dpd >= 180 OR status = 'defaulted')"
                " / SUM(outstanding_balance) * 100"
            ),
            "unit": "percentage",
        },
        "default_rate_balance": {
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


class AssetQualitySSOT:
    """Single source of truth for balance-weighted asset-quality KPIs."""

    @staticmethod
    def _resolve_column(df: pd.DataFrame, *candidates: str) -> str:
        for col in candidates:
            if col in df.columns:
                return col
        raise KeyError(f"Missing critical columns for KPI calculation: {list(candidates)}")

    @classmethod
    def _validate_inputs(cls, df: pd.DataFrame, required_cols: Sequence[str]) -> None:
        if df is None or df.empty:
            raise ValueError("Input DataFrame is empty. Cannot calculate KPIs.")
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise KeyError(f"Missing critical columns for KPI calculation: {missing}")
        if "outstanding_principal" in required_cols and df["outstanding_principal"].isna().any():
            raise ValueError(
                "Null values detected in 'outstanding_principal'. Data must be clean before KPI calculation."
            )

    @classmethod
    def calculate_par(cls, df: pd.DataFrame, days_past_due: int) -> float:
        cls._validate_inputs(df, ["outstanding_principal", "days_past_due"])
        total_principal = float(pd.to_numeric(df["outstanding_principal"], errors="coerce").sum())
        if total_principal == 0:
            return 0.0
        dpd = pd.to_numeric(df["days_past_due"], errors="coerce")
        par_principal = float(
            pd.to_numeric(df.loc[dpd >= days_past_due, "outstanding_principal"], errors="coerce").sum()
        )
        return float(par_principal / total_principal)

    @classmethod
    def calculate_npl_90_ratio(cls, df: pd.DataFrame) -> float:
        cls._validate_inputs(df, ["outstanding_principal", "days_past_due", "status"])
        total_principal = float(pd.to_numeric(df["outstanding_principal"], errors="coerce").sum())
        if total_principal == 0:
            return 0.0
        dpd = pd.to_numeric(df["days_past_due"], errors="coerce")
        status = df["status"].astype(str).str.upper()
        npl_mask = (dpd >= 90) | (status == "WRITTEN_OFF")
        npl_principal = float(
            pd.to_numeric(df.loc[npl_mask, "outstanding_principal"], errors="coerce").sum()
        )
        return float(npl_principal / total_principal)

    @classmethod
    def calculate_default_rate(cls, df: pd.DataFrame) -> float:
        cls._validate_inputs(df, ["outstanding_principal", "days_past_due", "status"])
        total_principal = float(pd.to_numeric(df["outstanding_principal"], errors="coerce").sum())
        if total_principal == 0:
            return 0.0
        dpd = pd.to_numeric(df["days_past_due"], errors="coerce")
        status = df["status"].astype(str).str.upper()
        default_mask = (dpd >= 180) | (status == "WRITTEN_OFF")
        default_principal = float(
            pd.to_numeric(df.loc[default_mask, "outstanding_principal"], errors="coerce").sum()
        )
        return float(default_principal / total_principal)

    @staticmethod
    def _build_normalized_df(
        *,
        balance: pd.Series,
        dpd: pd.Series,
        status: pd.Series | None = None,
    ) -> pd.DataFrame:
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
        return normalized_df

    @classmethod
    def calculate_metric_aliases(
        cls,
        *,
        balance: pd.Series,
        dpd: pd.Series,
        actor: str,
        metric_aliases: Sequence[str],
        status: pd.Series | None = None,
    ) -> dict[str, float]:
        normalized_df = cls._build_normalized_df(balance=balance, dpd=dpd, status=status)
        engine = KPIFormulaEngine(normalized_df, actor=actor, registry_data=_ASSET_QUALITY_REGISTRY)
        values: dict[str, float] = {}
        for alias in metric_aliases:
            metric_id = _METRIC_ALIAS_TO_ID.get(alias)
            if metric_id is None:
                continue
            values[alias] = float(engine.calculate_kpi(metric_id)["value"])
        return values


def calculate_asset_quality_metrics(
    balance: pd.Series,
    dpd: pd.Series,
    *,
    actor: str,
    metric_aliases: Sequence[str],
    status: pd.Series | None = None,
) -> dict[str, float]:
    return AssetQualitySSOT.calculate_metric_aliases(
        balance=balance,
        dpd=dpd,
        actor=actor,
        metric_aliases=metric_aliases,
        status=status,
    )
