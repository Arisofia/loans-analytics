import pandas as pd
from src.kpis.collection_rate import calculate_collection_rate
from src.kpis.par_90 import calculate_par_90

SAMPLE_PATH = "data_samples/abaco_portfolio_sample.csv"


def test_par_90_is_weighted_by_segment():
    df = pd.read_csv(SAMPLE_PATH)
    overall, _ = calculate_par_90(df)
    weighted = 0.0
    for _, group in df.groupby("segment"):
        val, _ = calculate_par_90(group)
        weighted += val * group["total_receivable_usd"].sum() / df["total_receivable_usd"].sum()
    assert overall == weighted


def test_collection_rate_remains_above_thresholds():
    df = pd.read_csv(SAMPLE_PATH)
    val, _ = calculate_collection_rate(df)
    assert val >= 90.0
    for _, group in df.groupby("segment"):
        val_group, _ = calculate_collection_rate(group)
        assert val_group >= 90.0


def test_no_missing_segments_or_dates():
    df = pd.read_csv(SAMPLE_PATH)
    assert set(df["segment"].unique()) == {"Consumer", "SME"}
    assert not df["measurement_date"].isna().any()
