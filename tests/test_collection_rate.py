import pandas as pd
import pytest
from src.kpis.collection_rate import calculate_collection_rate


def test_calculate_collection_rate_standard():
    df = pd.DataFrame(
        {"cash_available_usd": [900.0, 1800.0], "total_eligible_usd": [1000.0, 2000.0]}
    )
    value, context = calculate_collection_rate(df)
    assert value == pytest.approx(90.0)
    assert isinstance(context, dict)


def test_calculate_collection_rate_zero_eligible():
    df = pd.DataFrame({"cash_available_usd": [100.0], "total_eligible_usd": [0.0]})
    value, context = calculate_collection_rate(df)
    assert value == 0.0


def test_calculate_collection_rate_missing_columns():
    df = pd.DataFrame({"other_col": [100.0]})
    value, context = calculate_collection_rate(df)
    assert value == 0.0


def test_calculate_collection_rate_empty_df():
    df = pd.DataFrame()
    value, context = calculate_collection_rate(df)
    assert value == 0.0
