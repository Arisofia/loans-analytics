"""Decision dashboard and portfolio health score contract tests."""

from datetime import datetime

from fastapi.testclient import TestClient

from python.apps.analytics.api.main import app
from python.kpis.health_score import calculate_portfolio_health_score


def _sample_loans_payload() -> dict:
    month_start = datetime.now().replace(day=2, hour=0, minute=0, second=0, microsecond=0)
    return {
        "loans": [
            {
                "id": "L1",
                "borrower_id": "B1",
                "loan_amount": 1000.0,
                "principal_balance": 1000.0,
                "interest_rate": 0.1,
                "loan_status": "current",
                "days_past_due": 0.0,
                "total_scheduled": 100.0,
                "last_payment_amount": 90.0,
                "origination_date": month_start.isoformat(),
                "tpv": 1000.0,
            },
            {
                "id": "L2",
                "borrower_id": "B2",
                "loan_amount": 1500.0,
                "principal_balance": 1200.0,
                "interest_rate": 0.18,
                "loan_status": "90+ days past due",
                "days_past_due": 120.0,
                "total_scheduled": 180.0,
                "last_payment_amount": 20.0,
                "origination_date": month_start.isoformat(),
                "tpv": 1200.0,
            },
        ]
    }


def test_portfolio_health_score_traffic_light_levels():
    healthy = calculate_portfolio_health_score(
        par30=1.0,
        collection_rate=98.0,
        npl=1.0,
        cost_of_risk=0.5,
        default_rate=0.5,
    )
    critical = calculate_portfolio_health_score(
        par30=25.0,
        collection_rate=60.0,
        npl=20.0,
        cost_of_risk=12.0,
        default_rate=12.0,
    )

    assert healthy["traffic_light"] == "healthy"
    assert healthy["score"] >= 80.0
    assert critical["traffic_light"] == "critical"
    assert critical["score"] < 40.0


def test_decision_dashboard_endpoint_contract():
    client = TestClient(app)
    response = client.post("/analytics/decision-dashboard", json=_sample_loans_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["portfolio_health"]["score"] >= 0.0
    assert body["portfolio_health"]["score"] <= 100.0
    assert body["portfolio_health"]["traffic_light"] in {"healthy", "at_risk", "warning", "critical"}
    assert len(body["risk_stratification"]["decision_flags"]) > 0
    assert body["risk_heatmap"]["status"] in {"success", "no_data"}
    assert "npl" in body["unit_economics"]
    assert len(body["kpis"]) > 0
    assert len(body["recommendations"]) > 0


def test_executive_summary_includes_risk_kpis_and_portfolio_health():
    client = TestClient(app)
    response = client.post("/analytics/executive-summary", json=_sample_loans_payload())
    assert response.status_code == 200

    body = response.json()
    assert "risk_kpis" in body
    assert len(body["risk_kpis"]) > 0
    assert body["risk_kpis"][0]["id"] is not None
    assert "portfolio_health" in body
    assert body["portfolio_health"]["traffic_light"] in {"healthy", "at_risk", "warning", "critical"}


def test_full_analysis_includes_unit_economics_and_portfolio_health():
    client = TestClient(app)
    response = client.post("/analytics/full-analysis", json=_sample_loans_payload())
    assert response.status_code == 200

    body = response.json()
    assert "unit_economics" in body
    assert body["unit_economics"]["npl"]["npl_ratio"] >= 0.0
    assert "portfolio_health" in body
    assert body["portfolio_health"]["score"] >= 0.0
