"""OpenAPI contract checks for advanced risk endpoint."""

from fastapi.testclient import TestClient

from backend.python.apps.analytics.api.main import app


def test_openapi_contains_advanced_risk_endpoint_and_schema_example():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200

    spec = response.json()
    assert "/analytics/advanced-risk" in spec["paths"]

    post = spec["paths"]["/analytics/advanced-risk"]["post"]
    assert post["summary"] == "Advanced Risk KPI Snapshot"

    schema_ref = post["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert schema_ref.endswith("/AdvancedRiskResponse")

    advanced_schema = spec["components"]["schemas"]["AdvancedRiskResponse"]
    assert "example" in advanced_schema
    example = advanced_schema["example"]
    assert "par60" in example
    assert "dpd_buckets" in example
    assert isinstance(example["dpd_buckets"], list)
    assert example["dpd_buckets"][0]["bucket"] == "current"
