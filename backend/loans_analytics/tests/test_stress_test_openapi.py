from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def test_openapi_contains_stress_test_endpoint_and_schema_refs():
    client = TestClient(app)
    response = client.get('/openapi.json')
    assert response.status_code == 200  # nosec B101
    spec = response.json()
    assert '/analytics/stress-test' in spec['paths']  # nosec B101
    post = spec['paths']['/analytics/stress-test']['post']
    assert post['summary'] == 'Portfolio Stress Test'  # nosec B101
    response_ref = post['responses']['200']['content']['application/json']['schema']['$ref']
    assert response_ref.endswith('/StressTestResponse')  # nosec B101
    request_ref = post['requestBody']['content']['application/json']['schema']['$ref']
    assert request_ref.endswith('/StressTestRequest')  # nosec B101
