import pandas as pd
import pytest
from python.validation import validate_dataframe


def test_validate_dataframe_valid():
    # Coderabbit: Test that a valid DataFrame passes validation
    df = pd.DataFrame({"amount": [1.0, 2.0, 3.0]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_missing_amount_column():
    # Coderabbit: Test that missing required columns raises ValueError
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_non_float_amount():
    # Coderabbit: Test that integer values are accepted as numeric
    df = pd.DataFrame({"amount": [1, 2, 3]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_string_amount():
    # Coderabbit: Test that string values in numeric columns raise ValueError
    df = pd.DataFrame({"amount": ["1.0", "2.0", "3.0"]})
    with pytest.raises(ValueError, match="must be numeric"):
        validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_empty():
    # Coderabbit: Test that an empty DataFrame with required columns passes validation
    df = pd.DataFrame({"amount": []})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_with_nan():
    # Coderabbit: Test that NaN values in numeric columns are accepted
    df = pd.DataFrame({"amount": [1.0, float('nan'), 3.0]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])
