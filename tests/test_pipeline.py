
import pytest
import pandas as pd
from python.ingestion import CascadeIngestion
from python.transformation import DataTransformation
from python.kpi_engine import KPIEngine

def test_ingest_data(tmp_path):
    # Create a sample CSV file
    csv_content = "period,measurement_date,total_receivable_usd\n2025Q4,2025-12-01,1000.0\n2025Q4,2025-12-02,2000.0"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    ingestion = CascadeIngestion(data_dir=tmp_path)
    df = ingestion.ingest_csv("sample.csv")
    assert not df.empty

def test_transform_data():
    df = pd.DataFrame({"period": ["2025Q4"], "measurement_date": ["2025-12-01"], "total_receivable_usd": [1000.0]})
    transformer = DataTransformation()
    kpi_df = transformer.transform_to_kpi_dataset(df)
    assert isinstance(kpi_df, pd.DataFrame)

def test_validate_loans():
    df = pd.DataFrame({"period": ["2025Q4"], "measurement_date": ["2025-12-01"], "total_receivable_usd": [1000.0]})
    ingestion = CascadeIngestion()
    validated = ingestion.validate_loans(df)
    assert "_validation_passed" in validated.columns

def test_calculate_kpis():
    df = pd.DataFrame({
        "period": ["2025Q4", "2025Q4", "2025Q4"],
        "measurement_date": ["2025-12-01", "2025-12-02", "2025-12-03"],
        "total_receivable_usd": [1000.0, 2000.0, 3000.0]
    })
    transformer = DataTransformation()
    kpi_df = transformer.transform_to_kpi_dataset(df)
    kpi_engine = KPIEngine(kpi_df)
    par_30, _ = kpi_engine.calculate_par_30()
    assert isinstance(par_30, float)
