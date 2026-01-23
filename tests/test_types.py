from src.pipeline.types import ParRow, validate_par_row


def test_validate_par_row_accepts_expected_structure() -> None:
    p: ParRow = {
        "reporting_date": "2025-12-31",
        "outstanding_balance_usd": 500000.0,
        "par_7_balance_usd": 50000.0,
    }
    assert validate_par_row(p)
