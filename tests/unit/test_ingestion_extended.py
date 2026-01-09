import pytest
import pandas as pd
from pathlib import Path
from src.pipeline.data_ingestion import UnifiedIngestion

@pytest.fixture
def config():
    return {
        "pipeline": {
            "phases": {
                "ingestion": {
                    "data_dir": "data/raw",
                    "validation": {"strict": False}
                }
            }
        }
    }

def test_ingest_dataframe(config):
    ui = UnifiedIngestion(config)
    df = pd.DataFrame({" loan_id ": ["1"], "Amount": [100.0]})
    ingested = ui.ingest_dataframe(df)
    assert "loan_id" in ingested.columns
    assert "_ingest_run_id" in ingested.columns
    assert "_ingest_timestamp" in ingested.columns

def test_validate_loans(config):
    ui = UnifiedIngestion(config)
    df = pd.DataFrame({"loan_id": ["1"], "total_receivable_usd": [100.0]})
    # This might fail schema validation if not perfectly aligned with IngestionValidator
    # but we are testing the wrapper logic.
    validated = ui.validate_loans(df)
    assert "_validation_passed" in validated.columns

def test_get_ingest_summary(config):
    ui = UnifiedIngestion(config)
    ui.ingest_dataframe(pd.DataFrame({"a": [1]}))
    summary = ui.get_ingest_summary()
    assert summary["rows_ingested"] == 1
    assert "run_id" in summary

def test_ingest_parquet_failure(config, tmp_path):
    # Test failure path for coverage
    ui = UnifiedIngestion(config)
    result = ui.ingest_parquet("non_existent.parquet")
    assert result.empty

def test_ingest_excel_failure(config):
    ui = UnifiedIngestion(config)
    result = ui.ingest_excel("non_existent.xlsx")
    assert result.empty
