import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.loans_analytics.apps.analytics.api.main import app
from backend.loans_analytics.apps.analytics.api.models import LoanRecord
from backend.loans_analytics.apps.analytics.api.service import KPIService

def _make_loan(loan_id: str, principal_balance: float, loan_amount: float, interest_rate: float, loan_status: str, days_past_due: float=0.0, last_payment_amount: float=0.0, total_scheduled: float=0.0, recovery_value: float | None=None) -> dict:
    payload = {'id': loan_id, 'loan_amount': loan_amount, 'principal_balance': principal_balance, 'interest_rate': interest_rate, 'loan_status': loan_status, 'days_past_due': days_past_due, 'last_payment_amount': last_payment_amount, 'total_scheduled': total_scheduled}
    if recovery_value is not None:
        payload['recovery_value'] = recovery_value
    return payload

def _mixed_portfolio() -> list[dict]:
    return [_make_loan('L1', 1000.0, 1000.0, 0.15, 'current', 0.0, 100.0, 100.0), _make_loan('L2', 500.0, 500.0, 0.2, '30-59 days past due', 45.0, 20.0, 50.0), _make_loan('L3', 800.0, 800.0, 0.25, 'default', 95.0, 0.0, 80.0, 200.0), _make_loan('L4', 300.0, 300.0, 0.18, '60-89 days past due', 75.0, 10.0, 30.0)]

