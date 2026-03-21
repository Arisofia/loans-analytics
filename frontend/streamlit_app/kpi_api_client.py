"""
KPI Analytics API Client - Dashboard Integration Library.

Provides a lightweight client for consuming KPI data from the FastAPI
analytics endpoint, with built-in support for caching, error handling,
and threshold enrichment.

Usage:
    from frontend.streamlit_app.kpi_api_client import KPIAPIClient

    client = KPIAPIClient(api_url="http://localhost:8000")
    kpis = client.get_latest_kpis()  # Synchronous wrapper

    # Or use async directly
    import asyncio
    async def main():
        kpis = await client.async_get_latest_kpis()
    asyncio.run(main())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import os

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class KPIResponse:
    """Represents a single KPI with threshold metadata."""

    id: str
    name: str
    value: float
    unit: str
    threshold_status: str  # normal, warning, critical, not_configured
    thresholds: dict[str, float] = field(default_factory=dict)
    updated_at: Optional[str] = None

    def is_critical(self) -> bool:
        """Check if KPI is in critical state."""
        return self.threshold_status == "critical"

    def is_warning(self) -> bool:
        """Check if KPI is in warning state."""
        return self.threshold_status == "warning"

    def is_normal(self) -> bool:
        """Check if KPI is in normal state."""
        return self.threshold_status == "normal"

    def is_configured(self) -> bool:
        """Check if KPI has thresholds configured."""
        return self.threshold_status != "not_configured"


class KPIAPIClient:
    """
    Client for KPI Analytics API.

    Handles:
    - HTTP communication with FastAPI endpoint
    - Result caching with TTL
    - Error handling and fallback strategies
    - Threshold status enrichment
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: int = 30,
        cache_ttl: int = 60,
    ):
        """
        Initialize KPI API client.

        Args:
            api_url: Base URL of analytics API (default: FASTAPI_API_URL env var)
            timeout: HTTP request timeout in seconds
            cache_ttl: Cache time-to-live in seconds
        """
        self.api_url = api_url or os.getenv("KPI_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[Any, float]] = {}
        self._httpx_client: Optional[httpx.Client] = None

        if not httpx:
            logger.warning("httpx not installed - API client will not function")

    def _get_client(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._httpx_client is None:
            self._httpx_client = httpx.Client(timeout=self.timeout)
        return self._httpx_client

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached value is still valid."""
        if cache_key not in self._cache:
            return False

        _, timestamp = self._cache[cache_key]
        age = datetime.now(timezone.utc).timestamp() - timestamp
        return age < self.cache_ttl

    def get_latest_kpis(
        self,
        kpi_keys: Optional[list[str]] = None,
        portfolio_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch latest KPIs from API.

        Args:
            kpi_keys: List of specific KPI IDs to fetch (all if None)
            portfolio_id: Portfolio context for calculations
            use_cache: Use cached results if available

        Returns:
            Dict with 'kpis' list and metadata

        Raises:
            ConnectionError: If API is unreachable
            ValueError: If API response is invalid
        """
        if not httpx:
            raise ImportError("httpx required for API client")

        # Check cache
        cache_key = f"latest_kpis_{','.join(kpi_keys or [])}"
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for {cache_key}")
            data, _ = self._cache[cache_key]
            return data

        try:
            # Build request
            params = {}
            if kpi_keys:
                params["kpi_keys"] = ",".join(kpi_keys)
            if portfolio_id:
                params["portfolio_id"] = portfolio_id

            # Make request
            client = self._get_client()
            response = client.get(
                f"{self.api_url}/analytics/kpis/latest",
                params=params,
            )
            response.raise_for_status()

            data = response.json()

            # Parse KPI responses
            kpis = []
            for kpi_data in data.get("kpis", []):
                kpi = KPIResponse(
                    id=kpi_data.get("id", ""),
                    name=kpi_data.get("name", ""),
                    value=float(kpi_data.get("value", 0)),
                    unit=kpi_data.get("unit", "unknown"),
                    threshold_status=kpi_data.get("threshold_status", "not_configured"),
                    thresholds=kpi_data.get("thresholds", {}),
                    updated_at=kpi_data.get("updated_at"),
                )
                kpis.append(kpi)

            result = {
                "kpis": kpis,
                "timestamp": data.get("timestamp"),
                "metrics_published": data.get("metrics_published", False),
            }

            # Cache result
            self._cache[cache_key] = (result, datetime.now(timezone.utc).timestamp())

            return result

        except Exception as e:
            # Handle both httpx errors and other exceptions
            error_msg = str(e)

            # Check if it's an HTTP error or connection error
            if isinstance(e, (ValueError, KeyError, KeyboardInterrupt, SystemExit)):
                logger.error(f"Invalid API response: {error_msg}")
                if isinstance(e, (ValueError, KeyError)):
                    raise ValueError("Invalid API response format") from e
                raise
            else:
                # All other exceptions are treated as connection errors
                logger.error(f"API request failed: {error_msg}")
                raise ConnectionError(f"Failed to fetch KPIs from {self.api_url}") from e

    def get_kpi_value(
        self,
        kpi_id: str,
        use_cache: bool = True,
    ) -> KPIResponse:
        """
        Fetch single KPI with full context.

        Args:
            kpi_id: KPI identifier
            use_cache: Use cached results if available

        Returns:
            KPI response with thresholds

        Raises:
            ConnectionError: If API is unreachable
            ValueError: If KPI not found
        """
        if not httpx:
            raise ImportError("httpx required for API client")

        cache_key = f"kpi_{kpi_id}"
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for {cache_key}")
            data, _ = self._cache[cache_key]
            return data

        try:
            client = self._get_client()
            response = client.post(
                f"{self.api_url}/analytics/kpis/{kpi_id}",
                json={},
            )
            response.raise_for_status()

            data = response.json()

            kpi = KPIResponse(
                id=data.get("id", kpi_id),
                name=data.get("name", ""),
                value=float(data.get("value", 0)),
                unit=data.get("unit", "unknown"),
                threshold_status=data.get("threshold_status", "not_configured"),
                thresholds=data.get("thresholds", {}),
                updated_at=data.get("updated_at"),
            )

            # Cache result
            self._cache[cache_key] = (kpi, datetime.now(timezone.utc).timestamp())

            return kpi

        except Exception as e:
            # Handle both httpx errors and other exceptions
            error_msg = str(e)

            if isinstance(e, ValueError):
                logger.error(f"Invalid KPI response: {error_msg}")
                raise
            else:
                logger.error(f"Failed to fetch KPI {kpi_id}: {error_msg}")
                raise ConnectionError(f"Failed to fetch KPI {kpi_id}") from e

    def get_critical_kpis(
        self,
        kpi_keys: Optional[list[str]] = None,
    ) -> list[KPIResponse]:
        """Get all KPIs currently in critical status."""
        data = self.get_latest_kpis(kpi_keys=kpi_keys)
        return [kpi for kpi in data["kpis"] if kpi.is_critical()]

    def get_warning_kpis(
        self,
        kpi_keys: Optional[list[str]] = None,
    ) -> list[KPIResponse]:
        """Get all KPIs currently in warning status."""
        data = self.get_latest_kpis(kpi_keys=kpi_keys)
        return [kpi for kpi in data["kpis"] if kpi.is_warning()]

    def get_kpi_summary(
        self,
        kpi_keys: Optional[list[str]] = None,
    ) -> dict[str, int]:
        """Get summary of KPI statuses."""
        data = self.get_latest_kpis(kpi_keys=kpi_keys)
        summary = {
            "normal": 0,
            "warning": 0,
            "critical": 0,
            "not_configured": 0,
        }
        for kpi in data["kpis"]:
            summary[kpi.threshold_status] += 1
        return summary

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self._cache.clear()
        logger.debug("API client cache cleared")

    def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._httpx_client:
            self._httpx_client.close()
            self._httpx_client = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Thread-safe singleton for Streamlit caching
_client_instance: Optional[KPIAPIClient] = None


def get_client(
    api_url: Optional[str] = None,
    timeout: int = 30,
) -> KPIAPIClient:
    """Get or create KPI API client (singleton pattern)."""
    global _client_instance

    if _client_instance is None:
        _client_instance = KPIAPIClient(api_url=api_url, timeout=timeout)

    return _client_instance
