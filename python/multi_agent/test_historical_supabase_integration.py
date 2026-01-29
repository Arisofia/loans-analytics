"""Integration tests for Historical KPIs with Supabase backend (Phase G4.2.1)

These tests validate REAL mode against an actual Supabase instance.
They only run when Supabase credentials are configured and require the
integration_supabase marker.

Usage:
  pytest -m integration_supabase
  pytest -m integration_supabase -v

  To enable real network tests:
  RUN_REAL_SUPABASE_TESTS=1 pytest -m integration_supabase
"""

import os
from datetime import date, datetime, timedelta, timezone

import pytest

from python.multi_agent.historical_context import HistoricalContextProvider
from python.multi_agent.historical_backend_supabase import (
    SupabaseHistoricalBackend,
)

# Check if real Supabase tests are explicitly enabled
REAL_SUPABASE_ENABLED = os.getenv("RUN_REAL_SUPABASE_TESTS", "0") == "1"


def _supabase_configured() -> bool:
    """Check if Supabase credentials are available and valid.

    Validates that:
    1. Environment variables are set
    2. They are not placeholder/example values
    3. URL appears to be a real Supabase instance
    """
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    # Check if credentials exist and are not examples
    if not url or not key:
        return False

    # Reject placeholder/example values
    placeholder_urls = [
        "your-project",
        "https://your-project.supabase.co",
        "your-project.supabase.co",
    ]
    placeholder_keys = ["your-key", "your-anon-key"]

    if any(placeholder in url.lower() for placeholder in placeholder_urls):
        return False
    if any(placeholder in key.lower() for placeholder in placeholder_keys):
        return False

    # URL should have minimum structure of a real Supabase instance
    # Format: https://{project-ref}.supabase.co
    if not (url.startswith("https://") and ".supabase.co" in url):
        return False

    return True


@pytest.mark.integration_supabase
@pytest.mark.skipif(
    not _supabase_configured(),
    reason="Supabase credentials not configured (SUPABASE_URL, SUPABASE_ANON_KEY)",
)
class TestHistoricalKpisSupabaseIntegration:
    """Integration tests for Supabase-backed historical KPI provider."""

    def test_supabase_backend_connection(self):
        """Verify Supabase backend can connect and validate configuration."""
        # Instantiation will raise exception if credentials missing or connection fails
        backend = SupabaseHistoricalBackend()
        # If we reach here without exception, backend was created successfully
        assert isinstance(backend, SupabaseHistoricalBackend)

    def test_historical_context_provider_real_mode_init(self):
        """Verify HistoricalContextProvider initializes in REAL mode with backend."""
        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(
            cache_ttl_seconds=60,
            mode="REAL",
            backend=backend,
        )

        assert provider.mode.upper() == "REAL"
        assert provider._backend is not None
        assert isinstance(provider._backend, SupabaseHistoricalBackend)

    @pytest.mark.skipif(
        not REAL_SUPABASE_ENABLED,
        reason="Real Supabase tests disabled (set RUN_REAL_SUPABASE_TESTS=1)",
    )
    def test_historical_context_provider_real_mode_roundtrip(self):
        """Test loading historical data in REAL mode from Supabase.

        REQUIRES: RUN_REAL_SUPABASE_TESTS=1 and valid Supabase credentials

        This test:
        - Instantiates REAL mode with Supabase backend
        - Requests 30 days of history for a known KPI
        - Validates response structure matches expected contract
        - Does NOT require pre-populated data; gracefully handles empty results
        """
        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(
            cache_ttl_seconds=60,
            mode="REAL",
            backend=backend,
        )

        # Use a safe KPI ID that may or may not have data
        kpi_id = "npl_ratio"
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)

        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)

        history = provider._load_historical_data(
            kpi_id=kpi_id,
            start_date=start_dt,
            end_date=end_dt,
        )

        # Verify return type
        assert isinstance(history, list)

        # If data exists, validate structure
        if history:
            first_record = history[0]
            assert isinstance(first_record, dict)
            assert first_record["kpi_id"] == kpi_id
            assert "date" in first_record
            assert "value" in first_record

            # Validate field types
            assert isinstance(first_record["date"], (date, datetime))
            assert isinstance(first_record["value"], (int, float, type(None)))

    @pytest.mark.skipif(
        not REAL_SUPABASE_ENABLED,
        reason="Real Supabase tests disabled (set RUN_REAL_SUPABASE_TESTS=1)",
    )
    def test_mode_switching_mock_vs_real(self):
        """Verify MOCK and REAL modes return data of same structure.

        REQUIRES: RUN_REAL_SUPABASE_TESTS=1 and valid Supabase credentials

        This ensures backward compatibility: MOCK and REAL modes should
        return identically structured lists of dicts.
        """
        backend = SupabaseHistoricalBackend()

        # MOCK mode (default, no backend needed)
        provider_mock = HistoricalContextProvider(
            cache_ttl_seconds=60,
            mode="MOCK",
            backend=None,
        )

        # REAL mode (with backend)
        provider_real = HistoricalContextProvider(
            cache_ttl_seconds=60,
            mode="REAL",
            backend=backend,
        )

        kpi_id = "npl_ratio"
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)

        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)

        history_mock = provider_mock._load_historical_data(
            kpi_id=kpi_id,
            start_date=start_dt,
            end_date=end_dt,
        )

        history_real = provider_real._load_historical_data(
            kpi_id=kpi_id,
            start_date=start_dt,
            end_date=end_dt,
        )

        # Both should return lists
        assert isinstance(history_mock, list)
        assert isinstance(history_real, list)

        # MOCK should have data (synthetic); REAL may or may not
        assert len(history_mock) > 0, "MOCK mode should generate synthetic data"

        # If REAL has data, structure should match MOCK
        if history_real:
            assert set(history_mock[0].keys()) == set(history_real[0].keys())
