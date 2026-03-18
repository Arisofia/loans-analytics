"""Tests for cohort/vintage analytics calculations in KPI service."""

import asyncio
from datetime import datetime

from backend.python.apps.analytics.api.models import CohortAnalyticsResponse, LoanRecord
from backend.python.apps.analytics.api.service import KPIService


def _cohort_loans() -> list[LoanRecord]:
    jan = datetime(2026, 1, 15)
    feb = datetime(2026, 2, 10)
    return [
        LoanRecord(
            id="L1",
            borrower_id="B1",
            loan_amount=1000.0,
            principal_balance=900.0,
            interest_rate=0.2,
            loan_status="current",
            days_past_due=0,
            origination_date=jan,
            total_scheduled=200.0,
            last_payment_amount=190.0,
        ),
        LoanRecord(
            id="L2",
            borrower_id="B2",
            loan_amount=1500.0,
            principal_balance=1200.0,
            interest_rate=0.25,
            loan_status="90+ days past due",
            days_past_due=100,
            origination_date=jan,
            total_scheduled=300.0,
            last_payment_amount=120.0,
        ),
        LoanRecord(
            id="L3",
            borrower_id="B3",
            loan_amount=800.0,
            principal_balance=700.0,
            interest_rate=0.22,
            loan_status="default",
            days_past_due=120,
            origination_date=feb,
            total_scheduled=250.0,
            last_payment_amount=80.0,
        ),
    ]


def test_calculate_cohort_analytics_returns_grouped_metrics():
    service = KPIService(actor="test_user")
    response = asyncio.run(service.calculate_cohort_analytics(_cohort_loans()))

    assert isinstance(response, CohortAnalyticsResponse)
    assert response.summary.cohort_count == 2
    assert response.summary.total_loans == 3
    assert len(response.cohorts) == 2
    assert response.cohorts[0].cohort_month == "2026-01"
    assert response.cohorts[1].cohort_month == "2026-02"
    assert response.summary.highest_risk_cohort in {"2026-01", "2026-02"}
    assert response.summary.strongest_collection_cohort in {"2026-01", "2026-02"}

