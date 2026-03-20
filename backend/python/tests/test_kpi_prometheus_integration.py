"""Prometheus integration tests for KPI API publishing."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.python.apps.analytics.api.main import app


def _sample_realtime_payload() -> dict:
    return {
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


def test_metrics_kpis_endpoint_returns_prometheus_text():
    client = TestClient(app)
    response = client.get("/metrics/kpis")

    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_calculate_kpis_publishes_threshold_metrics():
    client = TestClient(app)

    calc_response = client.post("/analytics/kpis", json=_sample_realtime_payload())
    assert calc_response.status_code == 200

    metrics_response = client.get("/metrics/kpis")
    assert metrics_response.status_code == 200
    body = metrics_response.text

    assert "kpi_threshold_status" in body
    assert "kpi_value" in body
    assert 'kpi_name="COLLECTION_RATE"' in body


def test_single_kpi_publishes_metric_labels():
    client = TestClient(app)

    single_response = client.post("/analytics/kpis/collection-rate", json=_sample_realtime_payload())
    assert single_response.status_code == 200

    metrics_response = client.get("/metrics/kpis")
    body = metrics_response.text

    assert 'kpi_name="COLLECTION_RATE"' in body
    assert "kpi_last_update_timestamp" in body
