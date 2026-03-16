from __future__ import annotations

import math

import pandas as pd
import pytest

from src.zero_cost.local_migration_etl import (
    MAX_NOT_SPECIFIED_LOG_ROWS,
    build_not_specified_log,
    reconcile_payments,
)
from src.zero_cost.xirr import xirr


def test_xirr_known_case_precision():
    cashflows = [-1500.0, 200.0, 350.0, 450.0, 700.0]
    dates = [
        "2025-01-01",
        "2025-03-10",
        "2025-06-01",
        "2025-09-15",
        "2026-01-01",
    ]
    rate = xirr(cashflows, dates)
    assert math.isfinite(rate)
    assert rate == pytest.approx(0.1965354, rel=1e-3)


def test_xirr_requires_sign_change():
    with pytest.raises(ValueError):
        xirr([100, 200, 300], ["2025-01-01", "2025-02-01", "2025-03-01"])


def test_reconcile_payments_marks_missing_and_mismatch_reason_codes():
    fact_schedule = pd.DataFrame(
        {
            "loan_id": ["L1", "L1", "L2"],
            "scheduled_date": ["2025-02-01", "2025-03-01", "2025-02-15"],
            "scheduled_total": [100.0, 100.0, 75.0],
        }
    )
    fact_real_payment = pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3"],
            "payment_date": ["2025-02-01", "2025-02-15", "2025-02-20"],
            "paid_total": [100.0, 70.0, 50.0],
        }
    )

    reconciliation, unmatched = reconcile_payments(fact_schedule, fact_real_payment)

    assert "status" in reconciliation.columns
    assert set(unmatched["reason_code"]) == {
        "scheduled_without_payment",
        "amount_mismatch",
        "payment_without_schedule",
    }
    assert not unmatched["reason_code"].isna().any()
    assert (unmatched["reason_code"].str.strip() != "").all()


def test_build_not_specified_log_caps_at_max_rows(caplog):
    """build_not_specified_log should cap output at MAX_NOT_SPECIFIED_LOG_ROWS."""
    import logging

    n_rows = MAX_NOT_SPECIFIED_LOG_ROWS + 50
    df = pd.DataFrame({"col_a": [None] * n_rows, "col_b": [""] * n_rows})
    with caplog.at_level(logging.WARNING, logger="src.zero_cost.local_migration_etl"):
        result = build_not_specified_log(df, "test_table")

    assert len(result) == MAX_NOT_SPECIFIED_LOG_ROWS
    assert any("Truncated" in m for m in caplog.messages)


def test_reconcile_payments_captures_null_loan_id():
    """Rows with null loan_id should appear in unmatched with explicit reason_code."""
    fact_schedule = pd.DataFrame(
        {
            "loan_id": ["L1", None],
            "scheduled_date": ["2025-02-01", "2025-02-01"],
            "scheduled_total": [100.0, 50.0],
        }
    )
    fact_real_payment = pd.DataFrame(
        {
            "loan_id": ["L1", None],
            "payment_date": ["2025-02-01", "2025-02-01"],
            "paid_total": [100.0, 50.0],
        }
    )

    _, unmatched = reconcile_payments(fact_schedule, fact_real_payment)

    null_sched = unmatched[unmatched["reason_code"] == "missing_loan_id_schedule"]
    null_paid = unmatched[unmatched["reason_code"] == "missing_loan_id_payment"]
    assert len(null_sched) == 1, "Null loan_id schedule row should be captured"
    assert len(null_paid) == 1, "Null loan_id payment row should be captured"


def test_reconcile_payments_captures_invalid_dates_no_duplicates():
    """Rows with invalid dates should appear in unmatched; rows with both invalid
    date AND null loan_id should only be captured once (invalid date takes priority)."""
    fact_schedule = pd.DataFrame(
        {
            "loan_id": ["L1", None, "L2"],
            "scheduled_date": ["not-a-date", "not-a-date", "2025-02-01"],
            "scheduled_total": [100.0, 50.0, 75.0],
        }
    )
    fact_real_payment = pd.DataFrame(
        {
            "loan_id": ["L1", "L2"],
            "payment_date": ["2025-02-01", "not-a-date"],
            "paid_total": [100.0, 75.0],
        }
    )

    _, unmatched = reconcile_payments(fact_schedule, fact_real_payment)

    invalid_sched = unmatched[unmatched["reason_code"] == "invalid_scheduled_date"]
    invalid_paid = unmatched[unmatched["reason_code"] == "invalid_payment_date"]

    # Both schedule rows with invalid date (including the null loan_id one) are captured
    assert len(invalid_sched) == 2
    assert len(invalid_paid) == 1

    # The row with both null loan_id AND invalid date should not appear in missing_loan_id_*
    # — it should only appear once under invalid_scheduled_date (no duplicates)
    missing_loan = unmatched[unmatched["reason_code"] == "missing_loan_id_schedule"]
    all_refs = list(invalid_sched.index) + list(missing_loan.index)
    assert len(all_refs) == len(set(all_refs)), "No row should be logged twice"
