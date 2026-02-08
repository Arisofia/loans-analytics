#!/usr/bin/env python3
"""
KPI & Agent Accuracy Validation
Cross-checks pipeline KPI output against manual pandas calculations on raw data.
Then tests multi-agent system with real KPI context.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

LABEL_PASS = "\033[92mPASS\033[0m"
LABEL_FAIL = "\033[91mFAIL\033[0m"
LABEL_WARN = "\033[93mWARN\033[0m"

results = []
warnings = []  # Track warnings separately from failures


def check(name, ok, detail=""):
    status = LABEL_PASS if ok else LABEL_FAIL
    results.append((name, ok))
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def check_warn(name, ok, detail=""):
    """Record a non-blocking check: WARNs do not affect the exit code."""
    status = LABEL_PASS if ok else LABEL_WARN
    warnings.append((name, ok))  # Track separately from results
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def close_enough(a, b, tol=0.01):
    """Check if two values are within tolerance (1%)."""
    if a == 0 and b == 0:
        return True
    if a == 0 or b == 0:
        return abs(a - b) < 1.0
    return abs(a - b) / max(abs(a), abs(b)) < tol


def find_latest_run_id(runs_dir: Path) -> str | None:
    if not runs_dir.exists():
        return None
    runs = [p for p in runs_dir.iterdir() if p.is_dir()]
    if not runs:
        return None
    return sorted(runs, key=lambda p: p.name, reverse=True)[0].name


def main():
    print("=" * 70)
    print("  KPI ACCURACY VALIDATION — Cross-check vs Raw Data")
    print("=" * 70)

    parser = argparse.ArgumentParser(description="Validate pipeline KPI accuracy")
    parser.add_argument("--run-id", type=str, default=None, help="Pipeline run ID to validate")
    args = parser.parse_args()

    run_id = args.run_id or os.environ.get("KPI_VALIDATION_RUN_ID")
    if not run_id:
        run_id = find_latest_run_id(Path("logs/runs"))
        if run_id:
            print(f"  No run ID provided; using latest run: {run_id}")

    if not run_id:
        print("  No pipeline run found. Run the pipeline to generate logs/runs/<run_id>.")
        return 1

    # Load pipeline KPI output
    kpi_file = Path("logs/runs") / run_id / "kpis_output.json"
    if not kpi_file.exists():
        print(f"  KPI output not found: {kpi_file}")
        return 1
    with open(kpi_file) as f:
        pipeline_kpis = json.load(f)

    print(f"\n  Pipeline KPIs loaded: {len(pipeline_kpis)} metrics")
    for k, v in pipeline_kpis.items():
        print(f"    {k:35s} = {v}")

    # Load and prepare data - use pipeline's CLEAN (transformed) data
    # This validates the KPI calculation formulas against the same clean data
    # the pipeline uses (post-transformation), not the raw CSV
    print("\n" + "=" * 70)
    print("  MANUAL RECALCULATION FROM PIPELINE CLEAN DATA")
    print("=" * 70)

    clean_path = Path("logs/runs") / run_id / "clean_data.parquet"
    if clean_path.exists():
        df = pd.read_parquet(clean_path)
        print(f"\n  Clean data (parquet): {len(df)} rows, {len(df.columns)} columns")
    else:
        raw_candidates = sorted(Path("data/raw").glob("abaco_real_data_*.csv"))
        if not raw_candidates:
            print("  No real data CSV found in data/raw (abaco_real_data_*.csv)")
            return 1
        raw_path = raw_candidates[-1]
        df = pd.read_csv(raw_path)
        print(f"\n  Fallback to raw CSV: {raw_path} ({len(df)} rows, {len(df.columns)} columns)")

    # Apply transforms only when using raw CSV fallback
    needs_transform = not clean_path.exists()

    if needs_transform:
        # Apply same transformations as Phase 2
        # 1. Normalize status
        status_map = {
            "Current": "active",
            "Complete": "closed",
            "Default": "defaulted",
            "Active": "active",
            "Closed": "closed",
            "Defaulted": "defaulted",
        }

        if "current_status" in df.columns:
            df["status"] = (
                df["current_status"].map(status_map).fillna(df["current_status"].str.lower())
            )
        elif "status" in df.columns:
            df["status"] = df["status"].map(status_map).fillna(df["status"].str.lower())

        # 2. Rename columns to match pipeline schema
        if "days_past_due" in df.columns:
            df["dpd"] = pd.to_numeric(df["days_past_due"], errors="coerce").fillna(0).astype(int)

        # Ensure numeric columns
        for col in [
            "outstanding_balance",
            "principal_amount",
            "interest_rate",
            "last_payment_amount",
            "total_scheduled",
            "current_balance",
            "tpv",
            "term_months",
            "collateral_value",
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 3. Normalize interest rate (monthly % → annual decimal, same as transformation.py)
        if "interest_rate" in df.columns:
            median_rate = df["interest_rate"].median()
            median_term = df["term_months"].median() if "term_months" in df.columns else 12
            if median_rate < 5 and median_term < 6:
                df["interest_rate"] = df["interest_rate"] * 12 / 100

        # 5. Zero out current_balance for closed loans (same as pipeline Phase 2)
        if "current_balance" in df.columns:
            df.loc[df["status"] == "closed", "current_balance"] = 0

    # Add loan_count for repeat borrower calculation (always needed)
    if "borrower_id" in df.columns and "loan_id" in df.columns:
        loan_counts = df.groupby("borrower_id")["loan_id"].nunique().rename("loan_count")
        if "loan_count" not in df.columns:
            df = df.merge(loan_counts, on="borrower_id", how="left")

    # Zero out current_balance for closed loans if using clean data (already done by pipeline)
    if "current_balance" in df.columns and not needs_transform:
        # Clean data may already have this; ensure consistency
        pass

    print(f"  After transforms: {len(df)} rows")
    if "status" in df.columns:
        print(f"  Status distribution: {df['status'].value_counts().to_dict()}")
    else:
        check_warn("status column present", False, "missing; KPI checks may be incomplete")
    if "dpd" in df.columns:
        print(f"  DPD range: {df['dpd'].min()} - {df['dpd'].max()}")
    else:
        check_warn("dpd column present", False, "missing; PAR checks may be incomplete")

    # ==========================================
    # MANUAL KPI CALCULATIONS
    # ==========================================
    print("\n" + "=" * 70)
    print("  KPI-BY-KPI CROSS-VALIDATION")
    print("=" * 70)

    if "status" not in df.columns:
        print("  Required 'status' column missing. Cannot validate KPIs.")
        return 1

    active_mask = df["status"].isin(["active", "defaulted"])
    not_closed = df["status"] != "closed"

    # 1. total_outstanding_balance
    manual = df.loc[active_mask, "outstanding_balance"].sum()
    pipeline = pipeline_kpis["total_outstanding_balance"]
    check(
        "total_outstanding_balance",
        close_enough(manual, pipeline),
        f"manual={manual:,.2f} vs pipeline={pipeline:,.2f}",
    )

    # 2. total_loans_count
    manual = df.loc[not_closed, "loan_id"].nunique()
    pipeline = pipeline_kpis["total_loans_count"]
    check(
        "total_loans_count",
        close_enough(manual, pipeline),
        f"manual={manual} vs pipeline={pipeline}",
    )

    # 3. average_loan_size
    manual = df["principal_amount"].mean()
    pipeline = pipeline_kpis["average_loan_size"]
    check(
        "average_loan_size",
        close_enough(manual, pipeline),
        f"manual={manual:,.2f} vs pipeline={pipeline:,.2f}",
    )

    # 4. portfolio_yield
    manual = df["interest_rate"].mean() * 100
    pipeline = pipeline_kpis["portfolio_yield"]
    check(
        "portfolio_yield",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 5. par_30
    dpd30_balance = df.loc[df["dpd"] >= 30, "outstanding_balance"].sum()
    total_balance = df["outstanding_balance"].sum()
    manual = (dpd30_balance / total_balance * 100) if total_balance > 0 else 0
    pipeline = pipeline_kpis["par_30"]
    check(
        "par_30",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 6. par_90
    dpd90_balance = df.loc[df["dpd"] >= 90, "outstanding_balance"].sum()
    manual = (dpd90_balance / total_balance * 100) if total_balance > 0 else 0
    pipeline = pipeline_kpis["par_90"]
    check(
        "par_90",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 7. default_rate
    default_count = df.loc[df["status"] == "defaulted", "loan_id"].count()
    total_count = df["loan_id"].count()
    manual = (default_count / total_count * 100) if total_count > 0 else 0
    pipeline = pipeline_kpis["default_rate"]
    check(
        "default_rate",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 8. loss_rate
    default_balance = df.loc[df["status"] == "defaulted", "outstanding_balance"].sum()
    total_principal = df["principal_amount"].sum()
    manual = (default_balance / total_principal * 100) if total_principal > 0 else 0
    pipeline = pipeline_kpis["loss_rate"]
    check(
        "loss_rate",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 9. collections_rate
    total_payments = df["last_payment_amount"].sum()
    total_scheduled = df["total_scheduled"].sum()
    manual = (total_payments / total_scheduled * 100) if total_scheduled > 0 else 0
    pipeline = pipeline_kpis["collections_rate"]
    check(
        "collections_rate",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 10. recovery_rate
    default_payments = df.loc[df["status"] == "defaulted", "last_payment_amount"].sum()
    default_outstanding = df.loc[df["status"] == "defaulted", "outstanding_balance"].sum()
    manual = (default_payments / default_outstanding * 100) if default_outstanding > 0 else 0
    pipeline = pipeline_kpis["recovery_rate"]
    check(
        "recovery_rate",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 11. cash_on_hand
    manual = df["current_balance"].sum()
    pipeline = pipeline_kpis["cash_on_hand"]
    check(
        "cash_on_hand",
        close_enough(manual, pipeline),
        f"manual={manual:,.2f} vs pipeline={pipeline:,.2f}",
    )

    # 12. active_borrowers
    manual = df.loc[active_mask, "borrower_id"].nunique()
    pipeline = pipeline_kpis["active_borrowers"]
    check(
        "active_borrowers",
        close_enough(manual, pipeline),
        f"manual={manual} vs pipeline={pipeline}",
    )

    # 13. repeat_borrower_rate
    repeat = df.loc[df["loan_count"] > 1, "borrower_id"].nunique()
    total_borrowers = df["borrower_id"].nunique()
    manual = (repeat / total_borrowers * 100) if total_borrowers > 0 else 0
    pipeline = pipeline_kpis["repeat_borrower_rate"]
    check(
        "repeat_borrower_rate",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # 14. customer_lifetime_value
    total_tpv = df["tpv"].sum()
    unique_borrowers = df["borrower_id"].nunique()
    manual = total_tpv / unique_borrowers if unique_borrowers > 0 else 0
    pipeline = pipeline_kpis["customer_lifetime_value"]
    check(
        "customer_lifetime_value",
        close_enough(manual, pipeline),
        f"manual={manual:,.2f} vs pipeline={pipeline:,.2f}",
    )

    # 15. processing_time_avg
    manual = df["term_months"].mean()
    pipeline = pipeline_kpis["processing_time_avg"]
    check(
        "processing_time_avg",
        close_enough(manual, pipeline),
        f"manual={manual:.2f} vs pipeline={pipeline:.2f}",
    )

    # 16-17. Growth KPIs (month-to-date = 0 since data is from Feb 2)
    check(
        "disbursement_volume_mtd",
        pipeline_kpis["disbursement_volume_mtd"] == 0.0,
        f"pipeline={pipeline_kpis['disbursement_volume_mtd']} (expected 0 — data from prior month)",
    )
    check(
        "new_loans_count_mtd",
        pipeline_kpis["new_loans_count_mtd"] == 0.0,
        f"pipeline={pipeline_kpis['new_loans_count_mtd']} (expected 0)",
    )

    # 18. portfolio_growth_rate (comparison formula, returns 0 by design)
    check(
        "portfolio_growth_rate",
        pipeline_kpis["portfolio_growth_rate"] == 0.0,
        f"pipeline={pipeline_kpis['portfolio_growth_rate']} (comparison formula → 0)",
    )

    # 19. automation_rate
    if "payment_frequency" in df.columns:
        bullet = df.loc[df["payment_frequency"] == "bullet", "loan_id"].count()
        total = df["loan_id"].count()
        manual = (bullet / total * 100) if total > 0 else 0
    else:
        manual = 0
    pipeline = pipeline_kpis["automation_rate"]
    check(
        "automation_rate",
        close_enough(manual, pipeline),
        f"manual={manual:.2f}% vs pipeline={pipeline:.2f}%",
    )

    # ==========================================
    # FINANCIAL SANITY CHECKS
    # ==========================================
    print("\n" + "=" * 70)
    print("  FINANCIAL SANITY CHECKS")
    print("=" * 70)

    check(
        "PAR-30 < 30%",
        pipeline_kpis["par_30"] < 30,
        f"{pipeline_kpis['par_30']:.2f}% (guardrail: <30%)",
    )
    check(
        "PAR-90 < 15%",
        pipeline_kpis["par_90"] < 15,
        f"{pipeline_kpis['par_90']:.2f}% (guardrail: <15%)",
    )
    check(
        "Default rate < 10%",
        pipeline_kpis["default_rate"] < 10,
        f"{pipeline_kpis['default_rate']:.2f}% (guardrail: <10%)",
    )
    check(
        "Portfolio yield 5-15%",
        5 <= pipeline_kpis["portfolio_yield"] <= 15,
        f"{pipeline_kpis['portfolio_yield']:.2f}% (range: 5-15%)",
    )
    check(
        "Collections rate > 50%",
        pipeline_kpis["collections_rate"] > 50,
        f"{pipeline_kpis['collections_rate']:.2f}% (min: 50%)",
    )
    check(
        "AUM > $1M",
        pipeline_kpis["total_outstanding_balance"] > 1_000_000,
        f"${pipeline_kpis['total_outstanding_balance']:,.2f}",
    )
    check(
        "Active borrowers > 10",
        pipeline_kpis["active_borrowers"] > 10,
        f"{pipeline_kpis['active_borrowers']:.0f} borrowers",
    )

    # ==========================================
    # SUMMARY
    # ==========================================
<<<<<<< HEAD
<<<<<<< HEAD
    passed_results = sum(1 for _, ok in results if ok)
    failed_results = sum(1 for _, ok in results if not ok)
    passed_warnings = sum(1 for _, ok in warnings if ok)
    failed_warnings = sum(1 for _, ok in warnings if not ok)
    total_passed = passed_results + passed_warnings
    total_failed = failed_results  # Only blocking failures count toward exit code
    total_checks = len(results) + len(warnings)
||||||| parent of a31a90ae8 (Fix warning tracking - separate warnings from failures)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
=======
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    warned = sum(1 for _, ok in warnings if not ok)
||||||| parent of df8044b1a (fix: resolve merge conflict in validate_kpi_accuracy.py (check_warn) and clean up conflict markers)
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    warned = sum(1 for _, ok in warnings if not ok)
=======
    passed_results = sum(1 for _, ok in results if ok)
    failed_results = sum(1 for _, ok in results if not ok)
    passed_warnings = sum(1 for _, ok in warnings if ok)
    failed_warnings = sum(1 for _, ok in warnings if not ok)
    total_passed = passed_results + passed_warnings
    total_failed = failed_results  # Only blocking failures count toward exit code
>>>>>>> df8044b1a (fix: resolve merge conflict in validate_kpi_accuracy.py (check_warn) and clean up conflict markers)
    total_checks = len(results) + len(warnings)
>>>>>>> a31a90ae8 (Fix warning tracking - separate warnings from failures)
    print("\n" + "=" * 70)
<<<<<<< HEAD
<<<<<<< HEAD
    print(
        f"  KPI VALIDATION: {total_passed} passed ({passed_results} required, {passed_warnings} optional), "
        f"{total_failed} failed (blocking), {failed_warnings} failed (optional), {total_checks} total"
    )
    if total_failed == 0:
||||||| parent of a31a90ae8 (Fix warning tracking - separate warnings from failures)
    print(f"  KPI VALIDATION: {passed} passed, {failed} failed, {len(results)} total")
    if failed == 0:
=======
    print(f"  KPI VALIDATION: {passed} passed, {failed} failed, {warned} warned, {total_checks} total")
<<<<<<< HEAD
    if failed == 0:
>>>>>>> a31a90ae8 (Fix warning tracking - separate warnings from failures)
||||||| parent of 6ddf3817e (Update scripts/validate_kpi_accuracy.py)
    if failed == 0:
=======
    if failed == 0 and warned == 0:
        # All blocking checks passed and there are no warnings.
>>>>>>> 6ddf3817e (Update scripts/validate_kpi_accuracy.py)
||||||| parent of df8044b1a (fix: resolve merge conflict in validate_kpi_accuracy.py (check_warn) and clean up conflict markers)
    print(f"  KPI VALIDATION: {passed} passed, {failed} failed, {warned} warned, {total_checks} total")
    if failed == 0 and warned == 0:
        # All blocking checks passed and there are no warnings.
=======
    print(
        f"  KPI VALIDATION: {total_passed} passed ({passed_results} required, {passed_warnings} optional), "
        f"{total_failed} failed (blocking), {failed_warnings} failed (optional), {total_checks} total"
    )
    if total_failed == 0:
>>>>>>> df8044b1a (fix: resolve merge conflict in validate_kpi_accuracy.py (check_warn) and clean up conflict markers)
        print(f"  [{LABEL_PASS}] ALL KPIs PRODUCE ACCURATE REAL DATA")
    else:
        print(f"  [{LABEL_FAIL}] {total_failed} KPI(S) HAVE DISCREPANCIES:")
        for name, ok in results:
            if not ok:
                print(f"    - {name}")
    if failed_warnings > 0:
        print(f"  [{LABEL_WARN}] {failed_warnings} WARNING(S) (non-blocking)")
    print("=" * 70)
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
