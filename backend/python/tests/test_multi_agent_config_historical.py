import os
from datetime import datetime, timedelta, timezone
import pytest
from backend.python.multi_agent.config_historical import build_historical_context_provider
from backend.python.multi_agent.historical_context import HistoricalContextProvider

class TestConfigHistorical:

    def test_default_mode_is_mock(self):
        os.environ.pop('HISTORICAL_CONTEXT_MODE', None)
        provider = build_historical_context_provider()
        assert isinstance(provider, HistoricalContextProvider)
        assert provider.mode.upper() == 'MOCK'

    def test_explicit_mock_mode(self):
        provider = build_historical_context_provider(mode='MOCK')
        assert isinstance(provider, HistoricalContextProvider)
        assert provider.mode.upper() == 'MOCK'

    def test_env_var_selects_mode(self):
        original = os.environ.get('HISTORICAL_CONTEXT_MODE')
        try:
            os.environ['HISTORICAL_CONTEXT_MODE'] = 'MOCK'
            provider = build_historical_context_provider()
            assert provider.mode.upper() == 'MOCK'
        finally:
            if original:
                os.environ['HISTORICAL_CONTEXT_MODE'] = original
            else:
                os.environ.pop('HISTORICAL_CONTEXT_MODE', None)

    def test_explicit_mode_overrides_env_var(self):
        original = os.environ.get('HISTORICAL_CONTEXT_MODE')
        try:
            os.environ['HISTORICAL_CONTEXT_MODE'] = 'MOCK'
            provider = build_historical_context_provider(mode='MOCK')
            assert provider.mode.upper() == 'MOCK'
        finally:
            if original:
                os.environ['HISTORICAL_CONTEXT_MODE'] = original
            else:
                os.environ.pop('HISTORICAL_CONTEXT_MODE', None)

    def test_cache_ttl_passed_through(self):
        provider = build_historical_context_provider(cache_ttl_seconds=120)
        assert provider.cache_ttl_seconds == 120

    def test_invalid_mode_raises_error(self):
        with pytest.raises(ValueError, match='Invalid mode'):
            build_historical_context_provider(mode='INVALID')

    def test_real_mode_without_credentials_raises_error(self):
        original_url = os.environ.pop('SUPABASE_URL', None)
        original_key = os.environ.pop('SUPABASE_ANON_KEY', None)
        try:
            with pytest.raises(ValueError, match='SUPABASE'):
                build_historical_context_provider(mode='REAL')
        finally:
            if original_url:
                os.environ['SUPABASE_URL'] = original_url
            if original_key:
                os.environ['SUPABASE_ANON_KEY'] = original_key

    def test_mock_data_contract_shape(self):
        provider = build_historical_context_provider(mode='MOCK')
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=30)
        history = provider._load_historical_data('npl_ratio', start_dt, end_dt)
        assert isinstance(history, list)
        if history:
            sample = history[0]
            assert hasattr(sample, 'kpi_id')
            assert hasattr(sample, 'date')
            assert hasattr(sample, 'value')
            assert hasattr(sample, 'timestamp')
            assert isinstance(sample.kpi_id, str)
            assert isinstance(sample.value, (int, float))
