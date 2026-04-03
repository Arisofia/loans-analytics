import asyncio
from backend.loans_analytics.apps.analytics.api.models import LoanRecord, SegmentAnalyticsResponse
from backend.loans_analytics.apps.analytics.api.service import KPIService

def _segment_loans() -> list[LoanRecord]:
    return [LoanRecord(id='L1', borrower_id='B1', loan_amount=800.0, principal_balance=700.0, interest_rate=0.2, loan_status='current', days_past_due=0, payment_frequency='monthly', company='CompanyA', credit_line='SME', kam_hunter='H1', kam_farmer='F1', utilization_pct=0.2, total_scheduled=200.0, last_payment_amount=190.0), LoanRecord(id='L2', borrower_id='B2', loan_amount=3000.0, principal_balance=2500.0, interest_rate=0.28, loan_status='60-89 days past due', days_past_due=75, payment_frequency='biweekly', company='CompanyA', credit_line='SME', kam_hunter='H2', kam_farmer='F2', utilization_pct=0.55, total_scheduled=400.0, last_payment_amount=240.0), LoanRecord(id='L3', borrower_id='B3', loan_amount=12000.0, principal_balance=10000.0, interest_rate=0.3, loan_status='default', days_past_due=120, payment_frequency='monthly', company='CompanyB', credit_line='Enterprise', kam_hunter='H2', kam_farmer='F2', utilization_pct=0.92, total_scheduled=800.0, last_payment_amount=300.0)]

def test_calculate_segment_analytics_risk_band():
    service = KPIService(actor='test_user')
    response = asyncio.run(service.calculate_segment_analytics(loans=_segment_loans(), dimension='risk_band', top_n=10))
    assert isinstance(response, SegmentAnalyticsResponse)  # nosec B101
    assert response.summary.dimension == 'risk_band'  # nosec B101
    assert response.summary.total_loans == 3  # nosec B101
    assert len(response.segments) >= 2  # nosec B101
    assert response.summary.largest_segment is not None  # nosec B101
    assert response.summary.riskiest_segment is not None  # nosec B101

def test_calculate_segment_analytics_ticket_size():
    service = KPIService(actor='test_user')
    response = asyncio.run(service.calculate_segment_analytics(loans=_segment_loans(), dimension='ticket_size_band', top_n=10))
    segments = {row.segment for row in response.segments}
    assert 'ticket_<1k' in segments  # nosec B101
    assert 'ticket_1k_5k' in segments  # nosec B101
    assert 'ticket_10k_plus' in segments  # nosec B101

def test_calculate_segment_analytics_company_dimension():
    service = KPIService(actor='test_user')
    response = asyncio.run(service.calculate_segment_analytics(loans=_segment_loans(), dimension='company', top_n=10))
    segments = {row.segment for row in response.segments}
    assert response.summary.dimension == 'company'  # nosec B101
    assert 'CompanyA' in segments  # nosec B101
    assert 'CompanyB' in segments  # nosec B101

def test_calculate_segment_analytics_utilization_band_dimension():
    service = KPIService(actor='test_user')
    response = asyncio.run(service.calculate_segment_analytics(loans=_segment_loans(), dimension='utilization_band', top_n=10))
    segments = {row.segment for row in response.segments}
    assert response.summary.dimension == 'utilization_band'  # nosec B101
    assert '0_25' in segments  # nosec B101
    assert '50_75' in segments  # nosec B101
    assert '75_100' in segments  # nosec B101
