from __future__ import annotations
import logging
import os
from typing import Optional, Type
from backend.python.multi_agent.historical_context import HistoricalContextProvider
try:
    from backend.python.multi_agent.historical_backend_supabase import SupabaseHistoricalBackend
    SUPABASE_BACKEND_CLS: Optional[Type[SupabaseHistoricalBackend]] = SupabaseHistoricalBackend
except ImportError:
    SUPABASE_BACKEND_CLS = None
logger = logging.getLogger(__name__)

def build_historical_context_provider(cache_ttl_seconds: int=60, mode: Optional[str]=None) -> HistoricalContextProvider:
    effective_mode = str(mode or os.getenv('HISTORICAL_CONTEXT_MODE', 'MOCK')).upper()
    if effective_mode not in ('MOCK', 'REAL'):
        raise ValueError(f"Invalid mode: {effective_mode}. Must be 'MOCK' or 'REAL'.")
    if effective_mode == 'REAL':
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        if not supabase_url or not supabase_key:
            raise ValueError('REAL mode requires SUPABASE_URL and SUPABASE_ANON_KEY env vars.')
        if SUPABASE_BACKEND_CLS is None:
            raise ValueError('REAL mode requires supabase client library to be installed.')
        backend = SUPABASE_BACKEND_CLS()
        provider = HistoricalContextProvider(cache_ttl_seconds=cache_ttl_seconds, mode='REAL', backend=backend)
        logger.info('Built HistoricalContextProvider in REAL mode (Supabase)')
        return provider
    provider = HistoricalContextProvider(cache_ttl_seconds=cache_ttl_seconds, mode='MOCK')
    logger.info('Built HistoricalContextProvider in MOCK mode (synthetic data)')
    return provider
