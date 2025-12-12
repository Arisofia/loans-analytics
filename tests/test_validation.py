import pandas as pd
import pytest
from python.validation import validate_dataframe


def test_validate_dataframe_valid():
    df = pd.DataFrame({"amount": [1.0, 2.0, 3.0]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_missing_amount_column():
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    with pytest.raises(AssertionError, match="Missing required column: amount"):
        validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_non_float_amount():
    df = pd.DataFrame({"amount": [1, 2, 3]})
    # ints are numeric; should pass
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_string_amount():
    df = pd.DataFrame({"amount": ["1.0", "2.0", "3.0"]})
    with pytest.raises(AssertionError, match="must be numeric"):
        validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_empty():
    df = pd.DataFrame({"amount": []})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_with_nan():
    df = pd.DataFrame({"amount": [1.0, float('nan'), 3.0]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])
