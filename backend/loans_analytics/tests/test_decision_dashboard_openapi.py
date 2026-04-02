from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def test_openapi_contains_decision_dashboard_endpoint_and_schema_refs():
    client = TestClient(app)
    response = client.get('/openapi.json')
    assert response.status_code == 200
    spec = response.json()
    assert '/analytics/decision-dashboard' in spec['paths']
    post = spec['paths']['/analytics/decision-dashboard']['post']
    response_ref = post['responses']['200']['content']['application/json']['schema']['$ref']
    assert response_ref.endswith('/DecisionDashboardResponse')
    request_ref = post['requestBody']['content']['application/json']['schema']['$ref']
    assert request_ref.endswith('/LoanPortfolioRequest')
