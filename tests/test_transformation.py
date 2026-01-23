import pandas as pd
import pytest
from src.pipeline.data_transformation import UnifiedTransformation


def sample_df():
    return pd.DataFrame(
        {
            "total_receivable_usd": [1000.0, 2000.0],
            "total_eligible_usd": [900.0, 1800.0],
            "discounted_balance_usd": [800.0, 1600.0],
            "dpd_0_7_usd": [100.0, 200.0],
            "dpd_7_30_usd": [50.0, 100.0],
            "dpd_30_60_usd": [100.0, 200.0],
            "dpd_60_90_usd": [50.0, 50.0],
            "dpd_90_plus_usd": [25.0, 25.0],
        }
    )


def test_transform_basic(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    result = dt.transform(sample_df())
    assert result.df is not None
    assert not result.df.empty
    assert result.run_id == dt.run_id
    assert len(result.lineage) > 0


def test_transform_adds_tracking_columns(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    result = dt.transform(sample_df())
    assert "_tx_run_id" in result.df.columns
    assert "_tx_timestamp" in result.df.columns
    assert all(result.df["_tx_run_id"] == dt.run_id)


def test_transform_normalization(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    df = sample_df()
    df.columns = [c.upper() for c in df.columns]
    result = dt.transform(df)
    assert "total_receivable_usd" in result.df.columns


def test_transform_preserves_row_count(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    original_df = sample_df()
    result = dt.transform(original_df)
    assert len(result.df) == len(original_df)


def test_transform_generates_lineage(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    result = dt.transform(sample_df())
    assert len(result.lineage) > 0
    assert any(entry["step"] == "normalization" for entry in result.lineage)
    assert any(entry["step"] == "complete" for entry in result.lineage)


def test_transform_quality_checks(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    result = dt.transform(sample_df())
    assert isinstance(result.quality_checks, dict)


def test_run_id_generation(minimal_config):
    dt1 = UnifiedTransformation(minimal_config)
    dt2 = UnifiedTransformation(minimal_config)
    assert dt1.run_id != dt2.run_id
    assert dt1.run_id.startswith("tx_")
    assert dt2.run_id.startswith("tx_")


def test_custom_run_id(minimal_config):
    custom_id = "custom_transform_run"
    dt = UnifiedTransformation(minimal_config, run_id=custom_id)
    assert dt.run_id == custom_id


def test_transform_with_null_values(minimal_config):
    df = sample_df()
    df.loc[0, "dpd_0_7_usd"] = None
    dt = UnifiedTransformation(minimal_config)
    result = dt.transform(df)
    assert result.df is not None


def test_transform_error_handling(minimal_config):
    dt = UnifiedTransformation(minimal_config)
    with pytest.raises(Exception):
        dt.transform(None)
