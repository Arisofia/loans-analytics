import pandas as pd
import pytest

from python.pipeline.ingestion import UnifiedIngestion
from python.kpi_engine import KPIEngine
from python.pipeline.transformation import UnifiedTransformation


def test_pipeline_missing_required_column():
    # DataFrame missing a required field
    df = pd.DataFrame(
        {
            "period": ["2025Q1"],
            "measurement_date": ["2025-03-31"],
            # 'total_receivable_usd' is missing
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
    ingestion = UnifiedIngestion(data_dir=".")
    df = ingestion.ingest_dataframe(df)
    validated = ingestion.validate_loans(df)
    assert not validated["_validation_passed"].iloc[0]
    transformer = UnifiedTransformation()
    with pytest.raises(ValueError, match="missing required columns"):
        transformer.transform_to_kpi_dataset(validated)


def test_pipeline_invalid_numeric_type():
    # DataFrame with invalid numeric type
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
    ingestion = UnifiedIngestion()
    df = ingestion.ingest_dataframe(df)
    validated = ingestion.validate_loans(df)
    assert not validated["_validation_passed"].iloc[0]
    transformer = UnifiedTransformation()
    with pytest.raises(ValueError):
        transformer.transform_to_kpi_dataset(validated)


def test_pipeline_kpi_engine_missing_column():
    # DataFrame missing a KPI column
    df = pd.DataFrame(
        {
            "total_receivable_usd": [1000.0],
            # 'dpd_30_60_usd' is missing
            "dpd_60_90_usd": [30.0],
            "dpd_90_plus_usd": [20.0],
            "total_eligible_usd": [900.0],
            "discounted_balance_usd": [800.0],
            "dpd_0_7_usd": [700.0],
            "dpd_7_30_usd": [100.0],
        }
    )
    transformer = UnifiedTransformation()
    with pytest.raises(ValueError, match="missing required columns"):
        transformer.transform_to_kpi_dataset(df)
