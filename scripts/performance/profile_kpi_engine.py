#!/usr/bin/env python3
"""Profile KPI calculation runtime with cProfile on real or synthetic data."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
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
    """Build a deterministic synthetic portfolio for scale testing."""
    rng = np.random.default_rng(seed)
    start = np.datetime64("2024-01-01")

    statuses = np.array(["active", "defaulted", "closed"])
    status_probs = np.array([0.82, 0.08, 0.10])
    payment_freqs = np.array(["monthly", "biweekly", "bullet"])
    payment_probs = np.array([0.7, 0.2, 0.1])

    principal = rng.uniform(800.0, 45_000.0, size=rows).round(2)
    outstanding = (principal * rng.uniform(0.2, 1.0, size=rows)).round(2)
    scheduled = (principal * rng.uniform(0.01, 0.08, size=rows)).round(2)
    last_payment = (scheduled * rng.uniform(0.1, 1.1, size=rows)).round(2)

    return pd.DataFrame(
        {
            "loan_id": np.arange(1, rows + 1, dtype=np.int64).astype(str),
            "borrower_id": rng.integers(1, max(rows // 3, 2), size=rows, dtype=np.int64),
            "principal_amount": principal,
            "outstanding_balance": outstanding,
            "current_balance": (principal * rng.uniform(0.0, 0.4, size=rows)).round(2),
            "interest_rate": rng.uniform(0.08, 0.32, size=rows).round(4),
            "dpd": rng.integers(0, 180, size=rows, dtype=np.int64),
            "status": rng.choice(statuses, p=status_probs, size=rows),
            "origination_date": (start + rng.integers(0, 730, size=rows)).astype(str),
            "last_payment_amount": last_payment,
            "total_scheduled": np.maximum(scheduled, 1.0),
            "tpv": (principal * rng.uniform(1.0, 2.5, size=rows)).round(2),
            "term_months": rng.integers(6, 72, size=rows, dtype=np.int64),
            "payment_frequency": rng.choice(payment_freqs, p=payment_probs, size=rows),
        }
    )


def _load_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def run_profile(df: pd.DataFrame, top_n: int) -> dict[str, Any]:
    """Run KPI calculation under cProfile and return summary."""
    profiler = cProfile.Profile()
    phase = CalculationPhase(config={}, kpi_definitions=load_kpi_definitions())

    profiler.enable()
    started = time.perf_counter()
    result = phase.execute(df=df, run_dir=None)
    duration = time.perf_counter() - started
    profiler.disable()

    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats("cumtime").print_stats(top_n)

    return {
        "duration_seconds": round(duration, 6),
        "status": result.get("status", "unknown"),
        "kpi_count": result.get("kpi_count", 0),
        "top_functions": stream.getvalue(),
        "profiler": profiler,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Optional CSV/Parquet input file.")
    parser.add_argument("--rows", type=int, default=1_000_000, help="Synthetic rows when no input.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for synthetic data generation.")
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Number of top cProfile functions to print by cumulative time.",
    )
    parser.add_argument(
        "--profile-out",
        type=Path,
        default=Path("logs/performance/kpi_engine_profile.stats"),
        help="Path to write raw cProfile stats.",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("logs/performance/kpi_engine_profile_summary.json"),
        help="Path to write JSON summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.input:
        df = _load_input(args.input)
        source = str(args.input)
    else:
        df = _build_synthetic_loans(args.rows, args.seed)
        source = f"synthetic:{args.rows}"

    profile_result = run_profile(df, args.top_n)
    profiler = profile_result.pop("profiler")

    args.profile_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)

    profiler.dump_stats(str(args.profile_out))

    summary = {
        "source": source,
        "rows": int(len(df)),
        "duration_seconds": profile_result["duration_seconds"],
        "status": profile_result["status"],
        "kpi_count": profile_result["kpi_count"],
        "profile_stats_path": str(args.profile_out),
        "top_functions": profile_result["top_functions"],
    }

    args.summary_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "top_functions"}, indent=2))
    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
