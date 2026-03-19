#!/usr/bin/env python3
"""Unified portfolio analysis across loan tape and Control de Mora (INTERMEDIA)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def compute_dpd_loan_tape(row: pd.Series, reference_date: pd.Timestamp) -> int:
    """Approximate DPD for loan tape rows when explicit DPD is unavailable."""
    disb = pd.to_datetime(row.get("disbursement_date"), errors="coerce")
    # One-line fix: loans not yet disbursed at reference date must have dpd=0.
    if pd.notna(disb) and disb > reference_date:
        return 0

    explicit_dpd = pd.to_numeric(row.get("Days in Default"), errors="coerce")
    if pd.notna(explicit_dpd):
        return int(max(float(explicit_dpd), 0))

    term = pd.to_numeric(row.get("Term"), errors="coerce")
    term_unit = str(row.get("Term Unit", "")).strip().lower()
    if pd.isna(disb) or pd.isna(term):
        return 0

    if term_unit.startswith("day"):
        due = disb + pd.Timedelta(days=int(term))
    else:
        due = disb + pd.DateOffset(months=int(term))

    return int(max((reference_date - due).days, 0))


def monthly_from_loan_tape(raw_loan_data: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    df = raw_loan_data.copy()
    df["Disbursement Date"] = pd.to_datetime(df.get("Disbursement Date"), errors="coerce")
    df["month"] = df["Disbursement Date"].dt.to_period("M").dt.to_timestamp("M")
    df = df[df["month"].notna()]
    df = df[df["month"] <= cutoff]

    df["Disbursement Amount"] = pd.to_numeric(df.get("Disbursement Amount"), errors="coerce").fillna(0.0)
    df["Outstanding Loan Value"] = pd.to_numeric(df.get("Outstanding Loan Value"), errors="coerce").fillna(0.0)
    df["dpd"] = df.apply(lambda r: compute_dpd_loan_tape(r, cutoff), axis=1)

    out = (
        df.groupby("month", as_index=False)
        .agg(
            source=("Loan ID", lambda _: "loan_tape"),
            loans=("Loan ID", "nunique"),
            disbursed_amount=("Disbursement Amount", "sum"),
            outstanding_amount=("Outstanding Loan Value", "sum"),
            avg_dpd=("dpd", "mean"),
        )
        .sort_values("month")
    )
    return out


def monthly_from_control_mora(dim_loan: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    required_cols = {"snapshot_month", "loan_id", "principal_outstanding", "dpd"}
    if dim_loan.empty or not required_cols.issubset(set(dim_loan.columns)):
        return pd.DataFrame(columns=["month", "source", "loans", "disbursed_amount", "outstanding_amount", "avg_dpd"])

    df = dim_loan.copy()
    df["month"] = pd.to_datetime(df["snapshot_month"], errors="coerce").dt.to_period("M").dt.to_timestamp("M")
    df = df[df["month"].notna()]
    df = df[df["month"] > cutoff]

    df["principal_outstanding"] = pd.to_numeric(df["principal_outstanding"], errors="coerce").fillna(0.0)
    df["dpd"] = pd.to_numeric(df["dpd"], errors="coerce").fillna(0)

    out = (
        df.groupby("month", as_index=False)
        .agg(
            source=("loan_id", lambda _: "control_mora"),
            loans=("loan_id", "nunique"),
            disbursed_amount=("principal_outstanding", "sum"),
            outstanding_amount=("principal_outstanding", "sum"),
            avg_dpd=("dpd", "mean"),
        )
        .sort_values("month")
    )
    return out


def run(args: argparse.Namespace) -> None:
    from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
    from backend.src.zero_cost.pipeline_router import PipelineRouter

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cutoff = pd.Timestamp(args.cutoff)
    snapshot_month = pd.Timestamp(args.snapshot_month)

    loader = LoanTapeLoader(data_dir=data_dir)
    loader.load_all(data_dir)

    raw_loan_data_path = data_dir / "loan_data.csv"
    if not raw_loan_data_path.exists():
        raise FileNotFoundError(f"Required raw file not found: {raw_loan_data_path}")
    raw_loan_data = pd.read_csv(raw_loan_data_path, dtype=str, encoding="utf-8-sig", low_memory=False)

    router = PipelineRouter()
    control_tables = router.route(
        snapshot_month=snapshot_month,
        loan_tape_dir=data_dir,
        control_mora_path=args.control_mora_input,
    )

    # 1) monthly KPIs
    monthly_tape = monthly_from_loan_tape(raw_loan_data, cutoff)
    monthly_mora = monthly_from_control_mora(control_tables["dim_loan"], cutoff)
    monthly = pd.concat([monthly_tape, monthly_mora], ignore_index=True).sort_values("month")
    monthly.to_csv(output_dir / "kpis_monthly.csv", index=False)

    # 2) snapshot current by operation
    snapshot_cols = [
        "loan_id",
        "client_id",
        "client_name",
        "disbursement_date",
        "principal_outstanding",
        "dpd",
        "mora_bucket",
        "branch_code",
        "snapshot_month",
        "source",
    ]
    snapshot_current = control_tables["dim_loan"].copy()
    keep = [c for c in snapshot_cols if c in snapshot_current.columns]
    snapshot_current = snapshot_current[keep].sort_values("loan_id")
    snapshot_current.to_csv(output_dir / "kpis_snapshot_current.csv", index=False)

    # 3) KPIs by KAM (branch_code used as KAM code in INTERMEDIA mapping)
    if "branch_code" in snapshot_current.columns:
        snapshot_current = snapshot_current.copy()
        snapshot_current["branch_code"] = (
            snapshot_current["branch_code"].astype(str).str.strip().replace({"": "Sin KAM", "nan": "Sin KAM"})
        )
        by_kam = (
            snapshot_current.groupby("branch_code", dropna=False, as_index=False)
            .agg(
                loans=("loan_id", "nunique"),
                outstanding_amount=("principal_outstanding", "sum"),
                avg_dpd=("dpd", "mean"),
            )
            .rename(columns={"branch_code": "kam"})
            .sort_values("outstanding_amount", ascending=False)
        )
    else:
        by_kam = pd.DataFrame(columns=["kam", "loans", "outstanding_amount", "avg_dpd"])
    by_kam.to_csv(output_dir / "kpis_by_kam.csv", index=False)

    # 4) KPIs by industry from loan tape customer metadata
    customer_data = pd.read_csv(data_dir / "customer_data.csv", dtype=str, encoding="utf-8-sig", low_memory=False)
    industry_df = customer_data.copy()
    industry_df["Industry"] = industry_df.get("Industry", "Unknown").fillna("Unknown")
    industry_df["Loan ID"] = industry_df.get("Loan ID", "")

    loan_metrics = raw_loan_data[["Loan ID", "Outstanding Loan Value", "Days in Default"]].copy()
    loan_metrics["Outstanding Loan Value"] = pd.to_numeric(loan_metrics["Outstanding Loan Value"], errors="coerce").fillna(0.0)
    loan_metrics["Days in Default"] = pd.to_numeric(loan_metrics["Days in Default"], errors="coerce").fillna(0)

    merged = industry_df.merge(loan_metrics, on="Loan ID", how="left")
    by_industry = (
        merged.groupby("Industry", dropna=False, as_index=False)
        .agg(
            loans=("Loan ID", "nunique"),
            outstanding_amount=("Outstanding Loan Value", "sum"),
            avg_dpd=("Days in Default", "mean"),
        )
        .rename(columns={"Industry": "industry"})
        .sort_values("outstanding_amount", ascending=False)
    )
    by_industry.to_csv(output_dir / "kpis_by_industry.csv", index=False)

    print(f"Unified analysis complete. Outputs written to: {output_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run unified portfolio analysis Jan-2024 to present")
    parser.add_argument("--data-dir", default="data/raw", help="Directory with loan_tape CSV files")
    parser.add_argument("--output-dir", default="exports/unified", help="Directory for generated KPI exports")
    parser.add_argument(
        "--cutoff",
        default="2026-01-31",
        help="Last month-end for loan_tape monthly KPI inclusion (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--snapshot-month",
        default=pd.Timestamp.today().strftime("%Y-%m-%d"),
        help="Snapshot month to pull Control de Mora / INTERMEDIA data",
    )
    parser.add_argument(
        "--control-mora-input",
        default="gsheets://INTERMEDIA",
        help="Control de Mora source (CSV path or gsheets://INTERMEDIA)",
    )
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
