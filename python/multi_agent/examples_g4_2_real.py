"""G4.2 REAL/MOCK example: Fetch and display historical KPI data.

This script demonstrates the HistoricalContextProvider in both modes:
  - MOCK mode (default): Uses synthetic data, no Supabase required
  - REAL mode: Pulls from Supabase backend

Usage:
    # MOCK mode (no Supabase required)
    python -m python.multi_agent.examples_g4_2_real

    # REAL mode (requires Supabase env vars)
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_ANON_KEY="your-anon-key"
    export HISTORICAL_CONTEXT_MODE=REAL
    python -m python.multi_agent.examples_g4_2_real

    # Same script, different data source—demonstrates transparent switching.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from python.multi_agent.config_historical import build_historical_context_provider

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_example(kpi_id: str = "npl_ratio") -> None:
    """Fetch and display historical KPI data in configured mode."""
    mode = os.getenv("HISTORICAL_CONTEXT_MODE", "MOCK").upper()
    actual_mode = mode  # Track requested mode for reporting

    print("\n" + "=" * 70)
    print("G4.2 Historical KPI Example (Phase: Tangible REAL/MOCK)")
    print("=" * 70)
    print(f"KPI ID:  {kpi_id}")
    print(f"Mode:    {mode}")
    print(f"Date:    {datetime.now(timezone.utc).isoformat()}")
    print("-" * 70)

    history = None
    try:
        # Build provider using centralized factory
        provider = build_historical_context_provider(cache_ttl_seconds=60)

        # Fetch 30 days of history
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=30)

        history = provider._load_historical_data(kpi_id, start_dt, end_dt)

    except Exception as e:
        # If REAL mode fails, gracefully fall back to MOCK
        if mode == "REAL":
            print(f"\n⚠️  REAL mode failed: {type(e).__name__}")
            print("   Falling back to MOCK mode for demonstration...\n")
            mode = "MOCK"
            actual_mode = "REAL→MOCK (fallback)"
            try:
                provider = build_historical_context_provider(cache_ttl_seconds=60, mode="MOCK")
                end_dt = datetime.now(timezone.utc)
                start_dt = end_dt - timedelta(days=30)
                history = provider._load_historical_data(kpi_id, start_dt, end_dt)
            except Exception as fallback_error:
                print(f"✗ Both REAL and MOCK modes failed: {fallback_error}")
                raise
        else:
            raise

    # Display results (always runs after try/except)
    print(f"\nMode Used:   {actual_mode}")
    print(f"Observations: {len(history)}")

    if history:
        # Show first and last
        first = history[0]
        last = history[-1]

        print("\nFirst observation:")
        print(f"  Date:  {first.date}")
        print(f"  Value: {first.value}")

        print("\nLast observation:")
        print(f"  Date:  {last.date}")
        print(f"  Value: {last.value}")

        # Summary stats
        if len(history) > 1:
            values = [h.value for h in history if h.value is not None]
            if values:
                print("\nBasic stats:")
                print(f"  Min:   {min(values):.6f}")
                print(f"  Max:   {max(values):.6f}")
                print(f"  Mean:  {sum(values) / len(values):.6f}")

        # Show sample structure (first record)
        print("\nSample record structure:")
        print(f"  kpi_id:   {first.kpi_id}")
        print(f"  date:     {first.date}")
        print(f"  value:    {first.value}")
        print(f"  timestamp: {first.timestamp}")
    else:
        print("\nNo data returned. This is expected if:")
        print("  - In MOCK mode: KPI not in synthetic catalog")
        print("  - In REAL mode: historical_kpis table is empty or KPI not seeded")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_example()
