import numpy as np
import pandas as pd
import pytest

from python.kpis.par_30 import calculate_par_30


def test_calculate_par_30_standard():
    df = pd.DataFrame(
        {
            "dpd_30_60_usd": [100.0, 200.0],
            "dpd_60_90_usd": [50.0, 50.0],
            "dpd_90_plus_usd": [25.0, 25.0],
            "total_receivable_usd": [1000.0, 2000.0],
        }
    )
    value, context = calculate_par_30(df)
    assert value == pytest.approx(15.0)
    assert isinstance(context, dict)
    assert context['rows_processed'] == 2


def test_calculate_par_30_zero_receivable():
    df = pd.DataFrame(
        {
            "dpd_30_60_usd": [0.0],
            "dpd_60_90_usd": [0.0],
            "dpd_90_plus_usd": [0.0],
            "total_receivable_usd": [0.0],
        }
    )
    value, context = calculate_par_30(df)
    assert value == 0.0


def test_calculate_par_30_missing_columns():
    df = pd.DataFrame({"total_receivable_usd": [1000.0]})
    with pytest.raises(ValueError):
        calculate_par_30(df)


def test_calculate_par_30_empty_df():
    df = pd.DataFrame()
    value, context = calculate_par_30(df)
    assert value == 0.0
    assert isinstance(value, (float, np.floating))
