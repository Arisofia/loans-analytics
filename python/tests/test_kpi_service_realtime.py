"""Realtime KPI service tests."""

import asyncio
from datetime import datetime

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


def test_calculate_kpis_for_portfolio_includes_expanded_realtime_kpis():
    service = KPIService(actor="test_user")
    month_start = datetime.now().replace(day=2, hour=0, minute=0, second=0, microsecond=0)
    loans = [
        LoanRecord(
            id="L1",
            borrower_id="B1",
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.1,
            loan_status="current",
            total_scheduled=100.0,
            last_payment_amount=80.0,
            current_balance=200.0,
            payment_frequency="bullet",
            term_months=6.0,
            origination_date=month_start,
        ),
        LoanRecord(
            id="L2",
            borrower_id="B1",
            loan_amount=1500.0,
            principal_balance=500.0,
            interest_rate=0.2,
            loan_status="default",
            days_past_due=120.0,
            total_scheduled=200.0,
            last_payment_amount=50.0,
            recovery_value=100.0,
            current_balance=300.0,
            payment_frequency="manual",
            term_months=12.0,
            origination_date=month_start,
        ),
    ]

    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}

    assert kpi_map["LOSS_RATE"].value == 20.0
    assert kpi_map["RECOVERY_RATE"].value == 20.0
    assert kpi_map["CASH_ON_HAND"].value == 500.0
    assert kpi_map["AVERAGE_LOAN_SIZE"].value == 1250.0
    assert kpi_map["DISBURSEMENT_VOLUME_MTD"].value == 2500.0
    assert kpi_map["NEW_LOANS_COUNT_MTD"].value == 2.0
    assert kpi_map["ACTIVE_BORROWERS"].value == 1.0
    assert kpi_map["REPEAT_BORROWER_RATE"].value == 100.0
    assert kpi_map["AUTOMATION_RATE"].value == 50.0
    assert kpi_map["PROCESSING_TIME_AVG"].value == 9.0
