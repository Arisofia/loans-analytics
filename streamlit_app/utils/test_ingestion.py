import pandas as pd

from streamlit_app.utils.ingestion import DataIngestionEngine


def test_normalize_dataframe_converts_numeric_strings():
    engine = DataIngestionEngine("https://example.com", "anon", {})
    df = pd.DataFrame(
        {
            "customer": ["A", "B"],
            "balance": ["100", "-250.50"],
            "limit": ["1000", "2000"],
            "dpd": ["0", "-3"],
            "facility_amount": ["5000", "-7500"],
            "delta": ["-10", "-3.5"],
            "optional_fee": ["100", "N/A"],
        }
    )

    normalized, _ = engine.normalize_dataframe(df, source_name="financial")

    assert normalized["customer"].dtype == df["customer"].dtype
    assert normalized["customer"].tolist() == df["customer"].tolist()

    assert pd.api.types.is_numeric_dtype(normalized["balance"])
    assert normalized["balance"].tolist() == [100.0, -250.5]

    assert pd.api.types.is_numeric_dtype(normalized["limit"])
    assert normalized["limit"].tolist() == [1000.0, 2000.0]

    assert pd.api.types.is_numeric_dtype(normalized["dpd"])
    assert normalized["dpd"].tolist() == [0.0, -3.0]

    assert pd.api.types.is_numeric_dtype(normalized["facility_amount"])
    assert normalized["facility_amount"].tolist() == [5000.0, -7500.0]

    assert pd.api.types.is_numeric_dtype(normalized["delta"])
    assert normalized["delta"].tolist() == [-10.0, -3.5]

    assert pd.api.types.is_numeric_dtype(normalized["optional_fee"])
    assert normalized["optional_fee"].iloc[0] == 100.0
    assert pd.isna(normalized["optional_fee"].iloc[1])
