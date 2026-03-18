"""Tests for deterministic stress-testing analytics in KPI service."""

import asyncio

from backend.python.apps.analytics.api.models import LoanRecord, StressTestResponse
from backend.python.apps.analytics.api.service import KPIService


def _stress_loans() -> list[LoanRecord]:
    return [
        LoanRecord(
            id="L1",
            borrower_id="B1",
            loan_amount=1000.0,
            principal_balance=900.0,
            interest_rate=0.22,
            loan_status="current",
            days_past_due=0,
            total_scheduled=300.0,
            last_payment_amount=240.0,
            recovery_value=0.0,
            tpv=1200.0,
        ),
        LoanRecord(
            id="L2",
            borrower_id="B2",
            loan_amount=1500.0,
            principal_balance=1300.0,
            interest_rate=0.28,
            loan_status="60-89 days past due",
            days_past_due=75,
            total_scheduled=400.0,
            last_payment_amount=220.0,
            recovery_value=60.0,
            tpv=900.0,
        ),
        LoanRecord(
            id="L3",
            borrower_id="B2",
            loan_amount=800.0,
            principal_balance=700.0,
            interest_rate=0.3,
            loan_status="default",
            days_past_due=120,
            total_scheduled=250.0,
            last_payment_amount=80.0,
            recovery_value=120.0,
            tpv=600.0,
        ),
    ]


def test_calculate_stress_test_returns_expected_structure_and_directionality():
    service = KPIService(actor="test_user")
    response = asyncio.run(service.calculate_stress_test(loans=_stress_loans()))

    assert isinstance(response, StressTestResponse)
    assert response.scenario_id
    assert response.baseline.par30_pct >= 0.0
    assert response.stressed.par30_pct >= response.baseline.par30_pct
    assert response.stressed.collection_rate_pct <= response.baseline.collection_rate_pct
    assert response.stressed.revenue_forecast_6m_usd <= response.baseline.revenue_forecast_6m_usd
    assert response.deltas.expected_credit_loss_usd == round(
        response.stressed.expected_credit_loss_usd - response.baseline.expected_credit_loss_usd,
        2,
    )


def test_calculate_stress_test_handles_empty_inputs():
    service = KPIService(actor="test_user")
    response = asyncio.run(service.calculate_stress_test(loans=[]))

    assert response.baseline.par30_pct == 0.0
    assert response.stressed.par30_pct == 0.0
    assert response.alerts == []

