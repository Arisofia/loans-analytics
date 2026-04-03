from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app

def _payload() -> dict:
    return {'loans': [{'id': 'L1', 'borrower_id': 'B1', 'loan_amount': 1200.0, 'principal_balance': 1000.0, 'interest_rate': 0.2, 'loan_status': 'current', 'days_past_due': 0, 'previous_loan_status': 'current', 'previous_days_past_due': 0, 'previous_principal_balance': 1000.0}, {'id': 'L2', 'borrower_id': 'B2', 'loan_amount': 2400.0, 'principal_balance': 2000.0, 'interest_rate': 0.24, 'loan_status': '30-59 days past due', 'days_past_due': 45, 'previous_loan_status': 'current', 'previous_days_past_due': 0, 'previous_principal_balance': 2100.0}, {'id': 'L3', 'borrower_id': 'B3', 'loan_amount': 2100.0, 'principal_balance': 1700.0, 'interest_rate': 0.21, 'loan_status': 'current', 'days_past_due': 0, 'previous_loan_status': '30-59 days past due', 'previous_days_past_due': 45, 'previous_principal_balance': 1800.0}, {'id': 'L4', 'borrower_id': 'B4', 'loan_amount': 6200.0, 'principal_balance': 5000.0, 'interest_rate': 0.26, 'loan_status': 'default', 'days_past_due': 120, 'previous_loan_status': '60-89 days past due', 'previous_days_past_due': 75, 'previous_principal_balance': 5200.0}, {'id': 'L5', 'borrower_id': 'B5', 'loan_amount': 4600.0, 'principal_balance': 4300.0, 'interest_rate': 0.22, 'loan_status': '60-89 days past due', 'days_past_due': 80, 'previous_loan_status': 'default', 'previous_days_past_due': 110, 'previous_principal_balance': 4400.0}]}

def test_roll_rate_endpoint_returns_transition_rows_and_summary():
    client = TestClient(app)
    response = client.post('/analytics/roll-rates', json=_payload())
    assert response.status_code == 200  # nosec B101
    body = response.json()
    assert 'generated_at' in body  # nosec B101
    assert 'transition_matrix' in body  # nosec B101
    assert 'bucket_summaries' in body  # nosec B101
    assert 'summary' in body  # nosec B101
    summary = body['summary']
    assert summary['total_loans'] == 5  # nosec B101
    assert summary['historical_coverage_pct'] == 100.0  # nosec B101
    assert summary['portfolio_cure_rate_pct'] == 33.33  # nosec B101
    assert summary['portfolio_roll_forward_rate_pct'] == 50.0  # nosec B101
    assert summary['worst_migration_path'] == '61_90->90_plus'  # nosec B101
    assert summary['best_cure_source'] == '31_60'  # nosec B101
    transition_pairs = {(row['from_bucket'], row['to_bucket']) for row in body['transition_matrix']}
    assert ('31_60', 'current') in transition_pairs  # nosec B101
    assert ('61_90', '90_plus') in transition_pairs  # nosec B101
