import asyncio
from datetime import datetime
from typing import Any
from backend.loans_analytics.apps.analytics.api.models import LoanRecord, RollRateAnalyticsResponse
from backend.loans_analytics.apps.analytics.api.service import KPIService

def _loan_record(**overrides: Any) -> LoanRecord:
    base_payload = {'id': 'L0', 'borrower_id': 'B0', 'loan_amount': 1000.0, 'principal_balance': 900.0, 'interest_rate': 0.2, 'loan_status': 'current', 'days_past_due': 0, 'previous_loan_status': 'current', 'previous_days_past_due': 0, 'previous_principal_balance': 900.0, 'origination_date': datetime(2026, 1, 1)}
    base_payload.update(overrides)
    return LoanRecord.model_validate(base_payload)

def _roll_rate_loans() -> list[LoanRecord]:
    return [_loan_record(id='L1', borrower_id='B1', loan_amount=1200.0, principal_balance=1000.0, interest_rate=0.2, loan_status='current', days_past_due=0, previous_loan_status='current', previous_days_past_due=0, previous_principal_balance=1000.0), _loan_record(id='L2', borrower_id='B2', loan_amount=2400.0, principal_balance=2000.0, interest_rate=0.24, loan_status='30-59 days past due', days_past_due=45, previous_loan_status='current', previous_days_past_due=0, previous_principal_balance=2100.0), _loan_record(id='L3', borrower_id='B3', loan_amount=2100.0, principal_balance=1700.0, interest_rate=0.21, loan_status='current', days_past_due=0, previous_loan_status='30-59 days past due', previous_days_past_due=45, previous_principal_balance=1800.0), _loan_record(id='L4', borrower_id='B4', loan_amount=6200.0, principal_balance=5000.0, interest_rate=0.26, loan_status='default', days_past_due=120, previous_loan_status='60-89 days past due', previous_days_past_due=75, previous_principal_balance=5200.0), _loan_record(id='L5', borrower_id='B5', loan_amount=4600.0, principal_balance=4300.0, interest_rate=0.22, loan_status='60-89 days past due', days_past_due=80, previous_loan_status='default', previous_days_past_due=110, previous_principal_balance=4400.0)]

def test_calculate_roll_rate_analytics_returns_transition_matrix_and_summary():
    service = KPIService(actor='test_user')
    response = asyncio.run(service.calculate_roll_rate_analytics(loans=_roll_rate_loans()))
    assert isinstance(response, RollRateAnalyticsResponse)  # nosec B101
    assert response.summary.total_loans == 5  # nosec B101
    assert response.summary.historical_coverage_pct == 100.0  # nosec B101
    assert response.summary.portfolio_cure_rate_pct == 33.33  # nosec B101
    assert response.summary.portfolio_roll_forward_rate_pct == 50.0  # nosec B101
    assert response.summary.worst_migration_path == '61_90->90_plus'  # nosec B101
    assert response.summary.best_cure_source == '31_60'  # nosec B101
    transitions = {(row.from_bucket, row.to_bucket): row for row in response.transition_matrix}
    assert ('31_60', 'current') in transitions  # nosec B101
    assert transitions['31_60', 'current'].loan_count == 1  # nosec B101
    assert transitions['31_60', 'current'].loan_share_pct == 100.0  # nosec B101
    buckets = {row.from_bucket: row for row in response.bucket_summaries}
    assert buckets['31_60'].cure_rate_pct == 100.0  # nosec B101
    assert buckets['61_90'].roll_forward_rate_pct == 100.0  # nosec B101
    assert buckets['90_plus'].stability_rate_pct == 0.0  # nosec B101
