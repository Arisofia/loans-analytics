#!/usr/bin/env python3
"""Run scale benchmarks for KPI engine across configurable portfolio sizes."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline.calculation import CalculationPhase
from src.pipeline.config import load_kpi_definitions


def _build_synthetic_loans(rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = np.datetime64("2024-01-01")

    principal = rng.uniform(800.0, 45_000.0, size=rows).round(2)
    outstanding = (principal * rng.uniform(0.2, 1.0, size=rows)).round(2)
    scheduled = (principal * rng.uniform(0.01, 0.08, size=rows)).round(2)

    return pd.DataFrame(
        {
            "loan_id": np.arange(1, rows + 1, dtype=np.int64).astype(str),
            "borrower_id": rng.integers(1, max(rows // 3, 2), size=rows, dtype=np.int64),
            "principal_amount": principal,
            "outstanding_balance": outstanding,
            "current_balance": (principal * rng.uniform(0.0, 0.4, size=rows)).round(2),
            "interest_rate": rng.uniform(0.08, 0.32, size=rows).round(4),
            "dpd": rng.integers(0, 180, size=rows, dtype=np.int64),
            "status": rng.choice(
                ["active", "defaulted", "closed"], p=[0.82, 0.08, 0.10], size=rows
            ),
            "origination_date": (start + rng.integers(0, 730, size=rows)).astype(str),
            "last_payment_amount": (scheduled * rng.uniform(0.1, 1.1, size=rows)).round(2),
            "total_scheduled": np.maximum(scheduled, 1.0),
            "tpv": (principal * rng.uniform(1.0, 2.5, size=rows)).round(2),
            "term_months": rng.integers(6, 72, size=rows, dtype=np.int64),
            "payment_frequency": rng.choice(
                ["monthly", "biweekly", "bullet"], p=[0.7, 0.2, 0.1], size=rows
            ),
        }
    )


def _parse_rows(rows: str) -> list[int]:
    parsed = []
    for item in rows.split(","):
        value = item.strip()
        if not value:
            continue
        parsed.append(int(value))
    return parsed


def _run_once(df: pd.DataFrame, use_polars: bool) -> dict[str, Any]:
    previous = os.getenv("KPI_ENGINE_USE_POLARS")
    os.environ["KPI_ENGINE_USE_POLARS"] = "1" if use_polars else "0"
    try:
        phase = CalculationPhase(config={}, kpi_definitions=load_kpi_definitions())
        started = time.perf_counter()
        result = phase.execute(df=df, run_dir=None)
        elapsed = time.perf_counter() - started
    finally:
        if previous is None:
            os.environ.pop("KPI_ENGINE_USE_POLARS", None)
        else:
            os.environ["KPI_ENGINE_USE_POLARS"] = previous

    return {
        "status": result.get("status", "unknown"),
        "kpi_count": int(result.get("kpi_count", 0)),
        "duration_seconds": round(elapsed, 6),
        "rows_per_second": round(len(df) / elapsed, 2) if elapsed > 0 else 0.0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rows",
        default="100000,500000,1000000",
        help="Comma-separated row counts to benchmark.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Base random seed.")
    parser.add_argument("--trials", type=int, default=2, help="Trials per row count.")
    parser.add_argument(
        "--mode",
        choices=["polars", "pandas", "both"],
        default="both",
        help="Execution backend mode.",
    )
    parser.add_argument(
        "--target-seconds",
        type=float,
        default=5.0,
        help="Performance target used for pass/fail checks.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("logs/performance/kpi_engine_scale_benchmark.json"),
        help="Output JSON path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows_to_run = _parse_rows(args.rows)
    backends: list[tuple[str, bool]]
    if args.mode == "both":
        backends = [("pandas", False), ("polars", True)]
    elif args.mode == "polars":
        backends = [("polars", True)]
    else:
        backends = [("pandas", False)]

    runs: list[dict[str, Any]] = []
    for rows in rows_to_run:
        df = _build_synthetic_loans(rows, args.seed + rows)
        for backend_name, use_polars in backends:
            durations = []
            trial_status = "success"
            for trial in range(args.trials):
                result = _run_once(df, use_polars=use_polars)
                durations.append(result["duration_seconds"])
                if result["status"] != "success":
                    trial_status = "failed"
                runs.append(
                    {
                        "rows": rows,
                        "backend": backend_name,
                        "trial": trial + 1,
                        **result,
                    }
                )

            median_seconds = float(np.median(np.array(durations))) if durations else float("nan")
            print(
                f"rows={rows:,} backend={backend_name:<6} "
                f"median={median_seconds:.3f}s status={trial_status}"
            )

    summary_by_backend: dict[str, dict[int, float]] = {}
    for run in runs:
        backend = run["backend"]
        rows = int(run["rows"])
        summary_by_backend.setdefault(backend, {}).setdefault(rows, [])
        summary_by_backend[backend][rows].append(float(run["duration_seconds"]))

    median_table: dict[str, dict[str, Any]] = {}
    overall_pass = True
    for backend, by_rows in summary_by_backend.items():
        median_table[backend] = {}
        for rows, durations in by_rows.items():
            median_value = float(np.median(np.array(durations)))
            target_met = median_value <= args.target_seconds
            overall_pass = overall_pass and target_met
            median_table[backend][str(rows)] = {
                "median_seconds": round(median_value, 6),
                "target_seconds": args.target_seconds,
                "target_met": target_met,
            }

    payload = {
        "target_seconds": args.target_seconds,
        "mode": args.mode,
        "trials": args.trials,
        "runs": runs,
        "medians": median_table,
        "overall_target_met": overall_pass,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"overall_target_met": overall_pass, "output": str(args.out)}, indent=2))
    return 0 if overall_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
