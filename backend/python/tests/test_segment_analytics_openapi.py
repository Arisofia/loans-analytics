"""OpenAPI contract checks for segment analytics endpoint."""

from fastapi.testclient import TestClient

from backend.python.apps.analytics.api.main import app


def test_openapi_contains_segment_analytics_endpoint():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    assert "/analytics/segments" in spec["paths"]
    post = spec["paths"]["/analytics/segments"]["post"]
    assert post["summary"] == "Segment Drill-down Analytics"

    request_ref = post["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_ref = post["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref.endswith("/SegmentAnalyticsRequest")
    assert response_ref.endswith("/SegmentAnalyticsResponse")

