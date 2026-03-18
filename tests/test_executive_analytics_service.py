import asyncio

from backend.python.apps.analytics.api.models import LoanRecord
from backend.python.apps.analytics.api.service import KPIService


def _sample_loans() -> list[LoanRecord]:
    return [
        LoanRecord(
            id="LN-001",
            loan_amount=15000,
            appraised_value=20000,
            borrower_income=3600,
            monthly_debt=900,
            loan_status="current",
            interest_rate=0.21,
            principal_balance=12000,
        ),
        LoanRecord(
            id="LN-002",
            loan_amount=10000,
            appraised_value=14000,
            borrower_income=2800,
            monthly_debt=800,
            loan_status="30-59 days past due",
            interest_rate=0.24,
            principal_balance=8500,
        ),
    ]


def _sample_payments() -> list[dict]:
    return [
        {
            "payment_date": "2025-11-05",
            "customer_id": "C-001",
            "payment_amount": 1400,
            "interest_payment": 280,
            "fee_payment": 65,
        },
        {
            "payment_date": "2025-12-08",
            "customer_id": "C-002",
            "payment_amount": 1200,
            "interest_payment": 250,
            "fee_payment": 55,
        },
        {
            "payment_date": "2026-01-12",
            "customer_id": "C-001",
            "payment_amount": 1600,
            "interest_payment": 320,
            "fee_payment": 70,
        },
    ]


def _sample_customers() -> list[dict]:
    return [
        {
            "customer_id": "C-001",
            "created_at": "2025-10-01",
            "marketing_spend": 450,
        },
        {
            "customer_id": "C-002",
            "created_at": "2025-10-15",
            "marketing_spend": 375,
        },
    ]


def test_executive_analytics_includes_strategic_confirmations():
    service = KPIService(actor="test")

    payload = asyncio.run(
        service.get_executive_analytics(
            loans=_sample_loans(),
            payments=_sample_payments(),
            customers=_sample_customers(),
        )
    )

    confirmations = payload["strategic_confirmations"]
    assert confirmations["cac_confirmed"] is True
    assert confirmations["ltv_confirmed"] is True
    assert confirmations["margin_confirmed"] is True
    assert confirmations["revenue_forecast_confirmed"] is True

    assert len(payload["revenue_forecast_6m"]) == 6
    assert len(payload["opportunity_prioritization"]) >= 1
    assert len(payload["churn_90d_metrics"]) >= 1
    assert payload["data_governance"].get("quality_score") is not None
