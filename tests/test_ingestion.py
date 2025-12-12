import pandas as pd
import pytest
from python.ingestion import CascadeIngestion


def test_ingest_csv(tmp_path):
    csv_content = "period,measurement_date,total_receivable_usd\n2025Q4,2025-12-01,1000.0\n2025Q4,2025-12-02,2000.0"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    ingestion = CascadeIngestion(data_dir=tmp_path)
    df = ingestion.ingest_csv("sample.csv")
    assert not df.empty
    for col in ["period", "measurement_date", "total_receivable_usd", "_ingest_run_id", "_ingest_timestamp"]:
        assert col in df.columns
    assert hasattr(ingestion, "run_id")
    assert hasattr(ingestion, "timestamp")
    assert isinstance(ingestion.run_id, str)
    assert isinstance(ingestion.timestamp, str)
    assert all(df["_ingest_run_id"] == ingestion.run_id)
    assert all(isinstance(ts, str) for ts in df["_ingest_timestamp"])
    assert isinstance(ingestion.errors, list)
    assert df["total_receivable_usd"].sum() == pytest.approx(3000.0)


def test_ingest_csv_error(tmp_path):
    ingestion = CascadeIngestion(data_dir=tmp_path)
    df = ingestion.ingest_csv("nonexistent.csv")
    assert df.empty
    assert len(ingestion.errors) == 1
    err = ingestion.errors[0]
    for key in ["file", "error", "timestamp", "run_id"]:
        assert key in err
    assert err["file"] == "nonexistent.csv"
    assert "no such file".lower() in err["error"].lower()


def test_validate_loans():
    df = pd.DataFrame({
        "period": ["2025Q4"],
        "measurement_date": ["2025-12-01"],
        "total_receivable_usd": [1000.0]
    })
    ingestion = CascadeIngestion()
    validated = ingestion.validate_loans(df)
    assert "_validation_passed" in validated.columns
    # With hardened required fields, minimal rows fail validation
    assert bool(validated["_validation_passed"].iloc[0]) is False
    assert isinstance(ingestion.errors, list)
    assert len(ingestion.errors) >= 1


def test_validate_loans_missing_field():
    df = pd.DataFrame({
        "period": ["2025Q4"],
        "measurement_date": ["2025-12-01"]
    })
    ingestion = CascadeIngestion()
    validated = ingestion.validate_loans(df)
    assert "_validation_passed" in validated.columns
    assert bool(validated["_validation_passed"].iloc[0]) is False
    assert isinstance(ingestion.errors, list)
    assert len(ingestion.errors) >= 1
    assert ingestion.errors[0].get("stage") == "validation"


def test_validate_loans_invalid_numeric():
    df = pd.DataFrame({
        "period": ["2025Q4"],
        "measurement_date": ["2025-12-01"],
        "total_receivable_usd": ["invalid"]
    })
    ingestion = CascadeIngestion()
    validated = ingestion.validate_loans(df)
    assert "_validation_passed" in validated.columns
    assert bool(validated["_validation_passed"].iloc[0]) is False
    assert isinstance(ingestion.errors, list)
    numeric_errors = [err for err in ingestion.errors if err.get("stage") == "validation"]
    assert numeric_errors
    assert any("total_receivable_usd" in err.get("error", "") for err in numeric_errors)


def test_get_ingest_summary():
    ingestion = CascadeIngestion()
    summary = ingestion.get_ingest_summary()
    for key in ["run_id", "timestamp", "total_errors", "errors"]:
        assert key in summary
    assert summary["run_id"] == ingestion.run_id
    assert summary["timestamp"] == ingestion.timestamp
    assert isinstance(summary["total_errors"], int)
    assert isinstance(summary["errors"], list)
