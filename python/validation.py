"""
Module for data validation utilities and functions.
"""


def validate_dataframe(df):
    """Validate that the DataFrame contains required columns and types."""
    assert 'amount' in df.columns, "Missing 'amount' column"
    assert df['amount'].dtype == float, "'amount' must be float"
    # Add more checks as needed
