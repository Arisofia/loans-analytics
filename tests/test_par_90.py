import pandas as pd
import pytest

from python.kpis.par_90 import calculate_par_90


def test_calculate_par_90_standard():
    df = pd.DataFrame({"dpd_90_plus_usd": [50.0, 50.0], "total_receivable_usd": [1000.0, 2000.0]})
    value, context = calculate_par_90(df)
    assert value == pytest.approx(3.33, rel=0.01)
    assert isinstance(context, dict)


def test_calculate_par_90_zero_receivable():
    df = pd.DataFrame({"dpd_90_plus_usd": [10.0], "total_receivable_usd": [0.0]})
    value, context = calculate_par_90(df)
    assert value == 0.0


def test_calculate_par_90_missing_columns():
    df = pd.DataFrame({"total_receivable_usd": [1000.0]})
    value, context = calculate_par_90(df)
    assert value == 0.0


def test_calculate_par_90_empty_df():
    df = pd.DataFrame()
    value, context = calculate_par_90(df)
    assert value == 0.0
