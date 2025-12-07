import pandas as pd
import pytest
from python.transformation import DataTransformation

def sample_df():
    return pd.DataFrame({
        "total_receivable_usd": [1000.0, 2000.0],
        "total_eligible_usd": [900.0, 1800.0],
        "discounted_balance_usd": [800.0, 1600.0],
        "dpd_30_60_usd": [100.0, 200.0],
        "dpd_60_90_usd": [50.0, 50.0],
        "dpd_90_plus_usd": [25.0, 25.0]
    })

def test_calculate_receivables_metrics():
    dt = DataTransformation()
    metrics = dt.calculate_receivables_metrics(sample_df())
    for key in ["total_receivable", "total_eligible", "discounted_balance"]:
        assert key in metrics
    assert metrics["total_receivable"] == pytest.approx(3000.0)
    assert metrics["total_eligible"] == pytest.approx(2700.0)
    assert metrics["discounted_balance"] == pytest.approx(2400.0)
    # Check instance variables
    assert hasattr(dt, "run_id")
    assert isinstance(dt.run_id, str)

def test_calculate_dpd_ratios():
    dt = DataTransformation()
    ratios = dt.calculate_dpd_ratios(sample_df())
    for key in ["dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd"]:
        assert key in ratios
    assert ratios["dpd_30_60_usd"] == pytest.approx((100+200)/3000*100)
    assert ratios["dpd_60_90_usd"] == pytest.approx((50+50)/3000*100)
    assert ratios["dpd_90_plus_usd"] == pytest.approx((25+25)/3000*100)

def test_transform_to_kpi_dataset():
    dt = DataTransformation()
    kpi_df = dt.transform_to_kpi_dataset(sample_df())
    for col in ["receivable_amount", "eligible_amount", "discounted_amount", "dpd_30_60_usd_pct", "_transform_run_id", "_transform_timestamp"]:
        assert col in kpi_df.columns
    assert len(kpi_df) == len(sample_df())
    # Check instance variables
    assert hasattr(dt, "transformations_count")
    assert dt.transformations_count == 1

def test_validate_transformations():
    dt = DataTransformation()
    original = sample_df()
    kpi_df = dt.transform_to_kpi_dataset(original)
    result = dt.validate_transformations(original, kpi_df)
    assert result is True

def test_validate_transformations_row_mismatch():
    dt = DataTransformation()
    original = sample_df()
    kpi_df = dt.transform_to_kpi_dataset(original)
    kpi_df = kpi_df.iloc[:-1]
    result = dt.validate_transformations(original, kpi_df)
    assert result is False

def test_validate_transformations_total_mismatch():
    dt = DataTransformation()
    original = sample_df()
    kpi_df = dt.transform_to_kpi_dataset(original)
    kpi_df["receivable_amount"] = kpi_df["receivable_amount"] + 100
    result = dt.validate_transformations(original, kpi_df)
    assert result is False
