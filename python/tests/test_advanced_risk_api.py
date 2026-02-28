"""API tests for advanced risk analytics endpoints."""

from fastapi.testclient import TestClient

from python.apps.analytics.api.main import app


def _sample_payload() -> dict:
    return {
        "loans": [
            {
                "id": "L1",
                "borrower_id": "B1",
                "loan_amount": 1000.0,
                "principal_balance": 900.0,
                "interest_rate": 0.2,
                "loan_status": "current",
                "days_past_due": 0,
                "total_scheduled": 200.0,
                "last_payment_amount": 150.0,
                "origination_fee": 20.0,
                "origination_fee_taxes": 2.0,
                "credit_score": 710.0,
            },
            {
                "id": "L2",
                "borrower_id": "B1",
                "loan_amount": 1200.0,
                "principal_balance": 1000.0,
                "interest_rate": 0.3,
                "loan_status": "default",
                "days_past_due": 110,
                "total_scheduled": 200.0,
                "last_payment_amount": 50.0,
                "recovery_value": 100.0,
                "origination_fee": 25.0,
                "origination_fee_taxes": 2.5,
                "credit_score": 660.0,
            },
        ]
    }


def test_advanced_risk_endpoint_returns_expected_shape():
    client = TestClient(app)
    response = client.post("/analytics/advanced-risk", json=_sample_payload())
    assert response.status_code == 200

    body = response.json()
    expected_top_level_keys = {
        "par30",
        "par60",
        "par90",
        "default_rate",
        "collections_coverage",
        "fee_yield",
        "total_yield",
        "recovery_rate",
        "concentration_hhi",
        "repeat_borrower_rate",
        "credit_quality_index",
        "total_loans",
        "dpd_buckets",
    }
    assert expected_top_level_keys.issubset(body.keys())
    assert body["total_loans"] == 2
    assert body["par90"] == 52.63
    assert len(body["dpd_buckets"]) == 5
    assert {bucket["bucket"] for bucket in body["dpd_buckets"]} == {
        "current",
        "1_30",
        "31_60",
        "61_90",
        "90_plus",
    }


def test_full_analysis_deterministic_summary_includes_advanced_metrics(monkeypatch):
    # Force deterministic local analytical fallback path.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    client = TestClient(app)
    response = client.post("/analytics/full-analysis", json=_sample_payload())
    assert response.status_code == 200

    body = response.json()
    summary = body["summary"]
    assert "Risk exposure (PAR60)" in summary
    assert "Severe delinquency (PAR90)" in summary
    assert "Collections coverage" in summary
    assert "Borrower Concentration (HHI)" in summary
    assert "Credit Quality Index" in summary
    assert "Customer Acquisition Cost (CAC)" in summary
    assert "Gross Margin" in summary
    assert "6-Month Revenue Forecast" in summary

    kpi_ids = {k["id"] for k in body["kpis"]}
    assert "PAR30" in kpi_ids
    assert "PAR90" in kpi_ids
    assert "DEFAULT_RATE" in kpi_ids
    assert "TOTAL_LOANS_COUNT" in kpi_ids
    assert "CAC" in kpi_ids
    assert "GROSS_MARGIN_PCT" in kpi_ids
    assert "REVENUE_FORECAST_6M" in kpi_ids
    assert "CHURN_90D" in kpi_ids

    recommendations = body["recommendations"]
    assert any("recovery" in rec.lower() for rec in recommendations)
    assert any("collection" in rec.lower() for rec in recommendations)
