import pandas as pd
import pytest

from python.data_validation import validate_df_basic


def make_valid_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "segment": "Consumer",
                "measurement_date": "2025-01-31",
                "dpd_90_plus_usd": "32500",
                "total_receivable_usd": "1000000",
                "total_eligible_usd": "1000000",
                "cash_available_usd": "972000",
            }
        ]
    )


def test_validate_df_basic_happy_path():
    df = make_valid_df()
    validate_df_basic(df)
    assert pd.api.types.is_datetime64_any_dtype(df["measurement_date"])
    assert pd.api.types.is_numeric_dtype(df["total_eligible_usd"])


def test_validate_df_basic_missing_columns():
    df = pd.DataFrame({"segment": ["Consumer"]})
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_df_basic(df)


def test_validate_df_basic_type_error():
    with pytest.raises(TypeError, match="Expected DataFrame"):
        validate_df_basic([1, 2, 3])
