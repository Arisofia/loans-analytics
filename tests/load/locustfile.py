"""Locust load profile for Abaco Analytics API."""

from __future__ import annotations

import os

from locust import HttpUser, between, task


def _auth_headers() -> dict[str, str]:
    token = os.getenv("ABACO_BEARER_TOKEN", "").strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _sample_payload() -> dict:
    return {
        "loans": [
            {
                "id": "L-1001",
                "loan_amount": 15000.0,
                "appraised_value": 18500.0,
                "borrower_income": 54000.0,
                "monthly_debt": 850.0,
                "loan_status": "current",
                "interest_rate": 0.165,
                "principal_balance": 12750.0,
            },
            {
                "id": "L-1002",
                "loan_amount": 9200.0,
                "appraised_value": 9800.0,
                "borrower_income": 42000.0,
                "monthly_debt": 1000.0,
                "loan_status": "30-59 days past due",
                "interest_rate": 0.22,
                "principal_balance": 8700.0,
            },
        ],
        "ltv_threshold": 80.0,
        "dti_threshold": 50.0,
    }


class AnalyticsApiUser(HttpUser):
    """Traffic model focused on KPI and risk endpoints."""

    wait_time = between(1.0, 3.0)
    host = os.getenv("ABACO_API_BASE_URL", "http://localhost:8000")

    @task(5)
    def health(self) -> None:
        self.client.get("/health", name="GET /health", headers=_auth_headers())

    @task(3)
    def kpis(self) -> None:
        self.client.post(
            "/analytics/kpis",
            json=_sample_payload(),
            name="POST /analytics/kpis",
            headers=_auth_headers(),
        )

    @task(2)
    def risk_alerts(self) -> None:
        self.client.post(
            "/analytics/risk-alerts",
            json=_sample_payload(),
            name="POST /analytics/risk-alerts",
            headers=_auth_headers(),
        )
