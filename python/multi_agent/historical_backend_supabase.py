"""
Supabase-backed Historical Data Backend.

Provides integration with Supabase for storing and retrieving
historical KPI data in production environments.

Phase G4.2 Implementation
"""

import os
from datetime import date
from typing import Any, Dict, List

import requests

from .historical_context import HistoricalDataBackend, KpiHistoricalValue


class SupabaseHistoricalBackend(HistoricalDataBackend):
    """
    Supabase-backed implementation of HistoricalDataBackend.

    This uses Supabase REST API (PostgREST) to fetch historical KPI
    observations for a given kpi_id and date range.

    Environment Variables (required):
        - SUPABASE_URL: Supabase project URL
        - SUPABASE_ANON_KEY: Supabase anonymous/service key
        - SUPABASE_HISTORICAL_KPI_TABLE: Table name (default: "historical_kpis")

    Table Schema (expected, Phase G4.2.1):
        CREATE TABLE historical_kpis (
            id BIGSERIAL PRIMARY KEY,
            kpi_id TEXT NOT NULL,
            portfolio_id TEXT,
            product_code TEXT,
            segment_code TEXT,
            date DATE NOT NULL,
            ts_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            value_numeric NUMERIC(18,6),
            value_int BIGINT,
            value_json JSONB,
            source_system TEXT,
            run_id TEXT,
            is_final BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX idx_hkpi_kpi_date
            ON historical_kpis(kpi_id, date);

    Usage:
        backend = SupabaseHistoricalBackend()
        provider = HistoricalContextProvider(
            mode="REAL",
            backend=backend
        )

    Raises:
        RuntimeError: If required environment variables are not set
        requests.HTTPError: If Supabase API request fails
    """

    def __init__(self) -> None:
        """Initialize Supabase backend with environment configuration."""
        self.base_url = os.getenv("SUPABASE_URL")
        self.api_key = os.getenv("SUPABASE_ANON_KEY")
        self.table = os.getenv("SUPABASE_HISTORICAL_KPI_TABLE", "historical_kpis")

        if not self.base_url or not self.api_key:
            raise RuntimeError(
                "SupabaseHistoricalBackend requires SUPABASE_URL "
                "and SUPABASE_ANON_KEY environment variables. "
                "Set them before using REAL mode."
            )

        self._headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_kpi_history(
        self,
        kpi_id: str,
        start_date: date,
        end_date: date,
    ) -> List[KpiHistoricalValue]:
        """
        Retrieve historical KPI values from Supabase.

        Uses PostgREST query syntax to filter by kpi_id and date range.

        Args:
            kpi_id: KPI identifier
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of KpiHistoricalValue objects sorted by date

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If response data is malformed
        """
        # Build Supabase REST API URL
        # Format: /rest/v1/{table}?filters...
        url = f"{self.base_url}/rest/v1/{self.table}"

        # PostgREST filter syntax:
        # - eq: equals
        # - gte: greater than or equal
        # - lte: less than or equal
        # - Comma-separated for multiple conditions on same field
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        params = {
            "kpi_id": f"eq.{kpi_id}",
            "date": f"gte.{start_iso},lte.{end_iso}",
            "order": "date.asc",
            "select": "kpi_id,date,value_numeric,ts_utc",
        }

        # Execute request with timeout
        response = requests.get(url, headers=self._headers, params=params, timeout=10)
        response.raise_for_status()

        # Parse JSON response
        data: List[Dict[str, Any]] = response.json()

        # Convert to KpiHistoricalValue objects
        return [
            KpiHistoricalValue(
                kpi_id=row["kpi_id"],
                date=row["date"],
                value=float(row["value_numeric"]) if row.get("value_numeric") else 0.0,
                timestamp=row["ts_utc"],
            )
            for row in data
        ]
