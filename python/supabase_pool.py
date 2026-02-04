"""
Supabase connection pooling implementation.

Provides async connection pooling for Supabase PostgreSQL database
with automatic retry, health checks, and observability.
"""

from __future__ import annotations

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment,misc]

from python.config import settings

logger = logging.getLogger(__name__)


class SupabaseConnectionPool:
    """
    Async connection pool manager for Supabase PostgreSQL.

    Features:
    - Connection pooling with configurable min/max connections
    - Automatic reconnection with exponential backoff
    - Connection health checks
    - Graceful shutdown
    - Observability metrics
    """

    def __init__(
        self,
        database_url: str,
        *,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        command_timeout: Optional[int] = None,
        max_idle_time: Optional[int] = None,
        max_lifetime: Optional[int] = None,
    ):
        """
        Initialize connection pool.

        Args:
            database_url: PostgreSQL connection string
            min_size: Minimum pool connections (default from config)
            max_size: Maximum pool connections (default from config)
            command_timeout: Command timeout in seconds (default from config)
            max_idle_time: Max idle time before recycling (default from config)
            max_lifetime: Max connection lifetime (default from config)
        """
        if asyncpg is None:
            raise ImportError(
                "asyncpg is required for connection pooling. Install with: pip install asyncpg"
            )

        # Security: Store only normalized URL, never raw URL with password
        self._normalized_url = self._normalize_database_url(database_url)
        self.pool_config = settings.supabase_pool

        # Override with explicit parameters
        self.min_size = min_size or self.pool_config.min_size
        self.max_size = max_size or self.pool_config.max_size
        self.command_timeout = command_timeout or self.pool_config.command_timeout
        self.max_idle_time = max_idle_time or self.pool_config.max_idle_time
        self.max_lifetime = max_lifetime or self.pool_config.max_lifetime

        self._pool: Optional[asyncpg.Pool] = None
        self._metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "queries_executed": 0,
            "queries_failed": 0,
        }

    def _normalize_database_url(self, url: str) -> str:
        """
        Normalize Supabase database URL to asyncpg-compatible format.

        Supabase provides different URL formats:
        - Direct database: postgres://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
        - Connection pooler:
          postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION]
          .pooler.supabase.com:6543/postgres

        Args:
            url: Original database URL

        Returns:
            Normalized URL compatible with asyncpg
        """
        # Replace 'postgres://' with 'postgresql://' for asyncpg compatibility
        if url.startswith("postgres://") and not url.startswith("postgresql://"):
            url = url.replace("postgres://", "postgresql://", 1)

        # Handle Supabase connection pooler format: postgres.[PROJECT_REF]:[PASSWORD]@host
        # Extract and reformat to standard postgres://user:password@host format
        pooler_pattern = r"postgresql://postgres\.([^:]+):([^@]+)@(.+)"
        match = re.match(pooler_pattern, url)
        if match:
            project_ref, password, rest = match.groups()
            url = f"postgresql://postgres:{password}@{rest}"
            logger.info("Normalized Supabase pooler URL (project: %s)", project_ref)

        return url

    def __repr__(self) -> str:
        """
        Secure representation without exposing credentials.

        Returns:
            Safe string representation
        """
        return f"<SupabaseConnectionPool(id={id(self):#x}, size={self.max_size})>"

    def __str__(self) -> str:
        """
        Secure string without exposing credentials.

        Returns:
            Safe string representation
        """
        return f"SupabaseConnectionPool(max_connections={self.max_size})"

    async def initialize(self) -> None:
        """Initialize connection pool."""
        if not self.pool_config.enabled:
            logger.warning("Connection pooling is disabled in configuration")
            return

        try:
            logger.info(
                "Initializing Supabase connection pool (min=%d, max=%d, timeout=%ds)",
                self.min_size,
                self.max_size,
                self.command_timeout,
            )

            self._pool = await asyncpg.create_pool(
                self._normalized_url,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.command_timeout,
                max_inactive_connection_lifetime=self.max_idle_time,
            )

            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._metrics["total_connections"] = self._pool.get_size()
            logger.info("✅ Connection pool initialized with %d connections", self._pool.get_size())

        except Exception as e:
            self._metrics["failed_connections"] += 1
            logger.error("❌ Failed to initialize connection pool: %s", e, exc_info=True)
            raise

    async def close(self) -> None:
        """Close connection pool gracefully."""
        if self._pool:
            logger.info("Closing connection pool...")
            await self._pool.close()
            logger.info("✅ Connection pool closed")
            self._pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """
        Acquire a connection from the pool.

        Yields:
            Database connection

        Example:
            async with pool.acquire() as conn:
                result = await conn.fetch("SELECT * FROM loans")
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")

        max_retries = self.pool_config.max_retries
        retry_delay = self.pool_config.retry_delay

        for attempt in range(max_retries):
            try:
                async with self._pool.acquire() as connection:
                    self._metrics["active_connections"] += 1
                    try:
                        yield connection
                    finally:
                        self._metrics["active_connections"] -= 1
                return

            except asyncpg.PostgresError as e:
                self._metrics["failed_connections"] += 1

                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        "Connection attempt %d/%d failed: %s. Retrying in %ds...",
                        attempt + 1,
                        max_retries,
                        e,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("All %d connection attempts failed", max_retries, exc_info=True)
                    raise

    async def execute(self, query: str, *args: Any) -> str:
        """
        Execute a query with automatic retry.

        Args:
            query: SQL query to execute
            *args: Query parameters

        Returns:
            Query execution status
        """
        try:
            async with self.acquire() as conn:
                await asyncio.wait_for(conn.execute(query, *args), timeout=self.command_timeout)
                self._metrics["queries_executed"] += 1
                return "success"
        except asyncio.TimeoutError:
            self._metrics["queries_failed"] += 1
            logger.error("Query execution timed out after %ss", self.command_timeout)
            raise
        except Exception as e:
            self._metrics["queries_failed"] += 1
            logger.error("Query execution failed: %s", e, exc_info=True)
            raise

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """
        Fetch multiple rows with automatic retry.

        Args:
            query: SQL query to execute
            *args: Query parameters

        Returns:
            List of records
        """
        try:
            async with self.acquire() as conn:
                result = await asyncio.wait_for(
                    conn.fetch(query, *args), timeout=self.command_timeout
                )
                self._metrics["queries_executed"] += 1
                return result
        except asyncio.TimeoutError:
            self._metrics["queries_failed"] += 1
            logger.error("Query fetch timed out after %ss", self.command_timeout)
            raise
        except Exception as e:
            self._metrics["queries_failed"] += 1
            logger.error("Query fetch failed: %s", e, exc_info=True)
            raise

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        """
        Fetch a single row with automatic retry.

        Args:
            query: SQL query to execute
            *args: Query parameters

        Returns:
            Single record or None
        """
        try:
            async with self.acquire() as conn:
                result = await asyncio.wait_for(
                    conn.fetchrow(query, *args), timeout=self.command_timeout
                )
                self._metrics["queries_executed"] += 1
                return result
        except asyncio.TimeoutError:
            self._metrics["queries_failed"] += 1
            logger.error("Query fetchrow timed out after %ss", self.command_timeout)
            raise
        except Exception as e:
            self._metrics["queries_failed"] += 1
            logger.error("Query fetchrow failed: %s", e, exc_info=True)
            raise

    async def health_check(self) -> dict[str, Any]:
        """
        Check pool health and return metrics.

        Returns:
            Pool health metrics
        """
        if not self._pool:
            return {
                "status": "not_initialized",
                "healthy": False,
                "metrics": self._metrics,
            }

        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")

            return {
                "status": "healthy",
                "healthy": True,
                "pool_size": self._pool.get_size(),
                "free_connections": self._pool.get_idle_size(),
                "metrics": self._metrics,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
                "metrics": self._metrics,
            }

    def get_metrics(self) -> dict[str, int]:
        """Get current pool metrics."""
        return {
            **self._metrics,
            "pool_size": self._pool.get_size() if self._pool else 0,
            "free_connections": self._pool.get_idle_size() if self._pool else 0,
        }

    # Global pool instance (singleton pattern)
    _global_pool: Optional[SupabaseConnectionPool] = None


async def get_pool(database_url: Optional[str] = None) -> SupabaseConnectionPool:
    """
    Get or create global connection pool instance.

    Args:
        database_url: Optional database URL override

    Returns:
        Connection pool instance
    """
    # pylint: disable=protected-access  # Intentional singleton pattern
    if SupabaseConnectionPool._global_pool is None:
        if not database_url:
            raise ValueError("database_url required for pool initialization")

        SupabaseConnectionPool._global_pool = SupabaseConnectionPool(database_url)
        await SupabaseConnectionPool._global_pool.initialize()

    return SupabaseConnectionPool._global_pool


async def close_pool() -> None:
    """Close global connection pool."""
    # pylint: disable=protected-access  # Intentional singleton pattern
    if SupabaseConnectionPool._global_pool is not None:
        await SupabaseConnectionPool._global_pool.close()
        # Reset the global connection pool instance
        SupabaseConnectionPool._global_pool = None
