import pandas as pd
import pytest

from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.par_90 import calculate_par_90


def test_collection_rate_with_standard_columns():
    df = pd.DataFrame(
        {
            "payments_collected": [80.0, 90.0],
            "payments_due": [100.0, 100.0],
        }
    )

    value, context = calculate_collection_rate(df)

    assert value == 85.0
    assert context["rows_processed"] == 2
    assert context["collected_column"] == "payments_collected"
    assert context["due_column"] == "payments_due"


def test_collection_rate_with_real_dataset_columns():
    df = pd.DataFrame(
        {
            "last_payment_amount": [500.0, 1000.0],
            "total_scheduled": [1000.0, 2000.0],
        }
    )

    value, context = calculate_collection_rate(df)

    assert value == 50.0
    assert context["collected_column"] == "last_payment_amount"
    assert context["due_column"] == "total_scheduled"


def test_collection_rate_missing_columns_returns_context():
    df = pd.DataFrame({"amount": [1, 2, 3]})

    value, context = calculate_collection_rate(df)

    assert value == 0.0
    assert context["calculation_status"] == "missing_columns"
    assert "payments_collected" in context["missing_columns"]


def test_par_90_primary_formula():
    df = pd.DataFrame(
        {
            "dpd_90_plus_usd": [100.0, 50.0],
            "total_receivable_usd": [1000.0, 500.0],
        }
    )

    assert calculate_par_90(df) == 10.0


def test_par_90_fallback_from_days_past_due_and_outstanding_balance():
    df = pd.DataFrame(
        {
            "days_past_due": [0, 95, 120],
            "outstanding_balance": [100.0, 300.0, 100.0],
            "principal_amount": [1000.0, 1000.0, 1000.0],
        }
    )

    assert calculate_par_90(df) == 13.33


def test_par_90_missing_columns_raises():
    df = pd.DataFrame({"foo": [1]})

    with pytest.raises(ValueError, match="Missing required columns"):
        calculate_par_90(df)
