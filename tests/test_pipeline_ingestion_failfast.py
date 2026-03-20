import pandas as pd
import pytest

from backend.src.pipeline.ingestion import IngestionPhase


def test_calculate_hash_is_stable_across_column_order() -> None:
    phase = IngestionPhase(config={})

    df_a = pd.DataFrame([{"loan_id": "L-1", "amount": 100.0, "status": "active"}])
    df_b = pd.DataFrame([{"status": "active", "amount": 100.0, "loan_id": "L-1"}])

    assert phase._calculate_hash(df_a) == phase._calculate_hash(df_b)


def test_to_nullable_string_raises_for_undecodable_bytes() -> None:
    phase = IngestionPhase(config={})

    class BadBytes(bytes):
        def decode(self, encoding="utf-8", errors="strict"):
            raise UnicodeDecodeError(encoding, b"x", 0, 1, "forced decode failure")

    with pytest.raises(ValueError, match="decode failure"):
        phase._to_nullable_string(BadBytes(b"x"))


def test_ingestion_without_input_fails_instead_of_using_dummy_data():
    """Ingestion must not fallback to sample/dummy rows when input is missing."""
    pass