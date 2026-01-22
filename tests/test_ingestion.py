import io

import polars as pl

from python.ingestion import AbacoIngestion


def test_ingest_uploaded_file_basic():
    """Test successful ingestion of a valid CSV."""
    csv_content = """loan_id,loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,measurement_date
L1,1000,1200,50000,1500,current,0.05,950,2025-01-01
L2,5000,6000,75000,2000,current,0.06,4800,2025-01-01
"""
    ingestor = AbacoIngestion()
    df = ingestor.ingest_uploaded_file(io.BytesIO(csv_content.encode("utf-8")))

    assert not df.is_empty()
    assert len(df) == 2
    assert df.schema["loan_amount"] == pl.Float64
    assert df["loan_id"].to_list() == ["L1", "L2"]


def test_ingest_with_cleaning():
    """Test ingestion with currency and comma cleaning."""
    csv_content = """loan_id,loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,measurement_date
L1,"$1,000.00","$1,200.00","$50,000.00","$1,500.00",current,0.05,"$950.00",2025-01-01
"""
    ingestor = AbacoIngestion()
    df = ingestor.ingest_uploaded_file(io.BytesIO(csv_content.encode("utf-8")))

    assert not df.is_empty()
    assert df["loan_amount"][0] == 1000.0
    assert df["principal_balance"][0] == 950.0


def test_ingest_schema_mismatch():
    """Test ingestion with missing required columns."""
    csv_content = "loan_id,loan_amount\nL1,1000"
    ingestor = AbacoIngestion()
    df = ingestor.ingest_uploaded_file(io.BytesIO(csv_content.encode("utf-8")))

    assert df.is_empty()
    summary = ingestor.get_ingest_summary()
    assert summary["total_errors"] > 0
    # Check for either contract violation or casting error
    assert any(
        "Contract Violation" in err["error"] or "unable to find column" in err["error"]
        for err in summary["errors"]
    )


def test_ingest_summary_tracking():
    """Test that ingestion summary tracks rows and run_id."""
    ingestor = AbacoIngestion()
    csv_content = """loan_id,loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,measurement_date
L1,1000,1200,50000,1500,current,0.05,950,2025-01-01
"""
    ingestor.ingest_uploaded_file(io.BytesIO(csv_content.encode("utf-8")))
    summary = ingestor.get_ingest_summary()

    assert summary["rows_ingested"] == 1
    assert "run_id" in summary
    assert "timestamp" in summary
