import pandas as pd
import pytest
import numpy as np
from python.kpis.par_90 import calculate_par_90

def test_calculate_par_90_standard():
    df = pd.DataFrame({
        "dpd_90_plus_usd": [50.0, 50.0],
        "total_receivable_usd": [1000.0, 2000.0]
    })
    # Total DPD 90+ = 100
    # Total Receivable = 3000
    # PAR 90 = 3.333...
    assert calculate_par_90(df) == pytest.approx(3.3333333333333335)

def test_calculate_par_90_zero_receivable():
    df = pd.DataFrame({
        "dpd_90_plus_usd": [10.0],
        "total_receivable_usd": [0.0]
    })
    assert calculate_par_90(df) == 0.0

def test_calculate_par_90_missing_columns():
    # Should handle missing columns gracefully
    df = pd.DataFrame({
        "total_receivable_usd": [1000.0]
    })
    assert calculate_par_90(df) == 0.0

def test_calculate_par_90_empty_df():
    df = pd.DataFrame()
    assert calculate_par_90(df) == 0.0