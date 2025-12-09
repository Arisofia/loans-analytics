import pandas as pd
import pytest
from python.kpi_engine import calculate_par_90, calculate_collection_rate

def test_par_90_from_sample_data():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    result = calculate_par_90(df)
    assert result == pytest.approx(3.25, rel=0.01)  # 3.25% PAR expected

def test_collection_rate_calculation():
    df = pd.read_csv('data_samples/abaco_portfolio_sample.csv')
    result = calculate_collection_rate(df)
    assert result == pytest.approx(97.2, rel=0.01)  # 97.2% collection rate expected
