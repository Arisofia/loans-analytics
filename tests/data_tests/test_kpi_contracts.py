import pandas as pd
import pytest

from python.kpi_engine import calculate_collection_rate, calculate_par_90

SAMPLE_PATH = "data_samples/abaco_portfolio_sample.csv"


def test_par_90_from_sample_data():
    df = pd.read_csv(SAMPLE_PATH)
    result = calculate_par_90(df)
    assert result == pytest.approx(3.25, rel=0.001), "PAR90 drift detected"


def test_collection_rate_calculation():
    df = pd.read_csv(SAMPLE_PATH)
    result = calculate_collection_rate(df)
    # Current sample data yields ~97.2%
    assert result == pytest.approx(97.2, rel=0.001), "Collection rate drift detected"


def test_segment_level_contracts():
    df = pd.read_csv(SAMPLE_PATH)
    consumer = df[df["segment"] == "Consumer"]
    sme = df[df["segment"] == "SME"]

    consumer_par_90 = calculate_par_90(consumer)
    sme_par_90 = calculate_par_90(sme)

    assert consumer_par_90 == pytest.approx(3.25, rel=0.001)
    assert sme_par_90 == pytest.approx(3.25, rel=0.001)

    consumer_collection = calculate_collection_rate(consumer)
    sme_collection = calculate_collection_rate(sme)

    assert consumer_collection == pytest.approx(97.2, rel=0.001)
    assert sme_collection == pytest.approx(97.2, rel=0.001)
