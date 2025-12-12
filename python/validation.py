"""
Module for data validation utilities and functions.
"""


def validate_dataframe(df, required_columns=None, numeric_columns=None):
    """
    Validate that the DataFrame contains required columns and types.
    Args:
        df (pd.DataFrame): DataFrame to validate.
        required_columns (list[str], optional): Columns that must be present.
        numeric_columns (list[str], optional): Columns that must be numeric.
    Raises:
        AssertionError: If validation fails.
    """
    if required_columns:
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
    if numeric_columns:
        for col in numeric_columns:
            assert col in df.columns, f"Missing required numeric column: {col}"
            assert pd.api.types.is_numeric_dtype(df[col]), f"Column '{col}' must be numeric"
