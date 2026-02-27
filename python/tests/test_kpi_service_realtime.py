"""Realtime KPI service tests."""

import asyncio

from python.apps.analytics.api.models import LoanRecord
from python.apps.analytics.api.service import KPIService


def test_calculate_kpis_for_portfolio_includes_collection_rate():
    service = KPIService(actor="test_user")
    loans = [
        LoanRecord(
            id="L1",
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.1,
            loan_status="current",
            total_scheduled=100.0,
            last_payment_amount=80.0,
        ),
        LoanRecord(
            id="L2",
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.2,
            loan_status="90+ days past due",
            total_scheduled=150.0,
            last_payment_amount=75.0,
        ),
    ]

    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}

    assert "COLLECTION_RATE" in kpi_map
    assert kpi_map["COLLECTION_RATE"].value == 62.0
    assert kpi_map["COLLECTION_RATE"].formula


def test_calculate_kpis_for_portfolio_collection_rate_defaults_to_zero():
    service = KPIService(actor="test_user")
    loans = [
        LoanRecord(
            id="L1",
            loan_amount=1000.0,
            principal_balance=800.0,
            interest_rate=0.12,
            loan_status="current",
        ),
        LoanRecord(
            id="L2",
            loan_amount=1200.0,
            principal_balance=900.0,
            interest_rate=0.15,
            loan_status="default",
        ),
    ]

    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}

    assert "COLLECTION_RATE" in kpi_map
    assert kpi_map["COLLECTION_RATE"].value == 0.0
