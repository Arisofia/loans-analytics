import asyncio
from backend.python.apps.analytics.api.models import LoanRecord
from backend.python.apps.analytics.api.service import KPIService


def _sample_loans() -> list[LoanRecord]:
    """15-loan representative portfolio with diverse delinquency buckets."""
    return [
        LoanRecord(id='LN-001', loan_amount=32_000, appraised_value=48_000, borrower_income=72_000, monthly_debt=1_600, loan_status='current', interest_rate=0.2150, principal_balance=27_800),
        LoanRecord(id='LN-002', loan_amount=18_500, appraised_value=26_500, borrower_income=48_000, monthly_debt=1_100, loan_status='current', interest_rate=0.2450, principal_balance=15_200),
        LoanRecord(id='LN-003', loan_amount=9_800, appraised_value=14_200, borrower_income=31_200, monthly_debt=820, loan_status='current', interest_rate=0.3000, principal_balance=8_100),
        LoanRecord(id='LN-004', loan_amount=25_000, appraised_value=36_000, borrower_income=60_000, monthly_debt=1_350, loan_status='current', interest_rate=0.2600, principal_balance=20_400),
        LoanRecord(id='LN-005', loan_amount=41_000, appraised_value=62_000, borrower_income=96_000, monthly_debt=2_200, loan_status='current', interest_rate=0.2100, principal_balance=38_500),
        LoanRecord(id='LN-006', loan_amount=15_200, appraised_value=22_000, borrower_income=40_800, monthly_debt=950, loan_status='current', interest_rate=0.2800, principal_balance=11_600),
        LoanRecord(id='LN-007', loan_amount=8_500, appraised_value=12_500, borrower_income=26_400, monthly_debt=680, loan_status='current', interest_rate=0.3200, principal_balance=6_900),
        LoanRecord(id='LN-008', loan_amount=29_000, appraised_value=44_000, borrower_income=66_000, monthly_debt=1_500, loan_status='current', interest_rate=0.2350, principal_balance=24_700),
        LoanRecord(id='LN-009', loan_amount=12_000, appraised_value=17_500, borrower_income=36_000, monthly_debt=880, loan_status='current', interest_rate=0.2900, principal_balance=9_200),
        LoanRecord(id='LN-010', loan_amount=22_500, appraised_value=33_000, borrower_income=54_000, monthly_debt=1_250, loan_status='current', interest_rate=0.2500, principal_balance=18_300),
        LoanRecord(id='LN-011', loan_amount=14_000, appraised_value=20_000, borrower_income=36_000, monthly_debt=980, loan_status='30-59 days past due', interest_rate=0.2800, principal_balance=11_800),
        LoanRecord(id='LN-012', loan_amount=19_500, appraised_value=28_000, borrower_income=45_600, monthly_debt=1_100, loan_status='30-59 days past due', interest_rate=0.3100, principal_balance=16_200),
        LoanRecord(id='LN-013', loan_amount=11_000, appraised_value=16_000, borrower_income=30_000, monthly_debt=870, loan_status='60-89 days past due', interest_rate=0.3400, principal_balance=9_600),
        LoanRecord(id='LN-014', loan_amount=7_500, appraised_value=11_000, borrower_income=22_800, monthly_debt=620, loan_status='90+ days past due', interest_rate=0.3700, principal_balance=7_100),
        LoanRecord(id='LN-015', loan_amount=16_000, appraised_value=23_000, borrower_income=42_000, monthly_debt=1_050, loan_status='default', interest_rate=0.4000, principal_balance=15_400),
    ]


def _sample_payments() -> list[dict]:
    """12 payment records spread across 8 customers."""
    return [
        {'payment_date': '2025-10-03', 'customer_id': 'C-001', 'payment_amount': 2_800, 'interest_payment': 560, 'fee_payment': 120},
        {'payment_date': '2025-10-18', 'customer_id': 'C-002', 'payment_amount': 1_920, 'interest_payment': 384, 'fee_payment': 85},
        {'payment_date': '2025-11-05', 'customer_id': 'C-003', 'payment_amount': 1_050, 'interest_payment': 210, 'fee_payment': 45},
        {'payment_date': '2025-11-14', 'customer_id': 'C-004', 'payment_amount': 3_200, 'interest_payment': 640, 'fee_payment': 140},
        {'payment_date': '2025-12-01', 'customer_id': 'C-001', 'payment_amount': 2_800, 'interest_payment': 560, 'fee_payment': 120},
        {'payment_date': '2025-12-08', 'customer_id': 'C-005', 'payment_amount': 1_680, 'interest_payment': 336, 'fee_payment': 72},
        {'payment_date': '2025-12-20', 'customer_id': 'C-006', 'payment_amount': 2_200, 'interest_payment': 440, 'fee_payment': 95},
        {'payment_date': '2026-01-07', 'customer_id': 'C-002', 'payment_amount': 1_920, 'interest_payment': 384, 'fee_payment': 85},
        {'payment_date': '2026-01-15', 'customer_id': 'C-007', 'payment_amount': 870, 'interest_payment': 174, 'fee_payment': 37},
        {'payment_date': '2026-01-22', 'customer_id': 'C-003', 'payment_amount': 1_050, 'interest_payment': 210, 'fee_payment': 45},
        {'payment_date': '2026-02-04', 'customer_id': 'C-008', 'payment_amount': 4_100, 'interest_payment': 820, 'fee_payment': 175},
        {'payment_date': '2026-02-18', 'customer_id': 'C-004', 'payment_amount': 3_200, 'interest_payment': 640, 'fee_payment': 140},
    ]


def _sample_customers() -> list[dict]:
    """8 customers with realistic marketing spend for CAC calculation."""
    return [
        {'customer_id': 'C-001', 'created_at': '2025-09-01', 'marketing_spend': 680},
        {'customer_id': 'C-002', 'created_at': '2025-09-15', 'marketing_spend': 520},
        {'customer_id': 'C-003', 'created_at': '2025-10-03', 'marketing_spend': 390},
        {'customer_id': 'C-004', 'created_at': '2025-10-20', 'marketing_spend': 820},
        {'customer_id': 'C-005', 'created_at': '2025-11-08', 'marketing_spend': 445},
        {'customer_id': 'C-006', 'created_at': '2025-11-25', 'marketing_spend': 615},
        {'customer_id': 'C-007', 'created_at': '2025-12-10', 'marketing_spend': 280},
        {'customer_id': 'C-008', 'created_at': '2026-01-05', 'marketing_spend': 950},
    ]

def test_executive_analytics_includes_strategic_confirmations():
    service = KPIService(actor='test')
    payload = asyncio.run(service.get_executive_analytics(loans=_sample_loans(), payments=_sample_payments(), customers=_sample_customers()))
    confirmations = payload['strategic_confirmations']
    assert confirmations['cac_confirmed'] is True
    assert confirmations['ltv_confirmed'] is True
    assert confirmations['margin_confirmed'] is True
    assert confirmations['revenue_forecast_confirmed'] is True
    assert len(payload['revenue_forecast_6m']) == 6
    assert len(payload['opportunity_prioritization']) >= 1
    assert len(payload['churn_90d_metrics']) >= 1
    assert payload['data_governance'].get('quality_score') is not None
