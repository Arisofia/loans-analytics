import os
from datetime import datetime, timedelta, timezone
import pytest
from backend.python.multi_agent.config_historical import build_historical_context_provider
from backend.python.multi_agent.historical_context import HistoricalContextProvider

class TestConfigHistorical:

    @staticmethod
    def _assert_provider_mode(provider: HistoricalContextProvider, expected_mode: str) -> None:
        assert isinstance(provider, HistoricalContextProvider)
        assert provider.mode.upper() == expected_mode

    @staticmethod
    def _assert_history_sample_contract(sample: object) -> None:
        assert hasattr(sample, 'kpi_id')
        assert hasattr(sample, 'date')
        assert hasattr(sample, 'value')
        assert hasattr(sample, 'timestamp')
        assert isinstance(sample.kpi_id, str)
        assert isinstance(sample.value, (int, float))

    def test_default_mode_is_mock(self):
        os.environ.pop('HISTORICAL_CONTEXT_MODE', None)
        provider = build_historical_context_provider()
        self._assert_provider_mode(provider, 'MOCK')

    def test_explicit_mock_mode(self):
        provider = build_historical_context_provider(mode='MOCK')
        self._assert_provider_mode(provider, 'MOCK')

    def test_env_var_selects_mode(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('HISTORICAL_CONTEXT_MODE', 'MOCK')
        provider = build_historical_context_provider()
        self._assert_provider_mode(provider, 'MOCK')

    def test_explicit_mode_overrides_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('HISTORICAL_CONTEXT_MODE', 'MOCK')
        provider = build_historical_context_provider(mode='MOCK')
        self._assert_provider_mode(provider, 'MOCK')

    def test_cache_ttl_passed_through(self):
        provider = build_historical_context_provider(cache_ttl_seconds=120)
        assert provider.cache_ttl_seconds == 120

    def test_invalid_mode_raises_error(self):
        with pytest.raises(ValueError, match='Invalid mode'):
            build_historical_context_provider(mode='INVALID')

    def test_real_mode_without_credentials_raises_error(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv('SUPABASE_URL', raising=False)
        monkeypatch.delenv('SUPABASE_ANON_KEY', raising=False)
        with pytest.raises(ValueError, match='SUPABASE'):
            build_historical_context_provider(mode='REAL')

    def test_mock_data_contract_shape(self):
        provider = build_historical_context_provider(mode='MOCK')
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=30)
        history = provider._load_historical_data('npl_ratio', start_dt, end_dt)
        assert isinstance(history, list)
        assert history
        sample = history[0]
        self._assert_history_sample_contract(sample)
