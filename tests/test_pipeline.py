import pytest
import pandas as pd
from python.ingestion import CascadeIngestion
from python.transformation import DataTransformation
from python.kpi_engine import KPIEngine


def sample_df():
    return pd.DataFrame({
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
    })


def test_ingest_data(tmp_path):
    # Create a sample CSV file
    df = sample_df()
    csv_file = tmp_path / "sample.csv"
    df.to_csv(csv_file, index=False)
    ingestion = CascadeIngestion(data_dir=tmp_path)
    ingested = ingestion.ingest_csv("sample.csv")
    assert not ingested.empty


def test_transform_data():
    df = sample_df()
    transformer = DataTransformation()
    kpi_df = transformer.transform_to_kpi_dataset(df)
    assert isinstance(kpi_df, pd.DataFrame)


def test_validate_loans():
    df = pd.DataFrame({"period": ["2025Q4"], "measurement_date": ["2025-12-01"], "total_receivable_usd": [1000.0]})
    ingestion = CascadeIngestion(data_dir=".")
    validated = ingestion.validate_loans(df)
    assert "_validation_passed" in validated.columns


def test_calculate_kpis():
    df = sample_df()
    transformer = DataTransformation()
    kpi_df = transformer.transform_to_kpi_dataset(df)
    kpi_engine = KPIEngine(kpi_df)
    par_30, _ = kpi_engine.calculate_par_30()
    assert isinstance(par_30, float)
