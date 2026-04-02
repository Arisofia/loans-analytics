from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def test_openapi_contains_roll_rate_analytics_endpoint():
    client = TestClient(app)
    response = client.get('/openapi.json')
    assert response.status_code == 200
    spec = response.json()
    assert '/analytics/roll-rates' in spec['paths']
    post = spec['paths']['/analytics/roll-rates']['post']
    assert post['summary'] == 'Roll-Rate and Cure-Rate Analytics'
    request_ref = post['requestBody']['content']['application/json']['schema']['$ref']
    response_ref = post['responses']['200']['content']['application/json']['schema']['$ref']
    assert request_ref.endswith('/RollRateAnalyticsRequest')
    assert response_ref.endswith('/RollRateAnalyticsResponse')
