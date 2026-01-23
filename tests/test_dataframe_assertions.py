import pandas as pd
import pytest
from src.pipeline.data_validation import assert_dataframe_schema


def test_assert_dataframe_schema_detects_missing_columns():
    df = pd.DataFrame({"total_receivable_usd": [100.0]})
    with pytest.raises(AssertionError, match="missing required columns"):
        assert_dataframe_schema(
            df,
            required_columns=["total_receivable_usd", "total_eligible_usd"],
            numeric_columns=["total_receivable_usd", "total_eligible_usd"],
            stage="assertion_test",
        )


def test_assert_dataframe_schema_detects_non_numeric_columns():
    df = pd.DataFrame(
        {
            "total_receivable_usd": [100.0],
            "total_eligible_usd": ["invalid"],
        }
    )
    with pytest.raises(AssertionError, match="non-numeric columns"):
        assert_dataframe_schema(
            df,
            required_columns=["total_receivable_usd", "total_eligible_usd"],
            numeric_columns=["total_receivable_usd", "total_eligible_usd"],
            stage="assertion_test",
        )
