import pandas as pd
import pytest
from python.validation import validate_dataframe


def test_validate_dataframe_valid():
    df = pd.DataFrame({"amount": [1.0, 2.0, 3.0]})
    validate_dataframe(df)


def test_validate_dataframe_missing_amount_column():
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    with pytest.raises(AssertionError, match="Missing 'amount' column"):
        validate_dataframe(df)


def test_validate_dataframe_non_float_amount():
    df = pd.DataFrame({"amount": [1, 2, 3]})
    with pytest.raises(AssertionError, match="'amount' must be float"):
        validate_dataframe(df)


def test_validate_dataframe_string_amount():
    df = pd.DataFrame({"amount": ["1.0", "2.0", "3.0"]})
    with pytest.raises(AssertionError, match="'amount' must be float"):
        validate_dataframe(df)


def test_validate_dataframe_empty():
    df = pd.DataFrame({"amount": []})
    validate_dataframe(df)


def test_validate_dataframe_with_nan():
    df = pd.DataFrame({"amount": [1.0, float('nan'), 3.0]})
    validate_dataframe(df)
