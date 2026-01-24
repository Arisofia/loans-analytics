import logging

import polars as pl

from python.schemas import validate_ingestion_contract

logger = logging.getLogger(__name__)


def test_sample_data_contract_compliance():
    """Test using a sample dataframe to ensure validator works."""
    sample_data = {
        "loan_amount": [1000.0, 5000.0],
        "appraised_value": [1200.0, 6000.0],
        "borrower_income": [50000.0, 75000.0],
        "monthly_debt": [1500.0, 2000.0],
        "loan_status": ["current", "current"],
        "interest_rate": [0.05, 0.06],
        "principal_balance": [950.0, 4800.0],
        "loan_id": ["L1", "L2"],
        "measurement_date": ["2025-01-01", "2025-01-01"],
    }
    df = pl.DataFrame(sample_data)
    assert validate_ingestion_contract(df) is True


def test_dirty_data_cleaning_and_validation():
    """Test that currency symbols and commas are cleaned before contract validation."""
    import io

    from python.ingestion import AbacoIngestion

    dirty_csv = """loan_id,loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,measurement_date
L1,"$1,000.00","$1,200.00","$50,000.00","$1,500.00",current,0.05,"$950.00",2025-01-01
L2,"$5,000.00","$6,000.00","$75,000.00","$2,000.00",current,0.06,"$4,800.00",2025-01-01
"""
    ingestor = AbacoIngestion()
    df = ingestor.ingest_uploaded_file(io.BytesIO(dirty_csv.encode("utf-8")))

    assert not df.is_empty()
    assert df["loan_amount"][0] == 1000.0
    assert df["principal_balance"][1] == 4800.0
    assert df.schema["loan_amount"] == pl.Float64
