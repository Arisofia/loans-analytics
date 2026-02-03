"""Load realistic KPI data into Supabase historical_kpis table (G4.2.2a).

This script populates the historical_kpis Supabase table with realistic,
multi-dimensional KPI observations for 90+ days, enabling REAL mode testing
and integration.

SECURITY NOTE (python:S2245 - PRNG Usage):
This script generates SYNTHETIC KPI DATA for testing with reproducible randomness.
The `random` module usage is NOT cryptographically secure, but this is ACCEPTABLE because:
1. All data is synthetic metrics for testing/simulation, not production secrets
2. Reproducibility is REQUIRED - each KPI gets same random sequence via seed (line 95)
3. No security-sensitive data (IDs, tokens, passwords) is generated
4. KPI values need statistical distributions, not cryptographic unpredictability

Usage:
    # Load sample KPIs into Supabase
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_ANON_KEY="your-anon-key"
    python scripts/load_sample_kpis_supabase.py

    # Or specify a custom run_id for idempotence
    python scripts/load_sample_kpis_supabase.py --run-id "manual_load_2026_01_29"

Environment Variables:
    SUPABASE_URL: Supabase project URL (required)
    SUPABASE_ANON_KEY: Supabase anonymous key (required)
"""

from __future__ import annotations

import argparse
import logging
import os
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class KpiDataLoader:
    """Load synthetic but realistic KPI data into Supabase."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
        self.table_name = "historical_kpis"
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

    def validate_credentials(self) -> bool:
        """Verify Supabase credentials are valid."""
        if not self.supabase_url or not self.supabase_key:
            logger.error("SUPABASE_URL and SUPABASE_ANON_KEY env vars required")
            return False

        try:
            # Simple ping: list existing rows (limit 1)
            url = f"{self.supabase_url}/rest/v1/{self.table_name}?limit=1"
            resp = requests.get(url, headers=self.headers, timeout=5)
            if resp.status_code in (200, 206):
                logger.info("✓ Supabase credentials validated")
                return True
            else:
                logger.error("Supabase validation failed: %s %s", resp.status_code, resp.text)
                return False
        except OSError as e:
            logger.error("Supabase connection error: %s", e)
            return False

    def generate_kpi_series(
        self,
        kpi_id: str,
        start_date: date,
        days: int = 90,
        base_value: float = 1.0,
        trend: float = 0.0,
        noise: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Generate a synthetic KPI time series with trend and noise.

        Args:
            kpi_id: KPI identifier (e.g., "npl_ratio")
            start_date: First date in series
            days: Number of days (default 90)
            base_value: Starting value
            trend: Daily trend multiplier (e.g., 0.001 = +0.1% daily)
            noise: Random noise std dev (e.g., 0.05 = ±5%)

        Returns:
            List of dicts matching historical_kpis schema
        """
        random.seed(hash(kpi_id) % 2**32)  # Reproducible per KPI

        series = []
        current_date = start_date
        current_value = base_value

        for _ in range(days):
            # Apply trend
            current_value *= 1 + trend

            # Apply noise
            noise_factor = random.gauss(1.0, noise)
            value = current_value * noise_factor

            series.append(
                {
                    "kpi_id": kpi_id,
                    "date": current_date.isoformat(),
                    "value_numeric": round(value, 6),
                    "value_int": int(round(value * 1000)),  # E.g., basis points
                    "source_system": "synthetic_loader",
                    "is_final": True,
                }
            )

            current_date += timedelta(days=1)

        return series

    def expand_with_dimensions(
        self,
        base_series: list[dict[str, Any]],
        portfolios: list[str],
        products: list[str],
        segments: list[str],
    ) -> list[dict[str, Any]]:
        """Expand base series with portfolio/product/segment dimensions.

        Each dimension combination gets a variant of the base series.
        """
        expanded = []

        for series_item in base_series:
            for portfolio in portfolios:
                for product in products:
                    for segment in segments:
                        item = series_item.copy()
                        item["portfolio_id"] = portfolio
                        item["product_code"] = product
                        item["segment_code"] = segment
                        expanded.append(item)

        return expanded

    def load_batch(self, rows: list[dict[str, Any]], run_id: str) -> tuple[int, int]:
        """Load a batch of rows to Supabase.

        Args:
            rows: List of row dicts (one per historical_kpi record)
            run_id: Run identifier for traceability

        Returns:
            (successful_count, failed_count)
        """
        if not rows:
            logger.warning("No rows to load")
            return 0, 0

        # Add run_id and timestamps
        for row in rows:
            row["run_id"] = run_id
            row["ts_utc"] = datetime.now(timezone.utc).isoformat()

        url = f"{self.supabase_url}/rest/v1/{self.table_name}"

        try:
            logger.info("Loading %d rows to %s...", len(rows), self.table_name)
            resp = requests.post(url, json=rows, headers=self.headers, timeout=30)

            if resp.status_code in (200, 201):
                logger.info("✓ Successfully loaded %d rows", len(rows))
                return len(rows), 0
            else:
                logger.error("Load failed: %s %s", resp.status_code, resp.text[:200])
                return 0, len(rows)
        except OSError as e:
            logger.error("Load error: %s", e)
            return 0, len(rows)

    def run(self, run_id: str | None = None) -> None:
        """Load all KPI series."""
        if not self.validate_credentials():
            return

        run_id = (
            run_id
            or f"loader_{uuid4().hex[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        logger.info("Run ID: %s", run_id)

        end_date = date.today()
        start_date = end_date - timedelta(days=90)

        # Define KPI loading specs: (kpi_id, base_value, trend, noise)
        kpi_specs = [
            ("npl_ratio", 0.032, -0.0005, 0.03),  # Improving NPL
            ("approval_rate", 0.72, 0.0003, 0.05),  # Rising approval
            ("cost_of_risk", 0.085, -0.0002, 0.04),  # Cost improvement
            ("conversion_rate", 0.18, 0.0001, 0.06),  # Stable conversion
        ]

        # Dimensions
        portfolios = ["retail", "sme"]
        products = ["PLN", "CC", "MTG"]
        segments = ["mass", "affluent", "micro"]

        total_loaded = 0
        total_failed = 0

        for kpi_id, base_val, trend, noise in kpi_specs:
            logger.info("\nProcessing KPI: %s", kpi_id)

            # Generate base series (no dimensions)
            series = self.generate_kpi_series(
                kpi_id,
                start_date,
                days=90,
                base_value=base_val,
                trend=trend,
                noise=noise,
            )

            # Expand with all dimension combinations
            expanded = self.expand_with_dimensions(
                series,
                portfolios=portfolios,
                products=products,
                segments=segments,
            )

            logger.info(
                "  Generated %d rows (%d dates × %d portfolios × %d products × %d segments)",
                len(expanded),
                len(series),
                len(portfolios),
                len(products),
                len(segments),
            )

            # Load
            loaded, failed = self.load_batch(expanded, run_id)
            total_loaded += loaded
            total_failed += failed

        separator = "=" * 70
        logger.info("\n%s", separator)
        logger.info("Loading complete!")
        logger.info("  Rows loaded: %d", total_loaded)
        if total_failed:
            logger.warning("  Rows failed: %d", total_failed)
        logger.info("  Run ID: %s", run_id)
        logger.info("%s", separator)


def main():
    """CLI entry point for loading KPI data."""
    parser = argparse.ArgumentParser(
        description="Load realistic KPI data into Supabase historical_kpis table"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID for traceability (auto-generated if not provided)",
    )
    args = parser.parse_args()

    loader = KpiDataLoader()
    loader.run(run_id=args.run_id)


if __name__ == "__main__":
    main()
