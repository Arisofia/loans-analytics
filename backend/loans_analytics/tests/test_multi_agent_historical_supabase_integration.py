import os
from datetime import datetime, timedelta, timezone
import pytest
import requests as _requests
from backend.loans_analytics.multi_agent.historical_backend_supabase import SupabaseHistoricalBackend
from backend.loans_analytics.multi_agent.historical_context import HistoricalContextProvider
REAL_SUPABASE_ENABLED = os.getenv('RUN_REAL_SUPABASE_TESTS', '0') == '1'
SERVICE_ROLE_ENABLED = bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip())

def _supabase_configured() -> bool:
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_ANON_KEY', '').strip()
    if not url or not key:
        return False
    placeholder_urls = ['your-project', 'https://your-project.supabase.co', 'your-project.supabase.co']
    placeholder_keys = ['your-key', 'your-anon-key']
    if any((placeholder in url.lower() for placeholder in placeholder_urls)):
        return False
    if any((placeholder in key.lower() for placeholder in placeholder_keys)):
        return False
    return url.startswith('https://') and '.supabase.co' in url

@pytest.mark.integration_supabase
@pytest.mark.skipif(not _supabase_configured(), reason='Supabase credentials not configured (SUPABASE_URL, SUPABASE_ANON_KEY)')
class TestHistoricalKpisSupabaseIntegration:

    def test_supabase_backend_connection(self):
        backend = SupabaseHistoricalBackend()
        assert isinstance(backend, SupabaseHistoricalBackend)

    def test_historical_context_provider_real_mode_init(self):
        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(cache_ttl_seconds=60, mode='REAL', backend=backend)
        assert provider.mode.upper() == 'REAL'
        assert provider._backend is not None
        assert isinstance(provider._backend, SupabaseHistoricalBackend)

    @pytest.mark.skipif(not REAL_SUPABASE_ENABLED, reason='Real Supabase tests disabled (set RUN_REAL_SUPABASE_TESTS=1)')
    @pytest.mark.skipif(not SERVICE_ROLE_ENABLED, reason='SUPABASE_SERVICE_ROLE_KEY required for data seeding')
    def test_historical_context_provider_real_mode_roundtrip(self):
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(cache_ttl_seconds=60, mode='REAL', backend=backend)
        kpi_id = 'npl_ratio'
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)
        svc_headers = {'apikey': service_key, 'Authorization': f'Bearer {service_key}', 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}
        seed_rows = [{'kpi_id': kpi_id, 'date': (start_date + timedelta(days=i)).isoformat(), 'value_numeric': 0.05 + i * 0.001} for i in range(30)]
        url = f'{backend.base_url}/rest/v1/{backend.table}'
        _requests.post(url, headers=svc_headers, json=seed_rows, timeout=10).raise_for_status()
        try:
            start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)
            history = provider._load_historical_data(kpi_id=kpi_id, start_date=start_dt, end_date=end_dt)
            assert isinstance(history, list)
            assert history
            first_record = history[0]
            assert hasattr(first_record, 'kpi_id')
            assert first_record.kpi_id == kpi_id
            assert hasattr(first_record, 'date')
            assert hasattr(first_record, 'value')
            assert isinstance(first_record.value, (int, float, type(None)))
        finally:
            _requests.delete(f'{url}?kpi_id=eq.{kpi_id}&date=gte.{start_date.isoformat()}&date=lte.{end_date.isoformat()}', headers=svc_headers, timeout=10)

    @pytest.mark.skipif(not REAL_SUPABASE_ENABLED, reason='Real Supabase tests disabled (set RUN_REAL_SUPABASE_TESTS=1)')
    @pytest.mark.skipif(not SERVICE_ROLE_ENABLED, reason='SUPABASE_SERVICE_ROLE_KEY required for data seeding')
    def test_mode_switching_mock_vs_real(self):
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        backend = SupabaseHistoricalBackend()
        provider_mock = HistoricalContextProvider(cache_ttl_seconds=60, mode='MOCK', backend=None)
        provider_real = HistoricalContextProvider(cache_ttl_seconds=60, mode='REAL', backend=backend)
        kpi_id = 'npl_ratio'
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)
        svc_headers = {'apikey': service_key, 'Authorization': f'Bearer {service_key}', 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}
        seed_rows = [{'kpi_id': kpi_id, 'date': (start_date + timedelta(days=i)).isoformat(), 'value_numeric': 0.05 + i * 0.001} for i in range(30)]
        url = f'{backend.base_url}/rest/v1/{backend.table}'
        _requests.post(url, headers=svc_headers, json=seed_rows, timeout=10).raise_for_status()
        try:
            start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)
            history_mock = provider_mock._load_historical_data(kpi_id=kpi_id, start_date=start_dt, end_date=end_dt)
            history_real = provider_real._load_historical_data(kpi_id=kpi_id, start_date=start_dt, end_date=end_dt)
            assert isinstance(history_mock, list)
            assert isinstance(history_real, list)
            assert len(history_mock) > 0, 'MOCK mode should generate synthetic data'
            assert history_real
            mock_attrs = {a for a in dir(history_mock[0]) if not a.startswith('_')}
            real_attrs = {a for a in dir(history_real[0]) if not a.startswith('_')}
            assert mock_attrs == real_attrs
        finally:
            _requests.delete(f'{url}?kpi_id=eq.{kpi_id}&date=gte.{start_date.isoformat()}&date=lte.{end_date.isoformat()}', headers=svc_headers, timeout=10)
