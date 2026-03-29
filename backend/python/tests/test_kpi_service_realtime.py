import asyncio
from datetime import datetime
from pathlib import Path
import pytest
from backend.python.apps.analytics.api.models import LoanRecord
import backend.python.apps.analytics.api.service as service_module

KPIService = service_module.KPIService

def test_calculate_kpis_for_portfolio_includes_collection_rate():
    service = KPIService(actor='test_user')
    loans = [LoanRecord(id='L1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.1, loan_status='current', total_scheduled=100.0, last_payment_amount=80.0), LoanRecord(id='L2', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.2, loan_status='90+ days past due', total_scheduled=150.0, last_payment_amount=75.0)]
    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}
    assert 'COLLECTION_RATE' in kpi_map
    assert kpi_map['COLLECTION_RATE'].value == pytest.approx(62.0)
    assert kpi_map['COLLECTION_RATE'].formula
    assert kpi_map['COLLECTION_RATE'].status == 'critical'
    assert kpi_map['COLLECTION_RATE'].threshold_status == 'critical'
    assert kpi_map['COLLECTION_RATE'].benchmark == pytest.approx(95.0)
    assert kpi_map['COLLECTION_RATE'].thresholds is not None
    assert kpi_map['COLLECTION_RATE'].thresholds.get('warning') == pytest.approx(85.0)

def test_calculate_kpis_for_portfolio_collection_rate_defaults_to_zero():
    service = KPIService(actor='test_user')
    loans = [LoanRecord(id='L1', loan_amount=1000.0, principal_balance=800.0, interest_rate=0.12, loan_status='current'), LoanRecord(id='L2', loan_amount=1200.0, principal_balance=900.0, interest_rate=0.15, loan_status='default')]
    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}
    assert 'COLLECTION_RATE' in kpi_map
    assert kpi_map['COLLECTION_RATE'].value == pytest.approx(0.0)

def test_calculate_kpis_for_portfolio_includes_expanded_realtime_kpis():
    service = KPIService(actor='test_user')
    month_start = datetime.now().replace(day=2, hour=0, minute=0, second=0, microsecond=0)
    loans = [LoanRecord(id='L1', borrower_id='B1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.1, loan_status='current', total_scheduled=100.0, last_payment_amount=80.0, current_balance=200.0, payment_frequency='bullet', term_months=6.0, origination_date=month_start, tpv=1000.0), LoanRecord(id='L2', borrower_id='B1', loan_amount=1500.0, principal_balance=500.0, interest_rate=0.2, loan_status='default', days_past_due=120.0, total_scheduled=200.0, last_payment_amount=50.0, recovery_value=100.0, current_balance=300.0, payment_frequency='manual', term_months=12.0, origination_date=month_start, tpv=500.0)]
    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}
    assert kpi_map['LOSS_RATE'].value == pytest.approx(20.0)
    assert kpi_map['RECOVERY_RATE'].value == pytest.approx(10.0)
    assert kpi_map['CASH_ON_HAND'].value == pytest.approx(500.0)
    assert kpi_map['CASH_ON_HAND'].threshold_status == 'not_configured'
    assert kpi_map['AVERAGE_LOAN_SIZE'].value == pytest.approx(1250.0)
    assert kpi_map['DISBURSEMENT_VOLUME_MTD'].value == pytest.approx(2500.0)
    assert kpi_map['NEW_LOANS_COUNT_MTD'].value == pytest.approx(2.0)
    assert kpi_map['CUSTOMER_LIFETIME_VALUE'].value == pytest.approx(1500.0)
    assert kpi_map['CAC'].value > 0.0
    assert 0.0 <= kpi_map['GROSS_MARGIN_PCT'].value <= 100.0
    assert kpi_map['REVENUE_FORECAST_6M'].value > 0.0
    assert kpi_map['CHURN_90D'].value == pytest.approx(0.0)
    assert kpi_map['DEFAULT_RATE'].value == pytest.approx(50.0)
    assert kpi_map['TOTAL_LOANS_COUNT'].value == pytest.approx(2.0)
    assert kpi_map['ACTIVE_BORROWERS'].value == pytest.approx(1.0)
    assert kpi_map['REPEAT_BORROWER_RATE'].value == pytest.approx(100.0)
    assert kpi_map['AUTOMATION_RATE'].value == pytest.approx(50.0)
    assert kpi_map['PROCESSING_TIME_AVG'].value == pytest.approx(9.0)
    assert kpi_map['PAR60'].value == pytest.approx(33.33)
    assert kpi_map['PAR60'].status == 'critical'
    assert kpi_map['PAR60'].threshold_status == 'critical'
    assert kpi_map['DPD_1_30'].value == pytest.approx(0.0)
    assert kpi_map['DPD_31_60'].value == pytest.approx(0.0)
    assert kpi_map['DPD_61_90'].value == pytest.approx(0.0)
    assert kpi_map['DPD_90_PLUS'].value == pytest.approx(33.33)
    assert kpi_map['NPL'].value == pytest.approx(33.33)
    # NPL_90 should be exposed and align with the severe-delinquency proxy (PAR90) in this scenario
    assert 'NPL_90' in kpi_map
    assert kpi_map['NPL_90'].value == pytest.approx(33.33)
    assert kpi_map['NPL_90'].value == pytest.approx(kpi_map['PAR90'].value)


def test_calculate_kpis_for_portfolio_aligns_npl_and_npl_90_to_strict_definition():
    service = KPIService(actor='test_user')
    loans = [
        LoanRecord(
            id='L1',
            borrower_id='B1',
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.15,
            loan_status='30-59 days past due',
            days_past_due=45.0,
        ),
        LoanRecord(
            id='L2',
            borrower_id='B2',
            loan_amount=1000.0,
            principal_balance=1000.0,
            interest_rate=0.20,
            loan_status='current',
            days_past_due=0.0,
        ),
    ]
    response = asyncio.run(service.calculate_kpis_for_portfolio(loans))
    kpi_map = {k.id: k for k in response}
    assert kpi_map['NPL'].value == pytest.approx(0.0)
    assert kpi_map['PAR90'].value == pytest.approx(0.0)

def test_supported_catalog_kpis_include_remaining_catalog_ids():
    service = KPIService(actor='test_user')
    supported = set(service.get_supported_catalog_kpi_ids())
    assert {'default_rate', 'total_loans_count', 'customer_lifetime_value'}.issubset(supported)

def test_catalog_metadata_parse_failure_is_fail_fast(monkeypatch, tmp_path):
    kpi_path = tmp_path / 'kpi_definitions.yaml'
    kpi_path.write_text('dummy: true\n', encoding='utf-8')
    monkeypatch.setattr(service_module, '_CATALOG_STATE', {'cache': {}, 'file_hash': ''})
    monkeypatch.setattr(service_module, 'KPI_DEFINITIONS_PATH', Path(kpi_path))

    def _raise_parse_error(_handle):
        raise RuntimeError('synthetic parser failure')
    monkeypatch.setattr(service_module.yaml, 'safe_load', _raise_parse_error)
    with pytest.raises(ValueError, match='CRITICAL: Failed to load KPI catalog metadata'):
        service_module._load_catalog_kpi_metadata()
