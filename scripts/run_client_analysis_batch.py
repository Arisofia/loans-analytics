#!/usr/bin/env python3
from __future__ import annotations

# Standard Library Imports
import argparse
import json
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

# Third-Party Imports
import pandas as pd
import requests

# Optional: Azure Application Insights tracing
try:
    from src.azure_tracing import setup_azure_tracing, trace_analytics_job

    AZURE_TRACING_ENABLED = True
except ImportError:
    AZURE_TRACING_ENABLED = False

    def trace_analytics_job(job_name: str, client_id: str, run_id: str):
        def decorator(func):
            return func

        return decorator


# -----------------
# Logging
# -----------------


def _setup_logger(level: str) -> logging.Logger:
    logger = logging.getLogger("client_analysis_batch")
    if logger.handlers:
        return logger

    # Add Azure Application Insights handler if enabled
    if AZURE_TRACING_ENABLED:
        try:
            setup_azure_tracing()
        except Exception as e:
            print(f"[WARN] Azure tracing setup failed: {e}")

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(h)
    return logger


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


SUPABASE_URL = _env("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
if not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_ANON_KEY " "(or NEXT_PUBLIC_SUPABASE_ANON_KEY).")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _rest_get(
    relation: str,
    select: str = "*",
    where: Optional[dict[str, Any]] = None,
    limit: int = 50000,
) -> pd.DataFrame:
    url = f"{SUPABASE_URL}/rest/v1/{relation}"
    params: dict[str, str | int] = {"select": select, "limit": limit}
    if where:
        for k, v in where.items():
            params[k] = f"eq.{v}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=60)
    if r.status_code >= 300:
        raise RuntimeError(f"GET {relation} failed {r.status_code}: {r.text[:500]}")
    return pd.DataFrame(r.json() or [])


def _rest_upsert(
    relation: str,
    payload: list[dict[str, Any]],
    on_conflict: Optional[str] = None,
) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{relation}"
    headers = dict(HEADERS)
    headers["Prefer"] = "resolution=merge-duplicates"
    params = {}
    if on_conflict:
        params["on_conflict"] = on_conflict
    r = requests.post(
        url,
        headers=headers,
        params=params,
        json=payload,
        timeout=60,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"UPSERT {relation} failed {r.status_code}: {r.text[:500]}")


# -----------------
# Analytics
# -----------------


def safe_div(n: float, d: float) -> float:
    return float(n) / float(d) if d and d != 0 else float("nan")


def compute_client_metrics(
    loans: pd.DataFrame,
    client_id: str,
) -> dict[str, Any]:
    df = loans.copy()
    df["customer_id"] = df["customer_id"].astype(str)
    c = df[df["customer_id"] == str(client_id)].copy()
    if c.empty:
        raise ValueError(f"No rows for client_id={client_id}")

    total_outstanding = pd.to_numeric(df["outstanding_balance"], errors="coerce").sum(skipna=True)
    c_outstanding = pd.to_numeric(c["outstanding_balance"], errors="coerce").sum(skipna=True)

    dpd = pd.to_numeric(c["dpd"], errors="coerce")
    bal = pd.to_numeric(c["outstanding_balance"], errors="coerce")

    par90_bal = bal.where(dpd >= 90, 0).sum(skipna=True)
    par30_bal = bal.where(dpd >= 30, 0).sum(skipna=True)

    return {
        "client_id": str(client_id),
        "total_disbursed": float(
            pd.to_numeric(c["disbursement_amount"], errors="coerce").sum(skipna=True)
        ),
        "outstanding_balance": float(c_outstanding),
        "share_portfolio_outstanding": safe_div(c_outstanding, total_outstanding),
        "par30_balance_pct": safe_div(par30_bal, c_outstanding),
        "par90_balance_pct": safe_div(par90_bal, c_outstanding),
        "max_dpd": float(dpd.max(skipna=True)),
        "mean_dpd": float(dpd.mean(skipna=True)),
    }


