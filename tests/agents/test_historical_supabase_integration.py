import os
from datetime import date, datetime, timedelta, timezone
import pytest
from backend.python.multi_agent.historical_backend_supabase import SupabaseHistoricalBackend
from backend.python.multi_agent.historical_context import HistoricalContextProvider
REAL_SUPABASE_ENABLED = os.getenv('RUN_REAL_SUPABASE_TESTS', '0') == '1'

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
    def test_historical_context_provider_real_mode_roundtrip(self):
        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(cache_ttl_seconds=60, mode='REAL', backend=backend)
        kpi_id = 'npl_ratio'
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)
        history = provider._load_historical_data(kpi_id=kpi_id, start_date=start_dt, end_date=end_dt)
        assert isinstance(history, list)
        if history:
            first_record = history[0]
            assert isinstance(first_record, dict)
            assert first_record['kpi_id'] == kpi_id
            assert 'date' in first_record
            assert 'value' in first_record
            assert isinstance(first_record['date'], (date, datetime))
            assert isinstance(first_record['value'], (int, float, type(None)))

    @pytest.mark.skipif(not REAL_SUPABASE_ENABLED, reason='Real Supabase tests disabled (set RUN_REAL_SUPABASE_TESTS=1)')
    def test_mode_switching_mock_vs_real(self):
        backend = SupabaseHistoricalBackend()
        provider_mock = HistoricalContextProvider(cache_ttl_seconds=60, mode='MOCK', backend=None)
        provider_real = HistoricalContextProvider(cache_ttl_seconds=60, mode='REAL', backend=backend)
        kpi_id = 'npl_ratio'
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)
        history_mock = provider_mock._load_historical_data(kpi_id=kpi_id, start_date=start_dt, end_date=end_dt)
        history_real = provider_real._load_historical_data(kpi_id=kpi_id, start_date=start_dt, end_date=end_dt)
        assert isinstance(history_mock, list)
        assert isinstance(history_real, list)
        assert len(history_mock) > 0, 'MOCK mode should generate synthetic data'
        if history_real:
            assert set(history_mock[0].keys()) == set(history_real[0].keys())
