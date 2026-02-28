"""API tests for /analytics/stress-test endpoint."""

from fastapi.testclient import TestClient

from python.apps.analytics.api.main import app


def _payload() -> dict:
    return {
        "loans": [
            {
                "id": "L1",
                "borrower_id": "B1",
                "loan_amount": 1000.0,
                "principal_balance": 900.0,
                "interest_rate": 0.22,
                "loan_status": "current",
                "days_past_due": 0,
                "total_scheduled": 300.0,
                "last_payment_amount": 240.0,
                "recovery_value": 0.0,
                "tpv": 1200.0,
            },
            {
                "id": "L2",
                "borrower_id": "B2",
                "loan_amount": 1500.0,
                "principal_balance": 1300.0,
                "interest_rate": 0.28,
                "loan_status": "60-89 days past due",
                "days_past_due": 75,
                "total_scheduled": 400.0,
                "last_payment_amount": 220.0,
                "recovery_value": 60.0,
                "tpv": 900.0,
            },
            {
                "id": "L3",
                "borrower_id": "B2",
                "loan_amount": 800.0,
                "principal_balance": 700.0,
                "interest_rate": 0.3,
                "loan_status": "default",
                "days_past_due": 120,
                "total_scheduled": 250.0,
                "last_payment_amount": 80.0,
                "recovery_value": 120.0,
                "tpv": 600.0,
            },
        ]
    }


def test_stress_test_endpoint_returns_baseline_and_stressed_metrics():
    client = TestClient(app)
    response = client.post("/analytics/stress-test", json=_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["scenario_id"]
    assert set(body.keys()) == {
        "scenario_id",
        "generated_at",
        "assumptions",
        "baseline",
        "stressed",
        "deltas",
        "alerts",
    }

    assert body["stressed"]["par30_pct"] >= body["baseline"]["par30_pct"]
    assert body["stressed"]["collection_rate_pct"] <= body["baseline"]["collection_rate_pct"]
    assert (
        body["stressed"]["expected_credit_loss_usd"] >= body["baseline"]["expected_credit_loss_usd"]
    )


def test_stress_test_endpoint_allows_custom_shocks():
    client = TestClient(app)
    payload = _payload()
    payload.update(
        {
            "par_deterioration_pct": 60.0,
            "collection_efficiency_pct": -35.0,
            "recovery_efficiency_pct": -45.0,
            "funding_cost_bps": 400.0,
        }
    )
    response = client.post("/analytics/stress-test", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["assumptions"]["par_deterioration_pct"] == 60.0
    assert body["assumptions"]["funding_cost_bps"] == 400.0
    assert body["stressed"]["gross_margin_pct"] <= body["baseline"]["gross_margin_pct"]
    assert len(body["alerts"]) >= 1