@dataclass
class RunResult:
    client_id: str
    status: str
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


def _execute_one(client_id: str, loans_view: str, run_id: str) -> RunResult:
    t0 = time.time()

    @trace_analytics_job("client_metrics", str(client_id), run_id)
    def _run() -> RunResult:
        try:
            select_fields = "customer_id,disbursement_amount,outstanding_balance,dpd"
            loans = _rest_get(
                loans_view,
                select=select_fields,
                limit=250000,
            )
            metrics = compute_client_metrics(loans, client_id)

            row = {
                "run_id": run_id,
                "client_id": metrics["client_id"],
                "metrics_json": metrics,
                "computed_at_utc": datetime.utcnow().isoformat(),
            }
            _rest_upsert(
                "analytics.client_metrics",
                [row],
                on_conflict="run_id,client_id",
            )

            return RunResult(
                client_id=client_id,
                status="success",
                duration_seconds=round(time.time() - t0, 2),
            )
        except Exception as e:
            return RunResult(
                client_id=client_id,
                status="failed",
                error=f"{type(e).__name__}: {e}",
                duration_seconds=round(time.time() - t0, 2),
            )

    return _run()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--loans-view",
        default=os.getenv("LOANS_VIEW", "v_loan_portfolio_daily"),
    )
    ap.add_argument(
        "--clients-view",
        default=os.getenv("CLIENTS_VIEW", "v_clients"),
    )
    ap.add_argument("--client-id-col", default="customer_id")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sample", type=int, default=25)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = ap.parse_args()

    logger = _setup_logger(args.log_level)
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Record run header in DB
    _rest_upsert(
        "analytics.batch_runs",
        [
            {
                "run_id": run_id,
                "started_at_utc": datetime.utcnow().isoformat(),
                "loans_view": args.loans_view,
                "workers": args.workers,
            }
        ],
        on_conflict="run_id",
    )

    clients_df = _rest_get(args.clients_view, select=args.client_id_col, limit=200000)
    client_ids = clients_df[args.client_id_col].dropna().astype(str).unique().tolist()
    if not client_ids:
        raise RuntimeError("No clients returned from clients_view.")

    if not args.all:
        client_ids = (
            pd.Series(client_ids)
            .sample(
                n=min(args.sample, len(client_ids)),
                random_state=args.seed,
            )
            .tolist()
        )

    logger.info(
        "run_id=%s | clients=%d | workers=%d",
        run_id,
        len(client_ids),
        args.workers,
    )

    results: list[RunResult] = []
    if args.workers <= 1:
        for cid in client_ids:
            rr = _execute_one(cid, args.loans_view, run_id)
            results.append(rr)
            if rr.status != "success":
                logger.error("FAILED client=%s: %s", cid, rr.error)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(_execute_one, cid, args.loans_view, run_id) for cid in client_ids]
            for fut in as_completed(futs):
                rr = fut.result()
                results.append(rr)
                if rr.status != "success":
                    logger.error(
                        "FAILED client=%s: %s",
                        rr.client_id,
                        rr.error,
                    )

    # Finalize run row in DB
    failures = [r for r in results if r.status != "success"]
    sorted_results = sorted(results, key=lambda x: x.client_id)
    _rest_upsert(
        "analytics.batch_runs",
        [
            {
                "run_id": run_id,
                "finished_at_utc": datetime.utcnow().isoformat(),
                "total_clients": len(results),
                "failed_clients": len(failures),
                "status": "failed" if failures else "success",
                "results_json": [asdict(r) for r in sorted_results],
            }
        ],
        on_conflict="run_id",
    )

    # Emit summary to stdout for CI
    print(
        json.dumps(
            {
                "run_id": run_id,
                "total_clients": len(results),
                "failed_clients": len(failures),
                "status": "failed" if failures else "success",
                "results": [asdict(r) for r in sorted_results],
            },
            indent=2,
        )
    )

    if failures:
        raise SystemExit(2)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
