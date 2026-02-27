"""Realtime KPI endpoint contract tests."""

from datetime import datetime

from fastapi.testclient import TestClient

from python.apps.analytics.api.main import app


def test_calculate_all_kpis_includes_collection_rate_for_realtime_input():
    client = TestClient(app)
    payload = {
        "loans": [
            {
                "id": "L1",
                "loan_amount": 1000.0,
                "principal_balance": 1000.0,
                "interest_rate": 0.1,
                "loan_status": "current",
                "total_scheduled": 100.0,
                "last_payment_amount": 80.0,
            },
            {
                "id": "L2",
                "loan_amount": 1000.0,
                "principal_balance": 1000.0,
                "interest_rate": 0.2,
                "loan_status": "90+ days past due",
                "total_scheduled": 150.0,
                "last_payment_amount": 75.0,
            },
        ]
    }
    response = client.post("/analytics/kpis", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["CollectionRate"] is not None
    assert body["CollectionRate"]["id"] == "COLLECTION_RATE"
    assert body["CollectionRate"]["value"] == 62.0


def test_calculate_all_kpis_includes_expanded_metrics():
    client = TestClient(app)
    month_start = datetime.now().replace(day=2, hour=0, minute=0, second=0, microsecond=0)
    payload = {
        "loans": [
            {
                "id": "L1",
                "borrower_id": "B1",
                "loan_amount": 1000.0,
                "principal_balance": 1000.0,
                "interest_rate": 0.1,
                "loan_status": "current",
                "total_scheduled": 100.0,
                "last_payment_amount": 80.0,
                "current_balance": 200.0,
                "payment_frequency": "bullet",
                "term_months": 6.0,
                "origination_date": month_start.isoformat(),
            },
            {
                "id": "L2",
                "borrower_id": "B1",
                "loan_amount": 1500.0,
                "principal_balance": 500.0,
                "interest_rate": 0.2,
                "loan_status": "default",
                "days_past_due": 120.0,
                "total_scheduled": 200.0,
                "last_payment_amount": 50.0,
                "recovery_value": 100.0,
                "current_balance": 300.0,
                "payment_frequency": "manual",
                "term_months": 12.0,
                "origination_date": month_start.isoformat(),
            },
        ]
    }
    response = client.post("/analytics/kpis", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["LossRate"]["id"] == "LOSS_RATE"
    assert body["LossRate"]["value"] == 20.0
    assert body["RecoveryRate"]["value"] == 20.0
    assert body["CashOnHand"]["value"] == 500.0
    assert body["AverageLoanSize"]["value"] == 1250.0
    assert body["DisbursementVolumeMTD"]["value"] == 2500.0
    assert body["NewLoansCountMTD"]["value"] == 2.0
    assert body["ActiveBorrowers"]["value"] == 1.0
    assert body["RepeatBorrowerRate"]["value"] == 100.0
    assert body["AutomationRate"]["value"] == 50.0
    assert body["ProcessingTimeAvg"]["value"] == 9.0
