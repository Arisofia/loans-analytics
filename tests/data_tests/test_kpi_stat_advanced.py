import pandas as pd

from python.kpi_engine import calculate_collection_rate, calculate_par_90

SAMPLE_PATH = "data_samples/abaco_portfolio_sample.csv"


def test_par_90_is_weighted_by_segment():
    df = pd.read_csv(SAMPLE_PATH)
    overall = calculate_par_90(df)
    weighted = sum(
        calculate_par_90(group)
        * group["total_receivable_usd"].sum()
        / df["total_receivable_usd"].sum()
        for _, group in df.groupby("segment")
    )
    assert overall == weighted


def test_collection_rate_remains_above_thresholds():
    df = pd.read_csv(SAMPLE_PATH)
    assert calculate_collection_rate(df) >= 90.0
    for _, group in df.groupby("segment"):
        assert calculate_collection_rate(group) >= 90.0


def test_no_missing_segments_or_dates():
    df = pd.read_csv(SAMPLE_PATH)
    assert set(df["segment"].unique()) == {"Consumer", "SME"}
    assert not df["measurement_date"].isna().any()
