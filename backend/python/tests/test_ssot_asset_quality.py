from __future__ import annotations
from unittest.mock import patch
import pandas as pd
from backend.python.kpis.ssot_asset_quality import calculate_asset_quality_metrics

def test_calculate_asset_quality_metrics_returns_requested_aliases() -> None:
    balance = pd.Series([100.0, 200.0, 300.0])
    dpd = pd.Series([0.0, 45.0, 120.0])
    metrics = calculate_asset_quality_metrics(balance, dpd, actor='asset_quality_test', metric_aliases=('par30', 'par90', 'npl180', 'unknown_alias'))
    assert set(metrics.keys()) == {'par30', 'par90', 'npl180'}
    assert round(metrics['par30'], 2) == 83.33
    assert round(metrics['par90'], 2) == 50.0
    assert round(metrics['npl180'], 2) == 0.0

def test_calculate_asset_quality_metrics_normalizes_status_values() -> None:
    balance = pd.Series([100.0, 200.0, 300.0])
    dpd = pd.Series([10.0, 95.0, 190.0])
    status = pd.Series(['Current', 'DELINQUENT', 'in default'])
    with patch('backend.python.kpis.ssot_asset_quality.KPIFormulaEngine.calculate_kpi') as mock_calc:
        mock_calc.return_value = {'value': 0.0}
        calculate_asset_quality_metrics(balance, dpd, actor='asset_quality_test', metric_aliases=('npl90',), status=status)
    call_args = mock_calc.call_args_list[0]
    assert call_args.args[0] == 'npl_90_proxy'

def test_calculate_asset_quality_metrics_handles_missing_status() -> None:
    balance = pd.Series([50.0, 50.0])
    dpd = pd.Series([180.0, 0.0])
    metrics = calculate_asset_quality_metrics(balance, dpd, actor='asset_quality_test', metric_aliases=('npl180',), status=None)
    assert round(metrics['npl180'], 2) == 50.0


def test_calculate_asset_quality_metrics_fails_on_empty_input() -> None:
    balance = pd.Series([], dtype=float)
    dpd = pd.Series([], dtype=float)
    try:
        calculate_asset_quality_metrics(
            balance,
            dpd,
            actor="asset_quality_test",
            metric_aliases=("par30",),
        )
    except ValueError as exc:
        assert "empty dataset" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for empty dataset.")
