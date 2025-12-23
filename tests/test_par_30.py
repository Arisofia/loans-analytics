import pandas as pd
import pytest
import numpy as np
from python.kpis.par_30 import calculate_par_30

def test_calculate_par_30_standard():
    df = pd.DataFrame({
        "dpd_30_60_usd": [100.0, 200.0],
        "dpd_60_90_usd": [50.0, 50.0],
        "dpd_90_plus_usd": [25.0, 25.0],
        "total_receivable_usd": [1000.0, 2000.0]
    })
    # Total DPD 30+ = 300 + 100 + 50 = 450
    # Total Receivable = 3000
    # PAR 30 = 15.0
    assert calculate_par_30(df) == pytest.approx(15.0)

def test_calculate_par_30_zero_receivable():
    df = pd.DataFrame({
        "dpd_30_60_usd": [0.0],
        "dpd_60_90_usd": [0.0],
        "dpd_90_plus_usd": [0.0],
        "total_receivable_usd": [0.0]
    })
    assert calculate_par_30(df) == 0.0

def test_calculate_par_30_missing_columns():
    # Should handle missing columns gracefully by treating them as 0
    df = pd.DataFrame({
        "total_receivable_usd": [1000.0]
    })
    assert calculate_par_30(df) == 0.0

def test_calculate_par_30_empty_df():
    df = pd.DataFrame()
    assert calculate_par_30(df) == 0.0
    assert isinstance(calculate_par_30(df), (float, np.floating))