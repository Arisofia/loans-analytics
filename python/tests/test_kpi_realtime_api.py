"""Realtime KPI endpoint contract tests."""

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
