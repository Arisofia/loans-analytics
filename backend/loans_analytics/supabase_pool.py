from __future__ import annotations
import asyncio
import logging
import re
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncGenerator, Optional
from urllib.parse import urlparse
try:
    import asyncpg
except ImportError:
    asyncpg = None
if TYPE_CHECKING:
    import asyncpg as asyncpg_types
from backend.loans_analytics.config import settings
logger = logging.getLogger(__name__)

class SupabaseConnectionPool:

    def __init__(self, database_url: str, *, min_size: Optional[int]=None, max_size: Optional[int]=None, command_timeout: Optional[int]=None, max_idle_time: Optional[int]=None, max_lifetime: Optional[int]=None):
        if asyncpg is None:
            raise ImportError('asyncpg is required for connection pooling. Install with: pip install asyncpg')
        self._normalized_url = self._normalize_database_url(database_url)
        self.pool_config = settings.supabase_pool
        self.min_size = min_size or self.pool_config.min_size
        self.max_size = max_size or self.pool_config.max_size
        self.command_timeout = command_timeout or self.pool_config.command_timeout
        self.max_idle_time = max_idle_time or self.pool_config.max_idle_time
        self.max_lifetime = max_lifetime or self.pool_config.max_lifetime
        self._pool: Optional['asyncpg_types.Pool'] = None
        self._metrics = {'total_connections': 0, 'active_connections': 0, 'failed_connections': 0, 'queries_executed': 0, 'queries_failed': 0}

    def _normalize_database_url(self, url: str) -> str:
        if url.startswith('postgres://') and (not url.startswith('postgresql://')):
            url = url.replace('postgres://', 'postgresql://', 1)
        pooler_pattern = 'postgresql://postgres\\.([^:]+):([^@]+)@(.+)'  # gitleaks:allow
        match = re.match(pooler_pattern, url)
        if match:
            project_ref = match.group(1)
            logger.info('Detected Supabase pooler URL (project: %s)', project_ref)
        return url

    def _is_supabase_pooler(self) -> bool:
        parsed = urlparse(self._normalized_url)
        host = (parsed.hostname or '').lower()
        port = parsed.port
        return host.endswith('.pooler.supabase.com') or port == 6543

    def __repr__(self) -> str:
        return f'<SupabaseConnectionPool(id={id(self):#x}, size={self.max_size})>'

    def __str__(self) -> str:
        return f'SupabaseConnectionPool(max_connections={self.max_size})'

    async def initialize(self) -> None:
        if not self.pool_config.enabled:
            logger.warning('Connection pooling is disabled in configuration')
            return
        try:
            logger.info('Initializing Supabase connection pool (min=%d, max=%d, timeout=%ds)', self.min_size, self.max_size, self.command_timeout)
            pool_kwargs: dict[str, Any] = {'min_size': self.min_size, 'max_size': self.max_size, 'command_timeout': self.command_timeout, 'max_inactive_connection_lifetime': self.max_idle_time}
            if self._is_supabase_pooler():
                pool_kwargs['statement_cache_size'] = 0
                logger.info('Supabase pooler detected: asyncpg statement cache disabled')
            self._pool = await asyncpg.create_pool(self._normalized_url, **pool_kwargs)
            async with self._pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            self._metrics['total_connections'] = self._pool.get_size()
            logger.info('✅ Connection pool initialized with %d connections', self._pool.get_size())
        except Exception as e:
            self._metrics['failed_connections'] += 1
            logger.error('❌ Failed to initialize connection pool: %s', e, exc_info=True)
            raise

    async def close(self) -> None:
        if self._pool:
            logger.info('Closing connection pool...')
            await self._pool.close()
            logger.info('✅ Connection pool closed')
            self._pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator['asyncpg_types.Connection', None]:
        if not self._pool:
            raise RuntimeError('Connection pool not initialized. Call initialize() first.')
        max_retries = self.pool_config.max_retries
        retry_delay = self.pool_config.retry_delay
        connection: Optional['asyncpg_types.Connection'] = None
        for attempt in range(max_retries):
            try:
                connection = await self._pool.acquire()
                break
            except asyncpg.PostgresError as e:
                self._metrics['failed_connections'] += 1
                if attempt < max_retries - 1:
                    wait_time = retry_delay * 2 ** attempt
                    logger.warning('Connection attempt %d/%d failed: %s. Retrying in %ds...', attempt + 1, max_retries, e, wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error('All %d connection attempts failed', max_retries, exc_info=True)
                    raise
        if connection is None:
            raise RuntimeError('Failed to acquire database connection')
        self._metrics['active_connections'] += 1
        try:
            yield connection
        finally:
            self._metrics['active_connections'] -= 1
            try:
                await self._pool.release(connection)
            except Exception as release_err:
                logger.warning('Failed to release connection back to pool: %s', release_err)

    async def execute(self, query: str, *args: Any) -> str:
        try:
            async with self.acquire() as conn:
                await asyncio.wait_for(conn.execute(query, *args), timeout=self.command_timeout)
                self._metrics['queries_executed'] += 1
                return 'success'
        except asyncio.TimeoutError:
            self._metrics['queries_failed'] += 1
            logger.error('Query execution timed out after %ss', self.command_timeout)
            raise
        except Exception as e:
            self._metrics['queries_failed'] += 1
            logger.error('Query execution failed: %s', e, exc_info=True)
            raise

    async def fetch(self, query: str, *args: Any) -> list['asyncpg_types.Record']:
        try:
            async with self.acquire() as conn:
                result = await asyncio.wait_for(conn.fetch(query, *args), timeout=self.command_timeout)
                self._metrics['queries_executed'] += 1
                return result
        except asyncio.TimeoutError:
            self._metrics['queries_failed'] += 1
            logger.error('Query fetch timed out after %ss', self.command_timeout)
            raise
        except Exception as e:
            self._metrics['queries_failed'] += 1
            logger.error('Query fetch failed: %s', e, exc_info=True)
            raise

    async def fetchrow(self, query: str, *args: Any) -> Optional['asyncpg_types.Record']:
        try:
            async with self.acquire() as conn:
                result = await asyncio.wait_for(conn.fetchrow(query, *args), timeout=self.command_timeout)
                self._metrics['queries_executed'] += 1
                return result
        except asyncio.TimeoutError:
            self._metrics['queries_failed'] += 1
            logger.error('Query fetchrow timed out after %ss', self.command_timeout)
            raise
        except Exception as e:
            self._metrics['queries_failed'] += 1
            logger.error('Query fetchrow failed: %s', e, exc_info=True)
            raise

    async def health_check(self) -> dict[str, Any]:
        if not self._pool:
            return {'status': 'not_initialized', 'healthy': False, 'metrics': self._metrics}
        try:
            async with self.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return {'status': 'healthy', 'healthy': True, 'pool_size': self._pool.get_size(), 'free_connections': self._pool.get_idle_size(), 'metrics': self._metrics}
        except Exception as e:
            return {'status': 'unhealthy', 'healthy': False, 'error': str(e), 'metrics': self._metrics}

    def get_metrics(self) -> dict[str, int]:
        return {**self._metrics, 'pool_size': self._pool.get_size() if self._pool else 0, 'free_connections': self._pool.get_idle_size() if self._pool else 0}
    _global_pool: Optional[SupabaseConnectionPool] = None

async def get_pool(database_url: Optional[str]=None) -> SupabaseConnectionPool:
    if SupabaseConnectionPool._global_pool is None:
        db_url = database_url if database_url is not None else settings.database_url
        if not db_url:
            raise ValueError('database_url required for pool initialization')
        SupabaseConnectionPool._global_pool = SupabaseConnectionPool(db_url)
        await SupabaseConnectionPool._global_pool.initialize()
    return SupabaseConnectionPool._global_pool

async def close_pool() -> None:
    if SupabaseConnectionPool._global_pool is not None:
        await SupabaseConnectionPool._global_pool.close()
        SupabaseConnectionPool._global_pool = None
