from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def test_openapi_contains_segment_analytics_endpoint():
    client = TestClient(app)
    response = client.get('/openapi.json')
    assert response.status_code == 200  # nosec B101
    spec = response.json()
    assert '/analytics/segments' in spec['paths']  # nosec B101
    post = spec['paths']['/analytics/segments']['post']
    assert post['summary'] == 'Segment Drill-down Analytics'  # nosec B101
    request_ref = post['requestBody']['content']['application/json']['schema']['$ref']
    response_ref = post['responses']['200']['content']['application/json']['schema']['$ref']
    assert request_ref.endswith('/SegmentAnalyticsRequest')  # nosec B101
    assert response_ref.endswith('/SegmentAnalyticsResponse')  # nosec B101
