import pandas as pd
from python.pipeline.ingestion import UnifiedIngestion
from python.pipeline.transformation import UnifiedTransformation


def sample_df():
    return pd.DataFrame(
        {
            "period": ["2025Q4", "2025Q4", "2025Q4"],
            "measurement_date": ["2025-12-01", "2025-12-02", "2025-12-03"],
            "total_receivable_usd": [1000.0, 2000.0, 3000.0],
            "total_eligible_usd": [900.0, 1800.0, 2700.0],
            "discounted_balance_usd": [800.0, 1600.0, 2400.0],
            "dpd_0_7_usd": [100.0, 200.0, 300.0],
            "dpd_7_30_usd": [50.0, 100.0, 150.0],
            "dpd_30_60_usd": [100.0, 200.0, 300.0],
            "dpd_60_90_usd": [50.0, 50.0, 50.0],
            "dpd_90_plus_usd": [25.0, 25.0, 25.0],
            "cash_available_usd": [900.0, 1800.0, 2700.0],
        }
    )


def test_ingest_data(tmp_path, minimal_config):
    df = sample_df()
    csv_file = tmp_path / "sample.csv"
    df.to_csv(csv_file, index=False)
    ingestion = UnifiedIngestion(minimal_config)
    result = ingestion.ingest_file(csv_file)
    assert not result.df.empty


def test_transform_data(minimal_config):
    df = sample_df()
    transformer = UnifiedTransformation(minimal_config)
    result = transformer.transform(df)
    assert isinstance(result.df, pd.DataFrame)
    assert "_tx_run_id" in result.df.columns


def test_pipeline_ingestion_and_transformation(tmp_path, minimal_config):
    df = sample_df()
    csv_file = tmp_path / "sample.csv"
    df.to_csv(csv_file, index=False)

    ingestion = UnifiedIngestion(minimal_config)
    ingest_result = ingestion.ingest_file(csv_file)
    assert not ingest_result.df.empty

    transformer = UnifiedTransformation(minimal_config)
    transform_result = transformer.transform(ingest_result.df)
    assert isinstance(transform_result.df, pd.DataFrame)


def test_ingest_with_custom_run_id(tmp_path, minimal_config):
    df = sample_df()
    csv_file = tmp_path / "sample.csv"
    df.to_csv(csv_file, index=False)

    custom_run_id = "custom_ingest_123"
    ingestion = UnifiedIngestion(minimal_config, run_id=custom_run_id)
    result = ingestion.ingest_file(csv_file)
    assert result.run_id == custom_run_id
