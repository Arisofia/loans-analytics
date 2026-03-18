"""OpenAPI contract checks for cohort analytics endpoint."""

from fastapi.testclient import TestClient

from backend.python.apps.analytics.api.main import app


def test_openapi_contains_cohort_analytics_endpoint():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    assert "/analytics/cohorts" in spec["paths"]
    post = spec["paths"]["/analytics/cohorts"]["post"]
    assert post["summary"] == "Origination Cohort Analytics"

    request_ref = post["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_ref = post["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref.endswith("/CohortAnalyticsRequest")
    assert response_ref.endswith("/CohortAnalyticsResponse")
