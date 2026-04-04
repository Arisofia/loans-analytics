"""Tests for Finding 3: data quality profile must return score=0.0 for no-data inputs.

Validates the hardened behavior of ``get_data_quality_profile`` so that
None input and empty lists yield ``data_quality_score=0.0`` with explicit
issue messages, rather than a silent 100.0 "healthy" default.
"""

import pytest
from fastapi.testclient import TestClient

from backend.loans_analytics.apps.analytics.api.main import app

client = TestClient(app)


def test_data_quality_profile_none_loans_returns_zero_score():
    """POST with loans=null must return data_quality_score=0.0."""
    response = client.post("/data-quality/profile", json={"loans": None})
    assert response.status_code == 200
    body = response.json()
    assert body["data_quality_score"] == pytest.approx(0.0)
    assert any("unavailable" in issue.lower() for issue in body["issues"])


def test_data_quality_profile_empty_loans_returns_zero_score():
    """POST with loans=[] must return data_quality_score=0.0."""
    response = client.post("/data-quality/profile", json={"loans": []})
    assert response.status_code == 200
    body = response.json()
    assert body["data_quality_score"] == pytest.approx(0.0)
    assert any("unavailable" in issue.lower() or "empty" in issue.lower() for issue in body["issues"])


@pytest.mark.parametrize("payload", [{"loans": None}, {"loans": []}])
def test_data_quality_profile_no_silent_healthy_default(payload):
    """Neither None nor empty should ever produce score >= 50.0."""
    response = client.post("/data-quality/profile", json=payload)
    assert response.status_code == 200
    assert response.json()["data_quality_score"] < 50.0, (
        f"Score must be fail-closed (< 50) for payload {payload}"
    )
