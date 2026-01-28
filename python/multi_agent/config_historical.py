"""Centralized factory for historical KPI provider (REAL vs MOCK mode).

This module provides a single point of configuration for choosing between
REAL (Supabase-backed) and MOCK (synthetic) historical KPI data.

Usage:
    from python.multi_agent.config_historical import build_historical_context_provider

    # Default: MOCK mode (no Supabase credentials required)
    provider = build_historical_context_provider()

    # Explicit REAL mode (requires SUPABASE_URL, SUPABASE_ANON_KEY env vars)
    provider = build_historical_context_provider(mode="REAL")

    # Environment-based selection
    export HISTORICAL_CONTEXT_MODE=REAL  # or MOCK (default)
    provider = build_historical_context_provider()
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from python.multi_agent.historical_context import HistoricalContextProvider

logger = logging.getLogger(__name__)


def build_historical_context_provider(
    cache_ttl_seconds: int = 60,
    mode: Optional[str] = None,
) -> HistoricalContextProvider:
    """
    Factory for HistoricalContextProvider with centralized REAL/MOCK selection.

    Args:
        cache_ttl_seconds: TTL for KPI query cache (default: 60 seconds).
        mode: Explicit mode override. Priority:
              1. `mode` argument if provided (MOCK or REAL)
              2. HISTORICAL_CONTEXT_MODE env var (default: MOCK)

    Returns:
        HistoricalContextProvider configured for MOCK or REAL mode.

    Raises:
        ValueError: If mode is invalid or REAL mode requested without Supabase env vars.

    Examples:
        >>> # MOCK mode (default)
        >>> provider = build_historical_context_provider()
        >>> provider.mode
        'MOCK'

        >>> # REAL mode (requires env vars)
        >>> import os
        >>> os.environ['SUPABASE_URL'] = 'https://...'
        >>> os.environ['SUPABASE_ANON_KEY'] = '...'
        >>> provider = build_historical_context_provider(mode="REAL")
        >>> provider.mode
        'REAL'
    """
    effective_mode = (mode or os.getenv("HISTORICAL_CONTEXT_MODE", "MOCK")).upper()

    if effective_mode not in ("MOCK", "REAL"):
        raise ValueError(
            f"Invalid mode: {effective_mode}. Must be 'MOCK' or 'REAL'."
        )

    if effective_mode == "REAL":
        # Validate Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "REAL mode requires SUPABASE_URL and SUPABASE_ANON_KEY env vars."
            )

        # Import here to avoid hard dependency on supabase client
        from python.multi_agent.historical_backend_supabase import (
            SupabaseHistoricalBackend,
        )

        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(
            cache_ttl_seconds=cache_ttl_seconds,
            mode="REAL",
            backend=backend,
        )
        logger.info("Built HistoricalContextProvider in REAL mode (Supabase)")
        return provider

    # Default: G4.1-compatible MOCK mode
    provider = HistoricalContextProvider(
        cache_ttl_seconds=cache_ttl_seconds,
        mode="MOCK",
    )
    logger.info("Built HistoricalContextProvider in MOCK mode (synthetic data)")
    return provider
