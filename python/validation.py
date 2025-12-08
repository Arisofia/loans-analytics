
"""
Module for data validation utilities and functions.
"""



def validate_dataframe(df):
    assert 'amount' in df.columns, "Missing 'amount' column"
    assert df['amount'].dtype == float, "'amount' must be float"
    # Add more checks as needed
