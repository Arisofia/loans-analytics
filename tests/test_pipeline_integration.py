import pandas as pd
import pytest
from python.pipeline.ingestion import UnifiedIngestion
from python.pipeline.transformation import UnifiedTransformation


def test_pipeline_with_valid_data(minimal_config, tmp_path):
    df = pd.DataFrame(
        {
            "period": ["2025Q1"],
            "measurement_date": ["2025-03-31"],
            "cash_available_usd": [500.0],
            "total_receivable_usd": [1000.0],
            "total_eligible_usd": [1000.0],
            "discounted_balance_usd": [900.0],
            "dpd_0_7_usd": [800.0],
            "dpd_7_30_usd": [100.0],
            "dpd_30_60_usd": [50.0],
            "dpd_60_90_usd": [30.0],
            "dpd_90_plus_usd": [20.0],
        }
    )
    csv_file = tmp_path / "test.csv"
    df.to_csv(csv_file, index=False)

    ingestion = UnifiedIngestion(minimal_config)
    ingest_result = ingestion.ingest_file(csv_file)
    assert not ingest_result.df.empty

    transformer = UnifiedTransformation(minimal_config)
    transform_result = transformer.transform(ingest_result.df)
    assert not transform_result.df.empty


def test_pipeline_ingestion_with_invalid_numeric_column(minimal_config, tmp_path):
    df = pd.DataFrame(
        {
            "period": ["2025Q1"],
            "measurement_date": ["2025-03-31"],
            "total_receivable_usd": ["not-a-number"],
            "cash_available_usd": [500.0],
            "total_eligible_usd": [1000.0],
            "discounted_balance_usd": [900.0],
            "dpd_0_7_usd": [800.0],
            "dpd_7_30_usd": [100.0],
            "dpd_30_60_usd": [50.0],
            "dpd_60_90_usd": [30.0],
            "dpd_90_plus_usd": [20.0],
        }
    )
    csv_file = tmp_path / "test.csv"
    df.to_csv(csv_file, index=False)

    ingestion = UnifiedIngestion(minimal_config)
    with pytest.raises(ValueError):
        ingestion.ingest_file(csv_file)


def test_pipeline_transformation_with_valid_columns(minimal_config):
    df = pd.DataFrame(
        {
            "total_receivable_usd": [1000.0],
            "dpd_30_60_usd": [50.0],
            "dpd_60_90_usd": [30.0],
            "dpd_90_plus_usd": [20.0],
            "total_eligible_usd": [900.0],
            "discounted_balance_usd": [800.0],
            "dpd_0_7_usd": [700.0],
            "dpd_7_30_usd": [100.0],
        }
    )
    transformer = UnifiedTransformation(minimal_config)
    result = transformer.transform(df)
    assert not result.df.empty
