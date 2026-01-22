import pandas as pd
import pytest

from src.pipeline.data_validation import (ANALYTICS_NUMERIC_COLUMNS,
                                          NUMERIC_COLUMNS,
                                          REQUIRED_ANALYTICS_COLUMNS,
                                          find_column, validate_dataframe,
                                          validate_numeric_bounds)


def test_validate_dataframe_valid():
    # Test that a valid DataFrame passes validation
    df = pd.DataFrame({"amount": [1.0, 2.0, 3.0]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_missing_amount_column():
    # Test that missing required columns raises ValueError
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="Missing required column: amount"):
        validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_non_float_amount():
    # Test that integer values are accepted as numeric
    df = pd.DataFrame({"amount": [1, 2, 3]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_string_amount():
    # Test that string values in numeric columns raise ValueError
    df = pd.DataFrame({"amount": ["1.0", "2.0", "3.0"]})
    with pytest.raises(ValueError, match="must be numeric"):
        validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_empty():
    # Test that an empty DataFrame with required columns passes validation
    df = pd.DataFrame({"amount": []})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validate_dataframe_with_nan():
    # Test that NaN values in numeric columns are accepted
    df = pd.DataFrame({"amount": [1.0, float("nan"), 3.0]})
    validate_dataframe(df, required_columns=["amount"], numeric_columns=["amount"])


def test_validation_constants_integrity():
    """Verify that validation constants are correctly defined."""
    assert isinstance(REQUIRED_ANALYTICS_COLUMNS, list)
    assert len(REQUIRED_ANALYTICS_COLUMNS) > 0
    assert "loan_amount" in REQUIRED_ANALYTICS_COLUMNS

    assert isinstance(NUMERIC_COLUMNS, list)
    assert len(NUMERIC_COLUMNS) > 0
    assert "total_receivable_usd" in NUMERIC_COLUMNS


def test_analytics_numeric_columns_subset():
    """Verify that ANALYTICS_NUMERIC_COLUMNS is a subset of REQUIRED_ANALYTICS_COLUMNS."""
    assert set(ANALYTICS_NUMERIC_COLUMNS).issubset(set(REQUIRED_ANALYTICS_COLUMNS))


def test_validate_numeric_bounds():
    """Test validate_numeric_bounds checks for non-negative values."""
    df = pd.DataFrame({"positive": [1, 2, 3], "negative": [1, -2, 3], "mixed": [0, 1, 2]})
    # Test with specific columns
    results = validate_numeric_bounds(df, columns=["positive", "negative"])
    assert results["positive_non_negative"] is True
    assert results["negative_non_negative"] is False


def test_find_column_logic():
    """Test the fuzzy column matching logic."""
    df = pd.DataFrame({"ExactMatch": [1], "lower_case": [2], "Substring_Match": [3]})

    # 1. Exact match
    assert find_column(df, ["ExactMatch"]) == "ExactMatch"

    # 2. Case-insensitive match
    assert find_column(df, ["Lower_Case"]) == "lower_case"

    # 3. Substring match
    assert find_column(df, ["string"]) == "Substring_Match"

    # 4. Priority (Exact over substring)
    df2 = pd.DataFrame({"match": [1], "matcher": [2]})
    assert find_column(df2, ["match"]) == "match"

    # 5. None found
    assert find_column(df, ["missing"]) is None


def test_validate_dataframe_missing_multiple_columns():
    # Test that multiple missing columns raise ValueError with plural message
    df = pd.DataFrame({"value": [1.0]})
    with pytest.raises(ValueError, match="Missing required columns: amount, currency"):
        validate_dataframe(df, required_columns=["amount", "currency"])


def test_find_column_edge_cases():
    """Test find_column with empty inputs."""
    df = pd.DataFrame({"A": [1]})
    assert find_column(df, []) is None

    empty_df = pd.DataFrame()
    assert find_column(empty_df, ["A"]) is None


def test_safe_numeric_empty():
    """Test safe_numeric with empty input."""
    from src.pipeline.data_validation import safe_numeric

    s = pd.Series([], dtype=object)
    res = safe_numeric(s)
    assert res.empty


def test_validate_percentage_bounds():
    from src.pipeline.data_validation import validate_percentage_bounds

    df = pd.DataFrame(
        {
            "valid_pct": [0, 50, 100],
            "invalid_pct": [-1, 50, 101],
            "rate": [0, 100, 99.9],
            "bad_rate": [0, -0.1, 100.1],
        }
    )
    results = validate_percentage_bounds(
        df, columns=["valid_pct", "invalid_pct", "rate", "bad_rate"]
    )
    assert results["valid_pct_in_0_100"]
    assert not results["invalid_pct_in_0_100"]
    assert results["rate_in_0_100"]
    assert not results["bad_rate_in_0_100"]


def test_validate_iso8601_dates():
    from src.pipeline.data_validation import validate_iso8601_dates

    df = pd.DataFrame(
        {
            "good_date": ["2025-12-14", "2024-01-01"],
            "bad_date": ["2025/12/14", "14-12-2025"],
            "iso_datetime": ["2025-12-14T12:34:56Z", "2025-12-14T23:59:59+00:00"],
            "mixed": ["2025-12-14", "not-a-date"],
            "nulls": [None, "2025-12-14"],
        }
    )
    results = validate_iso8601_dates(
        df, columns=["good_date", "bad_date", "iso_datetime", "mixed", "nulls"]
    )
    assert results["good_date_iso8601"]
    assert not results["bad_date_iso8601"]
    assert results["iso_datetime_iso8601"]
    assert not results["mixed_iso8601"]
    assert results["nulls_iso8601"]
