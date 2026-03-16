from __future__ import annotations

import math

import pandas as pd
import pytest

from src.zero_cost.local_migration_etl import reconcile_payments
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
