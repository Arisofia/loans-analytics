from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def _payload() -> dict:
    return {'loans': [{'id': 'L1', 'borrower_id': 'B1', 'loan_amount': 1000.0, 'principal_balance': 900.0, 'interest_rate': 0.2, 'loan_status': 'current', 'days_past_due': 0, 'origination_date': '2026-01-15T00:00:00', 'total_scheduled': 200.0, 'last_payment_amount': 190.0}, {'id': 'L2', 'borrower_id': 'B2', 'loan_amount': 1500.0, 'principal_balance': 1200.0, 'interest_rate': 0.25, 'loan_status': '90+ days past due', 'days_past_due': 100, 'origination_date': '2026-01-20T00:00:00', 'total_scheduled': 300.0, 'last_payment_amount': 120.0}, {'id': 'L3', 'borrower_id': 'B3', 'loan_amount': 800.0, 'principal_balance': 700.0, 'interest_rate': 0.22, 'loan_status': 'default', 'days_past_due': 120, 'origination_date': '2026-02-10T00:00:00', 'total_scheduled': 250.0, 'last_payment_amount': 80.0}]}

def test_cohort_analytics_endpoint_returns_vintage_rows_and_summary():
    client = TestClient(app)
    response = client.post('/analytics/cohorts', json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert 'generated_at' in body
    assert 'cohorts' in body
    assert 'summary' in body
    assert len(body['cohorts']) == 2
    assert body['summary']['cohort_count'] == 2
    assert body['summary']['total_loans'] == 3
    cohort_months = [row['cohort_month'] for row in body['cohorts']]
    assert cohort_months == ['2026-01', '2026-02']
