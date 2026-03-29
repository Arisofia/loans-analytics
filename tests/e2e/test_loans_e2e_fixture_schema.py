import os
from pathlib import Path
import pytest
import pandas as pd

def test_loans_e2e_fixture_schema_up_to_date():
    """
    Fail fast if the E2E CSV fixture is missing or its schema drifts.
    This test intentionally does *not* use the csv_path fixture so that a missing
    file results in a hard failure rather than a skip.
    """
    default_path = Path(os.getenv('CSV_PATH', 'tests/fixtures/loans_e2e_fixture.csv')).resolve()

    # Ensure the default E2E fixture exists
    assert default_path.exists(), f"E2E CSV fixture is missing: {default_path}"

    # Validate schema/shape
    df = pd.read_csv(default_path)

    # Adjust this list to reflect the expected, stable schema of the loans E2E fixture.
    expected_columns = [
        "loan_id",
        "borrower_id",
        "amount",
        "status",
        "days_past_due",
        "outstanding_balance",
        "interest_rate",
        "last_payment_amount",
        "total_scheduled",
        "origination_date",
    ]

    assert list(df.columns) == expected_columns, (
        "E2E CSV fixture schema drift detected.\n"
        f"Expected columns: {expected_columns}\n"
        f"Actual columns:   {list(df.columns)}"
    )

    # Optional: guard against accidentally committing an empty/degenerate fixture
    assert not df.empty, "E2E CSV fixture should contain at least one row"
