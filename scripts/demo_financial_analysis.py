#!/usr/bin/env python3
"""
Demonstration script for the FinancialAnalyzer class.
This script generates sample loan data and applies segmentation,
DPD bucketing, and weighted statistic calculations.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

plt: Any

try:
    import matplotlib
    # Use non-interactive backend for scripts/tests to avoid GUI/display-related errors
    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt
    plt = _plt
    HAS_MATPLOTLIB = True
except Exception:
    # Matplotlib may not be installed in lightweight CI/test environments.
    # Provide a minimal stub that exposes the attributes used by this script so tests can patch `plt`.
    HAS_MATPLOTLIB = False
    class _StubPlt:
        def figure(self, *args, **kwargs):
            return None
        def title(self, *args, **kwargs):
            pass
        def xlabel(self, *args, **kwargs):
            pass
        def ylabel(self, *args, **kwargs):
            pass
        def xticks(self, *args, **kwargs):
            pass
        def tight_layout(self, *args, **kwargs):
            pass
        def savefig(self, *args, **kwargs):
            pass
    plt = _StubPlt()

import pandas as pd

# Project import moved into main() to avoid heavy imports during pytest collection.
# (Importing src modules at import-time can cause side-effects like telemetry threads.)
# No sys.path manipulation at module import time.
# (FinancialAnalyzer will be imported inside main.)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_sample_data():
    today = datetime.now().date()
    data = {
        "loan_id": [101, 102, 103, 104, 105],
        "customer_id": ["C1", "C2", "C1", "C3", "C2"],
        "outstanding_balance": [5000.0, 15000.0, 200.0, 50000.0, 12000.0],
        "line_amount": [10000.0, 20000.0, 5000.0, 50000.0, 15000.0],
        "days_past_due": [0, 45, 5, 120, 0],
        "apr": [0.12, 0.15, 0.18, 0.10, 0.14],
        "loan_count": [2, 5, 2, 1, 5],
        "last_active_date": [today, today, today, today - timedelta(days=100), today],
    }
    return pd.DataFrame(data)


def main():
    parser = argparse.ArgumentParser(description="Run Financial Analysis Demo")
    parser.add_argument("--data", type=str, help="Path to CSV file with loan data")
    args = parser.parse_args()

    print("--- ABACO Financial Analysis Demo ---\n")

    df = None
    if args.data:
        path = Path(args.data)
        if path.exists():
            print(f"Loading real data from {path}...")
            try:
                df = pd.read_csv(path)
                print(f"Loaded {len(df)} loans.")
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                sys.exit(1)
        else:
            logger.error(f"File not found: {path}")
            sys.exit(1)
    else:
        print("No data file provided. Generating sample data...")
        df = generate_sample_data()
        print(f"Generated {len(df)} sample loans.")

    # Import here to avoid import-time side-effects during pytest collection.
    from src.analytics.financial_analysis import FinancialAnalyzer

    analyzer = FinancialAnalyzer()

    # 2. Enrich Data (Buckets, Segments, Utilization)
    print("\n[1] Enriching Master Dataframe...")
    enriched_df = analyzer.enrich_master_dataframe(df)

    # Select columns to show that actually exist (handling both sample and real data schemas)
    cols_to_show = [
        c
        for c in ["loan_id", "dpd_bucket", "exposure_segment", "line_utilization", "client_type"]
        if c in enriched_df.columns
    ]
    if cols_to_show:
        print(enriched_df[cols_to_show].head(10).to_string(index=False))

    # 3. Calculate Weighted Stats
    print("\n[2] Calculating Weighted APR by Balance...")
    weighted_stats = analyzer.calculate_weighted_stats(enriched_df, metrics=["apr"])
    if not weighted_stats.empty:
        print(weighted_stats.to_string(index=False))
    else:
        print("Could not calculate weighted stats (missing columns?)")

    # 4. Calculate Concentration Risk (HHI)
    print("\n[3] Calculating Portfolio Concentration (HHI)...")
    hhi = analyzer.calculate_hhi(enriched_df)
    print(f"HHI Score: {hhi:.2f} (Scale 0-10,000)")

    # 5. Visualization
    if HAS_MATPLOTLIB and "dpd_bucket" in enriched_df.columns:
        print("\n[4] Generating DPD Distribution Chart...")
        counts = enriched_df["dpd_bucket"].value_counts()
        order = ["Current", "1-29", "30-59", "60-89", "90-119", "120-149", "150-179", "180+"]
        counts = counts.reindex(order).fillna(0)

        # Ensure non-interactive backend is enforced immediately before plotting.
        if HAS_MATPLOTLIB:
            matplotlib.use("Agg")

        # Temporarily remove IPython from sys.modules to avoid a matplotlib bug
        # where it references a misspelled variable when IPython is present.
        saved_ipy = sys.modules.pop("IPython", None)
        try:
            plt.figure(figsize=(10, 6))
            counts.plot(kind="bar", color="skyblue", edgecolor="black")
            plt.title("Loan Portfolio DPD Distribution")
            plt.xlabel("DPD Bucket")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            plt.tight_layout()
            output_img = "dpd_distribution.png"
            plt.savefig(output_img)
            print(f"Saved {output_img}")
        finally:
            if saved_ipy is not None:
                sys.modules["IPython"] = saved_ipy

    if HAS_MATPLOTLIB and "exposure_segment" in enriched_df.columns:
        print("\n[5] Generating Exposure Segment Chart...")
        counts = enriched_df["exposure_segment"].value_counts()

        # Ensure non-interactive backend is enforced immediately before plotting.
        if HAS_MATPLOTLIB:
            matplotlib.use("Agg")

        # Temporarily remove IPython from sys.modules to avoid a matplotlib bug
        # where it references a misspelled variable when IPython is present.
        saved_ipy = sys.modules.pop("IPython", None)
        try:
            plt.figure(figsize=(10, 6))
            counts.plot(kind="bar", color="lightgreen", edgecolor="black")
            plt.title("Client Exposure Segments")
            plt.xlabel("Segment")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            plt.tight_layout()
            output_img = "exposure_distribution.png"
            plt.savefig(output_img)
            print(f"Saved {output_img}")
        finally:
            if saved_ipy is not None:
                sys.modules["IPython"] = saved_ipy


if __name__ == "__main__":
    main()
