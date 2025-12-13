import pandas as pd
import pytest

from python.kpis.collection_rate import calculate_par_90


def test_par_90_sample_row():
    df = pd.DataFrame(
        {
            "dpd_90_plus_usd": [32_500],
            "total_receivable_usd": [1_000_000],
        }
    )
    assert calculate_par_90(df) == pytest.approx(3.25, rel=1e-3)


def test_par_90_empty_df_returns_zero():
    assert calculate_par_90(pd.DataFrame()) == 0.0


def test_par_90_zero_receivable_returns_zero():
    df = pd.DataFrame(
        {"dpd_90_plus_usd": [10_000], "total_receivable_usd": [0]}
    )
    assert calculate_par_90(df) == 0.0


def test_par_90_coerces_non_numeric():
    df = pd.DataFrame(
        {
            "dpd_90_plus_usd": ["n/a", None],
            "total_receivable_usd": ["0", "0"],
        }
    )
    assert calculate_par_90(df) == 0.0
