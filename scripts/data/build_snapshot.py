#!/usr/bin/env python3
"""
Build a monthly Control-de-Mora snapshot into the DuckDB star schema.

Usage
-----
    python scripts/data/build_snapshot.py \
        --input data/raw/control_mora_ene2026.csv \
        --month 2026-01-31

Environment variables (alternative to CLI flags):
    INPUT  — path to CSV
    MONTH  — snapshot month (YYYY-MM-DD or YYYY-MM)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure repo root is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
from backend.src.zero_cost.storage import ZeroCostStorage


def main() -> None:
    parser = argparse.ArgumentParser(description="Build monthly snapshot into DuckDB star schema")
    parser.add_argument(
        "--input",
        default=os.environ.get("INPUT", "data/samples/abaco_sample_data_20260202.csv"),
        help="Path to Control-de-Mora CSV file",
    )
    parser.add_argument(
        "--month",
        default=os.environ.get("MONTH", ""),
        help="Snapshot month (YYYY-MM-DD or YYYY-MM).  Inferred from filename if omitted.",
    )
    parser.add_argument(
        "--duckdb",
        default="data/duckdb/analytics.duckdb",
        help="Path to DuckDB database file",
    )
    parser.add_argument(
        "--parquet-dir",
        default="data/duckdb",
        help="Base directory for Parquet outputs",
    )
    args = parser.parse_args()

    # Load
    print(f"📥  Loading: {args.input}")
    adapter = ControlMoraAdapter(snapshot_month=args.month or None)
    loans_df = adapter.load(args.input)
    print(f"   Loaded {len(loans_df)} rows")

    # Build snapshot
    print("🔨  Building monthly snapshot...")
    builder = MonthlySnapshotBuilder()
    snap_df = builder.build(loans_df, as_of_month=args.month or None)
    print(f"   Snapshot: {len(snap_df)} rows")

    # Persist to star schema
    storage = ZeroCostStorage(
        base_dir=args.parquet_dir,
        db_path=args.duckdb,
    )
    try:
        print("💾  Writing star-schema tables...")
        tables = builder.to_star_schema(snap_df, storage)
        for name, df in tables.items():
            print(f"   {name}: {len(df)} rows")
    finally:
        storage.close()

    # Print KPIs
    kpis = builder.compute_portfolio_kpis(snap_df)
    print("\n📊  Portfolio KPIs:")
    for k, v in kpis.items():
        if isinstance(v, dict):
            print(f"   {k}:")
            for bk, bv in v.items():
                print(f"      {bk}: {bv}")
        else:
            print(f"   {k}: {v}")

    print("\n✅  Snapshot build complete.")


if __name__ == "__main__":
    main()
