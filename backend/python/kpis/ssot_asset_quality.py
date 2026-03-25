from __future__ import annotations
from collections.abc import Sequence
import pandas as pd
from backend.python.kpis.formula_engine import KPIFormulaEngine
_METRIC_ALIAS_TO_ID: dict[str, str] = {'par30': 'par_30', 'par60': 'par_60', 'par90': 'par_90', 'npl': 'npl', 'npl90': 'npl_90_proxy', 'npl180': 'npl_180_proxy'}
_ASSET_QUALITY_REGISTRY = {'version': 'asset-quality-ssot-1.2', 'asset_quality_kpis': {'par_30': {'formula': "SUM(outstanding_balance WHERE dpd >= 30 OR status IN ['delinquent', 'defaulted']) / SUM(outstanding_balance) * 100", 'unit': 'percentage'}, 'par_60': {'formula': "SUM(outstanding_balance WHERE dpd >= 60 OR status IN ['delinquent', 'defaulted']) / SUM(outstanding_balance) * 100", 'unit': 'percentage'}, 'par_90': {'formula': 'SUM(outstanding_balance WHERE dpd >= 90) / SUM(outstanding_balance) * 100', 'unit': 'percentage'}, 'npl': {'formula': "SUM(outstanding_balance WHERE dpd >= 60 OR status IN ['delinquent', 'defaulted']) / SUM(outstanding_balance) * 100", 'unit': 'percentage'}, 'npl_90_proxy': {'formula': "SUM(outstanding_balance WHERE dpd >= 90 OR status = 'defaulted') / SUM(outstanding_balance) * 100", 'unit': 'percentage'}, 'npl_180_proxy': {'formula': "SUM(outstanding_balance WHERE dpd >= 180 OR status = 'defaulted') / SUM(outstanding_balance) * 100", 'unit': 'percentage'}}}

def _normalize_status_for_ssot(status: pd.Series) -> pd.Series:
    normalized = status.astype(str).str.lower().fillna('active')
    normalized = normalized.mask(normalized.str.contains('default', na=False), 'defaulted')
    normalized = normalized.mask(normalized.str.contains('delinq', na=False), 'delinquent')
    return normalized

def calculate_asset_quality_metrics(balance: pd.Series, dpd: pd.Series, *, actor: str, metric_aliases: Sequence[str], status: pd.Series | None=None) -> dict[str, float]:
    normalized_df = pd.DataFrame({'outstanding_balance': pd.to_numeric(balance, errors='coerce').fillna(0.0), 'dpd': pd.to_numeric(dpd, errors='coerce').fillna(0.0), 'status': _normalize_status_for_ssot(status) if status is not None else pd.Series(['active'] * len(balance), index=balance.index, dtype=str)})
    engine = KPIFormulaEngine(normalized_df, actor=actor, registry_data=_ASSET_QUALITY_REGISTRY)
    values: dict[str, float] = {}
    for alias in metric_aliases:
        metric_id = _METRIC_ALIAS_TO_ID.get(alias)
        if metric_id is None:
            continue
        values[alias] = float(engine.calculate_kpi(metric_id)['value'])
    return values
