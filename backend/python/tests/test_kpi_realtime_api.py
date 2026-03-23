from datetime import datetime
from fastapi.testclient import TestClient
from backend.python.apps.analytics.api.main import app

def test_calculate_all_kpis_includes_collection_rate_for_realtime_input():
    client = TestClient(app)
    payload = {'loans': [{'id': 'L1', 'loan_amount': 1000.0, 'principal_balance': 1000.0, 'interest_rate': 0.1, 'loan_status': 'current', 'total_scheduled': 100.0, 'last_payment_amount': 80.0}, {'id': 'L2', 'loan_amount': 1000.0, 'principal_balance': 1000.0, 'interest_rate': 0.2, 'loan_status': '90+ days past due', 'total_scheduled': 150.0, 'last_payment_amount': 75.0}]}
    response = client.post('/analytics/kpis', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['CollectionRate'] is not None
    assert body['CollectionRate']['id'] == 'COLLECTION_RATE'
    assert body['CollectionRate']['value'] == 62.0
    assert body['CollectionRate']['status'] == 'critical'
    assert body['CollectionRate']['benchmark'] == 95.0
    assert body['CollectionRate']['thresholds']['warning'] == 85.0

def test_calculate_all_kpis_includes_expanded_metrics():
    client = TestClient(app)
    month_start = datetime.now().replace(day=2, hour=0, minute=0, second=0, microsecond=0)
    payload = {'loans': [{'id': 'L1', 'borrower_id': 'B1', 'loan_amount': 1000.0, 'principal_balance': 1000.0, 'interest_rate': 0.1, 'loan_status': 'current', 'total_scheduled': 100.0, 'last_payment_amount': 80.0, 'current_balance': 200.0, 'payment_frequency': 'bullet', 'term_months': 6.0, 'origination_date': month_start.isoformat(), 'tpv': 1000.0}, {'id': 'L2', 'borrower_id': 'B1', 'loan_amount': 1500.0, 'principal_balance': 500.0, 'interest_rate': 0.2, 'loan_status': 'default', 'days_past_due': 120.0, 'total_scheduled': 200.0, 'last_payment_amount': 50.0, 'recovery_value': 100.0, 'current_balance': 300.0, 'payment_frequency': 'manual', 'term_months': 12.0, 'origination_date': month_start.isoformat(), 'tpv': 500.0}]}
    response = client.post('/analytics/kpis', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['LossRate']['id'] == 'LOSS_RATE'
    assert body['LossRate']['value'] == 20.0
    assert body['RecoveryRate']['value'] == 10.0
    assert body['CashOnHand']['value'] == 500.0
    assert body['AverageLoanSize']['value'] == 1250.0
    assert body['DisbursementVolumeMTD']['value'] == 2500.0
    assert body['NewLoansCountMTD']['value'] == 2.0
    assert body['CustomerLifetimeValue']['value'] == 1500.0
    assert body['CAC']['id'] == 'CAC'
    assert body['CAC']['value'] > 0.0
    assert body['GrossMarginPct']['id'] == 'GROSS_MARGIN_PCT'
    assert 0.0 <= body['GrossMarginPct']['value'] <= 100.0
    assert body['RevenueForecast6M']['id'] == 'REVENUE_FORECAST_6M'
    assert body['RevenueForecast6M']['value'] > 0.0
    assert body['Churn90D']['id'] == 'CHURN_90D'
    assert body['Churn90D']['value'] == 0.0
    assert body['DefaultRate']['value'] == 50.0
    assert body['TotalLoansCount']['value'] == 2.0
    assert body['ActiveBorrowers']['value'] == 1.0
    assert body['RepeatBorrowerRate']['value'] == 100.0
    assert body['AutomationRate']['value'] == 50.0
    assert body['ProcessingTimeAvg']['value'] == 9.0
    assert body['PAR60']['value'] == 33.33
    assert body['PAR60']['status'] == 'critical'
    assert body['DPD1_30']['value'] == 0.0
    assert body['DPD31_60']['value'] == 0.0
    assert body['DPD61_90']['value'] == 0.0
    assert body['DPD90Plus']['value'] == 33.33

def test_get_single_kpi_supports_new_path_aliases():
    client = TestClient(app)
    month_start = datetime.now().replace(day=2, hour=0, minute=0, second=0, microsecond=0)
    payload = {'loans': [{'id': 'L1', 'borrower_id': 'B1', 'loan_amount': 1000.0, 'principal_balance': 1000.0, 'interest_rate': 0.1, 'loan_status': 'current', 'origination_date': month_start.isoformat(), 'tpv': 1000.0}, {'id': 'L2', 'borrower_id': 'B1', 'loan_amount': 1500.0, 'principal_balance': 500.0, 'interest_rate': 0.2, 'loan_status': 'default', 'origination_date': month_start.isoformat(), 'tpv': 500.0}]}
    clv = client.post('/analytics/kpis/customer-lifetime-value', json=payload)
    assert clv.status_code == 200
    assert clv.json()['id'] == 'CUSTOMER_LIFETIME_VALUE'
    assert clv.json()['value'] == 1500.0
    default_rate = client.post('/analytics/kpis/default-rate', json=payload)
    assert default_rate.status_code == 200
    assert default_rate.json()['id'] == 'DEFAULT_RATE'
    assert default_rate.json()['status'] == 'critical'
    assert default_rate.json()['thresholds']['critical'] == 5.0
    total_loans = client.post('/analytics/kpis/total-loans-count', json=payload)
    assert total_loans.status_code == 200
    assert total_loans.json()['id'] == 'TOTAL_LOANS_COUNT'
    cac = client.post('/analytics/kpis/cac', json=payload)
    assert cac.status_code == 200
    assert cac.json()['id'] == 'CAC'
    margin = client.post('/analytics/kpis/gross-margin-pct', json=payload)
    assert margin.status_code == 200
    assert margin.json()['id'] == 'GROSS_MARGIN_PCT'
    forecast = client.post('/analytics/kpis/revenue-forecast-6m', json=payload)
    assert forecast.status_code == 200
    assert forecast.json()['id'] == 'REVENUE_FORECAST_6M'
    churn = client.post('/analytics/kpis/churn-90d', json=payload)
    assert churn.status_code == 200
    assert churn.json()['id'] == 'CHURN_90D'
    ltv = client.post('/analytics/kpis/ltv', json=payload)
    assert ltv.status_code == 200
    assert ltv.json()['id'] == 'AVG_LTV'
    avg_ltv = client.post('/analytics/kpis/avg-ltv', json=payload)
    assert avg_ltv.status_code == 200
    assert avg_ltv.json()['id'] == 'AVG_LTV'
    dti = client.post('/analytics/kpis/dti', json=payload)
    assert dti.status_code == 200
    assert dti.json()['id'] == 'AVG_DTI'
    avg_dti = client.post('/analytics/kpis/avg-dti', json=payload)
    assert avg_dti.status_code == 200
    assert avg_dti.json()['id'] == 'AVG_DTI'
    dpd_90_plus = client.post('/analytics/kpis/dpd-90-plus', json=payload)
    assert dpd_90_plus.status_code == 200
    assert dpd_90_plus.json()['id'] == 'DPD_90_PLUS'
