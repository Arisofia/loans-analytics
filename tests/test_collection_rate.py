import pandas as pd
import pytest
import numpy as np
from python.kpis.collection_rate import calculate_collection_rate

def test_calculate_collection_rate_standard():
    df = pd.DataFrame({
        "cash_available_usd": [900.0, 1800.0],
        "total_eligible_usd": [1000.0, 2000.0]
    })
    # Total Cash: 2700
    # Total Eligible: 3000
    # Rate: 90.0%
    assert calculate_collection_rate(df) == pytest.approx(90.0)

def test_calculate_collection_rate_zero_eligible():
    df = pd.DataFrame({
        "cash_available_usd": [100.0],
        "total_eligible_usd": [0.0]
    })
    assert calculate_collection_rate(df) == 0.0

def test_calculate_collection_rate_missing_columns():
    # Should handle missing columns gracefully (treat as 0)
    df = pd.DataFrame({
        "other_col": [100.0]
    })
    assert calculate_collection_rate(df) == 0.0

def test_calculate_collection_rate_empty_df():
    df = pd.DataFrame()
    assert calculate_collection_rate(df) == 0.0