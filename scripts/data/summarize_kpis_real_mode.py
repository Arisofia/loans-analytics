"""Summarize REAL-mode KPIs over the last 90 days (G4.2.2c sanity check).

This script validates that REAL mode (Supabase) is returning meaningful,
trend-aware data after the loader has populated historical_kpis.

Usage:
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_ANON_KEY="your-anon-key"
    export HISTORICAL_CONTEXT_MODE=REAL

    source .venv/bin/activate
    python scripts/summarize_kpis_real_mode.py

Output:
    - KPI count, min/max/mean, and simple trend direction (up/down/flat)
    - Validates data quality before agents and dashboards rely on it
"""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timedelta, timezone

from python.multi_agent.config_historical import build_historical_context_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


KPI_IDS = [
    "npl_ratio",
    "approval_rate",
    "cost_of_risk",
    "conversion_rate",
]


def compute_stats(values: list[float]) -> dict[str, float]:
    """Compute basic statistics from a list of values."""
    if not values:
        return {"min": math.nan, "max": math.nan, "mean": math.nan}

    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def infer_trend(values: list[float]) -> str:
    """Classify trend direction by comparing first and last thirds of series.

    Returns:
        "up" if last third mean is >2% higher than first third
        "down" if last third mean is >2% lower than first third
        "flat" otherwise
        "insufficient data" if fewer than 6 observations
    """
    if len(values) < 6:
        return "insufficient data"

    n = len(values)
    third = max(n // 3, 1)
    first_mean = sum(values[:third]) / third
    last_mean = sum(values[-third:]) / third

    if first_mean == 0:
        # Avoid division by zero; use absolute difference instead
        if abs(last_mean - first_mean) > 0.001:
            return "up" if last_mean > first_mean else "down"
        return "flat"

    pct_change = (last_mean - first_mean) / abs(first_mean)
    if pct_change > 0.02:
        return "up"
    if pct_change < -0.02:
        return "down"
    return "flat"


def summarize_kpis(days: int = 90) -> None:
    """Fetch and summarize KPI statistics in REAL mode."""
    mode_env = os.getenv("HISTORICAL_CONTEXT_MODE", "MOCK").upper()
    if mode_env != "REAL":
        logger.warning(
            "HISTORICAL_CONTEXT_MODE=%s; summaries are intended for REAL mode.",
            mode_env,
        )

    provider = build_historical_context_provider()
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)

    print("\n" + "=" * 72)
    print("REAL-mode KPI Summary (G4.2.2c Validation)")
    print("=" * 72)
    print(f"Mode:   {provider.mode}")
    print(f"Window: {start_dt.date()} → {end_dt.date()} ({days} days)")
    print("=" * 72)

    for kpi_id in KPI_IDS:
        try:
            history = provider._load_historical_data(kpi_id, start_dt, end_dt)

            # Aggregate across all dimensions
            values = [obs.value for obs in history if obs.value is not None]

            if not values:
                print(f"  {kpi_id:<20} | No data")
                continue

            stats = compute_stats(values)
            trend = infer_trend(values)

            print(
                f"  {kpi_id:<20} | count={len(values):<4} "
                f"min={stats['min']:>10.6f}  max={stats['max']:>10.6f}  "
                f"mean={stats['mean']:>10.6f}  trend={trend:>4}"
            )
        except Exception as e:
            logger.error("Error fetching %s: %s", kpi_id, e)
            print(f"  {kpi_id:<20} | ERROR: {e}")

    print("=" * 72)
    print("✓ Summary complete")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    summarize_kpis()