class TestUnitEconomicsEndpoint:

    def test_returns_200_with_valid_payload(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        response = client.post('/analytics/unit-economics', json=payload)
        assert response.status_code == 200  # nosec B101

    def test_response_has_all_top_level_keys(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        expected_keys = {'generated_at', 'npl', 'lgd', 'cost_of_risk', 'nim', 'payback', 'cure_rate', 'dpd_migration'}
        assert expected_keys.issubset(body.keys())  # nosec B101

    def test_npl_structure(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        npl = body['npl']
        assert 'npl_ratio' in npl  # nosec B101
        assert 'npl_balance' in npl  # nosec B101
        assert 'total_balance' in npl  # nosec B101
        assert 'npl_loan_count' in npl  # nosec B101
        assert 'formula' in npl  # nosec B101
        assert npl['npl_ratio'] > 0  # nosec B101

    def test_lgd_structure(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        lgd = body['lgd']
        assert 'lgd_pct' in lgd  # nosec B101
        assert 'recovery_rate_pct' in lgd  # nosec B101
        assert 'defaulted_balance' in lgd  # nosec B101
        assert 'recovered_amount' in lgd  # nosec B101
        assert 0.0 <= lgd['lgd_pct'] <= 100.0  # nosec B101

    def test_cost_of_risk_structure(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        cor = body['cost_of_risk']
        assert 'cost_of_risk_pct' in cor  # nosec B101
        assert 'npl_ratio' in cor  # nosec B101
        assert 'lgd_pct' in cor  # nosec B101
        assert 'expected_loss_balance' in cor  # nosec B101

    def test_nim_structure_and_values(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio(), 'funding_cost_rate': 0.06}
        body = client.post('/analytics/unit-economics', json=payload).json()
        nim = body['nim']
        assert 'nim_pct' in nim  # nosec B101
        assert 'gross_yield_pct' in nim  # nosec B101
        assert 'funding_cost_pct' in nim  # nosec B101
        assert nim['funding_cost_pct'] == pytest.approx(6.0, abs=0.01)  # nosec B101

    def test_payback_period_with_cac_and_arpu(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio(), 'cac': 100.0, 'monthly_arpu': 25.0}
        body = client.post('/analytics/unit-economics', json=payload).json()
        payback = body['payback']
        assert 'payback_months' in payback  # nosec B101
        assert payback['payback_months'] == pytest.approx(4.0, abs=0.01)  # nosec B101
        assert payback['cac'] == pytest.approx(100.0)  # nosec B101
        assert payback['monthly_arpu'] == pytest.approx(25.0)  # nosec B101

    def test_payback_period_zero_arpu(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio(), 'cac': 100.0, 'monthly_arpu': 0.0}
        body = client.post('/analytics/unit-economics', json=payload).json()
        assert body['payback']['payback_months'] is None  # nosec B101

    def test_cure_rate_structure(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        cure = body['cure_rate']
        assert {'cure_rate_pct', 'delinquent_count', 'curing_count', 'note'}.issubset(cure.keys())  # nosec B101
        assert 0.0 <= cure['cure_rate_pct'] <= 100.0  # nosec B101

    def test_dpd_migration_structure(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        migration = body['dpd_migration']
        assert isinstance(migration, list)  # nosec B101
        assert len(migration) > 0  # nosec B101
        required = {'bucket', 'loan_count', 'balance', 'balance_share_pct', 'risk_level', 'recommended_action'}
        assert all((required.issubset(set(bucket.keys())) for bucket in migration))  # nosec B101
        assert all((bucket['risk_level'] in {'low', 'medium', 'high', 'critical'} for bucket in migration))  # nosec B101

    def test_dpd_migration_recommended_actions_present(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        assert all((bucket['recommended_action'].strip() != '' for bucket in body['dpd_migration']))  # nosec B101

    def test_dpd_migration_bucket_names_normalized(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        bucket_names = {b['bucket'] for b in body['dpd_migration']}
        assert not any((name.startswith('dpd_') for name in bucket_names)), f'Found un-normalized bucket names: {bucket_names}'  # nosec B101
        expected = {'current', '1_30', '31_60', '61_90', '90_plus'}
        assert bucket_names.issubset(expected), f'Unexpected bucket names: {bucket_names - expected}'  # nosec B101

    def test_single_current_loan(self):
        client = TestClient(app)
        payload = {'loans': [_make_loan('L1', 1000.0, 1000.0, 0.15, 'current', 0.0, 100.0, 100.0)]}
        body = client.post('/analytics/unit-economics', json=payload).json()
        assert body['npl']['npl_ratio'] == 0.0  # nosec B101
        assert body['lgd']['lgd_pct'] == 0.0  # nosec B101
        assert body['cost_of_risk']['cost_of_risk_pct'] == 0.0  # nosec B101

    def test_generated_at_is_datetime(self):
        client = TestClient(app)
        payload = {'loans': _mixed_portfolio()}
        body = client.post('/analytics/unit-economics', json=payload).json()
        raw_ts = body['generated_at'].replace('Z', '+00:00')
        dt = datetime.fromisoformat(raw_ts)
        assert isinstance(dt, datetime)  # nosec B101

class TestKPIServiceUnitEconomics:

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_basic(self):
        service = KPIService(actor='test')
        loans = [LoanRecord(id='L1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.15, loan_status='current', days_past_due=0.0, total_scheduled=100.0, last_payment_amount=100.0), LoanRecord(id='L2', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.2, loan_status='default', days_past_due=95.0, total_scheduled=100.0, last_payment_amount=0.0, recovery_value=200.0)]
        result = await service.calculate_unit_economics(loans)
        assert result.npl.npl_ratio == pytest.approx(50.0, abs=0.01)  # nosec B101
        assert result.lgd.lgd_pct == pytest.approx(80.0, abs=0.01)  # nosec B101
        assert result.lgd.recovery_rate_pct == pytest.approx(20.0, abs=0.01)  # nosec B101
        assert result.cost_of_risk.cost_of_risk_pct == pytest.approx(40.0, abs=0.01)  # nosec B101

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_dpd_migration_action_flags(self):
        service = KPIService(actor='test')
        loans = [LoanRecord(id='L1', loan_amount=500.0, principal_balance=500.0, interest_rate=0.1, loan_status='current', days_past_due=0.0), LoanRecord(id='L2', loan_amount=500.0, principal_balance=500.0, interest_rate=0.2, loan_status='30-59 days past due', days_past_due=45.0)]
        result = await service.calculate_unit_economics(loans)
        assert len(result.dpd_migration) >= 2  # nosec B101
        assert all((bucket.recommended_action.strip() != '' for bucket in result.dpd_migration))  # nosec B101
        assert all((bucket.risk_level in {'low', 'medium', 'high', 'critical'} for bucket in result.dpd_migration))  # nosec B101

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_empty_loans(self):
        service = KPIService(actor='test')
        result = await service.calculate_unit_economics([])
        assert result.npl.npl_ratio == 0.0  # nosec B101
        assert result.lgd.lgd_pct == 0.0  # nosec B101
        assert result.cost_of_risk.cost_of_risk_pct == 0.0  # nosec B101
        assert result.nim.nim_pct == 0.0  # nosec B101
        assert result.cure_rate.cure_rate_pct == 0.0  # nosec B101
        assert result.payback.payback_months is None  # nosec B101

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_nim_with_custom_funding_cost(self):
        service = KPIService(actor='test')
        loans = [LoanRecord(id='L1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.3, loan_status='current', days_past_due=0.0)]
        result = await service.calculate_unit_economics(loans, funding_cost_rate=0.05)
        assert result.nim.funding_cost_pct == pytest.approx(5.0, abs=0.01)  # nosec B101
        assert result.nim.gross_yield_pct > 0.0  # nosec B101
        assert result.nim.nim_pct > 0.0  # nosec B101

    @pytest.mark.asyncio
    async def test_calculate_unit_economics_payback_period(self):
        service = KPIService(actor='test')
        loans = [LoanRecord(id='L1', loan_amount=1000.0, principal_balance=1000.0, interest_rate=0.1, loan_status='current', days_past_due=0.0)]
        result = await service.calculate_unit_economics(loans, cac=240.0, monthly_arpu=20.0)
        assert result.payback.payback_months == pytest.approx(12.0, abs=0.01)  # nosec B101
