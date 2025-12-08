import pytest
import pandas as pd
from python.ingestion import ingest_data
from python.transformation import transform_data
from python.validation import validate_dataframe
from python.kpi_engine import calculate_kpis

def test_ingest_data():
    df = ingest_data('data/abaco_portfolio_calculations.csv')
    assert not df.empty

def test_transform_data():
    df = pd.DataFrame({'amount': [1, 2, None]})
    df = transform_data(df)
    assert df['amount'].dtype == float
    assert df.isnull().sum().sum() == 0

def test_validate_dataframe():
    df = pd.DataFrame({'amount': [1.0, 2.0]})
    validate_dataframe(df)

def test_calculate_kpis():
    df = pd.DataFrame({'amount': [1.0, 2.0, 3.0]})
    kpis = calculate_kpis(df)
    assert kpis['total_loans'] == 6.0
    assert kpis['avg_loan'] == 2.0
