import pytest
import pandas as pd
from datetime import datetime
from backend.loans_analytics.apps.analytics.api.models import LoanRecord
from backend.loans_analytics.apps.analytics.api.service import KPIService

@pytest.mark.asyncio
async def test_calculate_kpis_for_portfolio_includes_next_gen_kpis():
    service = KPIService(actor='test_user')
    loans = [LoanRecord(id='L1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.1, loan_status='current', days_past_due=0.0, total_scheduled=100.0, last_payment_amount=100.0), LoanRecord(id='L2', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.2, loan_status='90+ days past due', days_past_due=95.0, total_scheduled=100.0, last_payment_amount=0.0, recovery_value=200.0)]
    response = await service.calculate_kpis_for_portfolio(loans)
    kpi_map = {k.id: k for k in response}
    assert 'PAR60' in kpi_map
    assert 'NPL' in kpi_map
    assert 'LGD' in kpi_map
    assert 'COR' in kpi_map
    assert 'CURERATE' in kpi_map
    assert 'NIM' in kpi_map
    assert kpi_map['PAR60'].value == pytest.approx(50.0)
    assert kpi_map['NPL'].value == pytest.approx(50.0)
    assert kpi_map['LGD'].value == pytest.approx(80.0)
    assert kpi_map['COR'].value == pytest.approx(40.0)

@pytest.mark.asyncio
async def test_get_risk_stratification():
    service = KPIService(actor='test_user')
    loans = [LoanRecord(id='L1', borrower_id='B1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.1, loan_status='current', days_past_due=0.0, total_scheduled=100.0, last_payment_amount=100.0), LoanRecord(id='L2', borrower_id='B2', loan_amount=5000.0, principal_balance=5000.0, interest_rate=0.15, loan_status='30-59 days past due', days_past_due=45.0, total_scheduled=500.0, last_payment_amount=400.0)]
    response = await service.get_risk_stratification(loans)
    assert len(response.buckets) > 0
    assert len(response.decision_flags) == 4
    flags = {f.flag: f for f in response.decision_flags}
    assert 'Concentration' in flags
    assert 'Asset Quality' in flags
    assert 'Liquidity' in flags
    assert 'Recovery' in flags
    assert flags['Concentration'].status == 'red'
    assert flags['Asset Quality'].status == 'red'
    assert flags['Liquidity'].status == 'yellow'
    assert flags['Recovery'].status == 'red'
    assert response.summary

@pytest.mark.asyncio
async def test_get_vintage_curves():
    service = KPIService(actor='test_user')
    now = datetime.now()
    loans = [LoanRecord(id='OLD', origination_date=now - pd.DateOffset(months=6), loan_amount=1000.0, principal_balance=800.0, interest_rate=0.1, loan_status='current', days_past_due=0.0), LoanRecord(id='NEW', origination_date=now - pd.DateOffset(months=1), loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.1, loan_status='default', days_past_due=95.0)]
    response = await service.calculate_vintage_curves(loans)
    assert len(response.curves) == 2
    assert len(response.portfolio_average_curve) == 2
    avg_points = {p.months_on_book: p for p in response.portfolio_average_curve}
    assert 1 in avg_points
    assert 6 in avg_points
    assert avg_points[1].npl_ratio == pytest.approx(100.0)
    assert avg_points[6].npl_ratio == pytest.approx(0.0)
