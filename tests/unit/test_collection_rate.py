import pandas as pd
import pytest

from python.kpis.collection_rate import calculate_collection_rate


def test_collection_rate_sample_row():
    df = pd.DataFrame([
        {
            "segment": "Consumer",
            "measurement_date": "2025-01-31",
            "dpd_90_plus_usd": 32500,
            "total_receivable_usd": 1_000_000,
            "total_eligible_usd": 1_000_000,
            "cash_available_usd": 972_000,
        }
    ])
    assert calculate_collection_rate(df) == pytest.approx(97.2, rel=1e-3)


def test_collection_rate_empty_df_returns_zero():
    assert calculate_collection_rate(pd.DataFrame()) == 0.0


def test_collection_rate_zero_denominator_returns_zero():
    df = pd.DataFrame(
        {"cash_available_usd": [1000], "total_eligible_usd": [0]}
    )
    assert calculate_collection_rate(df) == 0.0


def test_collection_rate_coerces_non_numeric():
    df = pd.DataFrame(
        {
            "cash_available_usd": ["notanumber", None],
            "total_eligible_usd": ["100000", "100000"],
        }
    )
    assert calculate_collection_rate(df) == 0.0


def test_collection_rate_aggregates_rows():
    df = pd.DataFrame(
        {
            "cash_available_usd": [972_000, 972_000],
            "total_eligible_usd": [1_000_000, 1_000_000],
        }
    )
    assert calculate_collection_rate(df) == pytest.approx(97.2, rel=1e-3)
