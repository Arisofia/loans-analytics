from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def _payload() -> dict:
    return {'dimension': 'risk_band', 'top_n': 10, 'loans': [{'id': 'L1', 'borrower_id': 'B1', 'loan_amount': 800.0, 'principal_balance': 700.0, 'interest_rate': 0.2, 'loan_status': 'current', 'days_past_due': 0, 'payment_frequency': 'monthly', 'company': 'CompanyA', 'credit_line': 'SME', 'kam_hunter': 'H1', 'kam_farmer': 'F1', 'utilization_pct': 0.2, 'total_scheduled': 200.0, 'last_payment_amount': 190.0}, {'id': 'L2', 'borrower_id': 'B2', 'loan_amount': 3000.0, 'principal_balance': 2500.0, 'interest_rate': 0.28, 'loan_status': '60-89 days past due', 'days_past_due': 75, 'payment_frequency': 'biweekly', 'company': 'CompanyA', 'credit_line': 'SME', 'kam_hunter': 'H2', 'kam_farmer': 'F2', 'utilization_pct': 0.55, 'total_scheduled': 400.0, 'last_payment_amount': 240.0}, {'id': 'L3', 'borrower_id': 'B3', 'loan_amount': 12000.0, 'principal_balance': 10000.0, 'interest_rate': 0.3, 'loan_status': 'default', 'days_past_due': 120, 'payment_frequency': 'monthly', 'company': 'CompanyB', 'credit_line': 'Enterprise', 'kam_hunter': 'H2', 'kam_farmer': 'F2', 'utilization_pct': 0.92, 'total_scheduled': 800.0, 'last_payment_amount': 300.0}]}

def test_segment_analytics_endpoint_returns_segment_rows_and_summary():
    client = TestClient(app)
    response = client.post('/analytics/segments', json=_payload())
    assert response.status_code == 200  # nosec B101
    body = response.json()
    assert 'generated_at' in body  # nosec B101
    assert 'segments' in body  # nosec B101
    assert 'summary' in body  # nosec B101
    assert body['summary']['dimension'] == 'risk_band'  # nosec B101
    assert body['summary']['total_loans'] == 3  # nosec B101
    assert len(body['segments']) >= 2  # nosec B101

def test_segment_analytics_endpoint_supports_ticket_size_dimension():
    client = TestClient(app)
    payload = _payload()
    payload['dimension'] = 'ticket_size_band'
    response = client.post('/analytics/segments', json=payload)
    assert response.status_code == 200  # nosec B101
    body = response.json()
    assert body['summary']['dimension'] == 'ticket_size_band'  # nosec B101

def test_segment_analytics_endpoint_supports_company_dimension():
    client = TestClient(app)
    payload = _payload()
    payload['dimension'] = 'company'
    response = client.post('/analytics/segments', json=payload)
    assert response.status_code == 200  # nosec B101
    body = response.json()
    assert body['summary']['dimension'] == 'company'  # nosec B101
    segments = {row['segment'] for row in body['segments']}
    assert 'CompanyA' in segments  # nosec B101
    assert 'CompanyB' in segments  # nosec B101
