"""Tests for roll-rate and cure-rate analytics in KPI service."""

import asyncio

from backend.python.apps.analytics.api.models import LoanRecord, RollRateAnalyticsResponse
from backend.python.apps.analytics.api.service import KPIService


def _roll_rate_loans() -> list[LoanRecord]:
    return [
        LoanRecord(
            id="L1",
            borrower_id="B1",
            loan_amount=1200.0,
            principal_balance=1000.0,
            interest_rate=0.2,
            loan_status="current",
            days_past_due=0,
            previous_loan_status="current",
            previous_days_past_due=0,
            previous_principal_balance=1000.0,
        ),
        LoanRecord(
            id="L2",
            borrower_id="B2",
            loan_amount=2400.0,
            principal_balance=2000.0,
            interest_rate=0.24,
            loan_status="30-59 days past due",
            days_past_due=45,
            previous_loan_status="current",
            previous_days_past_due=0,
            previous_principal_balance=2100.0,
        ),
        LoanRecord(
            id="L3",
            borrower_id="B3",
            loan_amount=2100.0,
            principal_balance=1700.0,
            interest_rate=0.21,
            loan_status="current",
            days_past_due=0,
            previous_loan_status="30-59 days past due",
            previous_days_past_due=45,
            previous_principal_balance=1800.0,
        ),
        LoanRecord(
            id="L4",
            borrower_id="B4",
            loan_amount=6200.0,
            principal_balance=5000.0,
            interest_rate=0.26,
            loan_status="default",
            days_past_due=120,
            previous_loan_status="60-89 days past due",
            previous_days_past_due=75,
            previous_principal_balance=5200.0,
        ),
        LoanRecord(
            id="L5",
            borrower_id="B5",
            loan_amount=4600.0,
            principal_balance=4300.0,
            interest_rate=0.22,
            loan_status="60-89 days past due",
            days_past_due=80,
            previous_loan_status="default",
            previous_days_past_due=110,
            previous_principal_balance=4400.0,
        ),
    ]


def test_calculate_roll_rate_analytics_returns_transition_matrix_and_summary():
    service = KPIService(actor="test_user")
    response = asyncio.run(service.calculate_roll_rate_analytics(loans=_roll_rate_loans()))

    assert isinstance(response, RollRateAnalyticsResponse)
    assert response.summary.total_loans == 5
    assert response.summary.historical_coverage_pct == 100.0
    assert response.summary.portfolio_cure_rate_pct == 33.33
    assert response.summary.portfolio_roll_forward_rate_pct == 50.0
    assert response.summary.worst_migration_path == "61_90->90_plus"
    assert response.summary.best_cure_source == "31_60"

    transitions = {(row.from_bucket, row.to_bucket): row for row in response.transition_matrix}
    assert ("31_60", "current") in transitions
    assert transitions[("31_60", "current")].loan_count == 1
    assert transitions[("31_60", "current")].loan_share_pct == 100.0

    buckets = {row.from_bucket: row for row in response.bucket_summaries}
    assert buckets["31_60"].cure_rate_pct == 100.0
    assert buckets["61_90"].roll_forward_rate_pct == 100.0
    assert buckets["90_plus"].stability_rate_pct == 0.0
