import pytest
import pandas as pd
from backend.loans_analytics.kpis.ssot_asset_quality import calculate_asset_quality_metrics

def test_calculate_asset_quality_metrics_fails_on_empty_input():
    balance = pd.Series([], dtype=float)
    dpd = pd.Series([], dtype=float)
    with pytest.raises(ValueError, match="empty dataset"):
        calculate_asset_quality_metrics(balance, dpd, actor='asset_quality_test', metric_aliases=('par30',))
