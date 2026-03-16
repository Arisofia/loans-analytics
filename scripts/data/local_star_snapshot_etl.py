#!/usr/bin/env python3
"""Run local monthly ETL and produce star-schema exports for Fly.io/Supabase stack."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.zero_cost.local_migration_etl import LocalMonthlySnapshotETL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger("local_star_snapshot_etl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build monthly star schema snapshot from raw CSV files")
    parser.add_argument("--loan-tape-dir", default="data/raw", help="Directory with loan tape CSV files")
    parser.add_argument("--control-mora", default="", help="Optional control mora CSV path")
    parser.add_argument("--snapshot-month", required=True, help="Snapshot month YYYY-MM-DD")
    parser.add_argument("--output-dir", default="exports/local_star", help="Output directory")
    return parser.parse_args()


def _write(df: pd.DataFrame, output_dir: Path, name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{name}.csv"
    parquet_path = output_dir / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    logger.info("Wrote %s (%d rows)", csv_path, len(df))


def main() -> None:
    args = parse_args()
    etl = LocalMonthlySnapshotETL(snapshot_month=args.snapshot_month)
    result = etl.run(
        loan_tape_dir=args.loan_tape_dir,
        control_mora_path=args.control_mora or None,
    )

    out = Path(args.output_dir)
    _write(result.dim_loan, out, "dim_loan")
    _write(result.fact_schedule, out, "fact_schedule")
    _write(result.fact_real_payment, out, "fact_real_payment")
    _write(result.fact_monthly_snapshot, out, "fact_monthly_snapshot")
    _write(result.payment_reconciliation, out, "payment_reconciliation")

    unmatched_path = out / "unmatched_records.csv"
    result.unmatched_records.to_csv(unmatched_path, index=False)
    logger.info("Wrote %s (%d rows)", unmatched_path, len(result.unmatched_records))

    if "reason_code" in result.unmatched_records.columns:
        invalid = result.unmatched_records["reason_code"].fillna("").str.strip().eq("").sum()
        if invalid:
            raise SystemExit(f"Invalid unmatched_records: {invalid} rows without reason_code")


if __name__ == "__main__":
    main()
