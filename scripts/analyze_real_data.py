#!/usr/bin/env python3
"""Quick analysis of real Abaco data files."""

import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Analyze real Abaco data files")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / "Downloads",
        help="Directory containing source CSV files (default: ~/Downloads)",
    )
    args = parser.parse_args()

    # Define files
    FILES = {
        "loan_data": args.data_dir / "Abaco - Loan Tape_Loan Data_Table (3).csv",
        "customer": args.data_dir / "Abaco - Loan Tape_Customer Data_Table (3).csv",
        "collateral": args.data_dir / "Abaco - Loan Tape_Collateral_Table (3).csv",
        "payment_schedule": args.data_dir
        / "Abaco - Loan Tape_Payment Schedule_Table (3).csv",
        "historic_payments": args.data_dir
        / "Abaco - Loan Tape_Historic Real Payment_Table (3).csv",
    }

    print("=" * 70)
    print("📊 ABACO REAL DATA ANALYSIS")
    print("=" * 70)

    for name, filepath in FILES.items():
        try:
            # Read full file
            df = pd.read_csv(filepath)
            print(f"\n📄 {name.upper()}: {filepath.name}")
            print(f"   Rows: {len(df):,}")
            print(f"   Columns ({len(df.columns)}): {', '.join(df.columns)}")

            # Show sample
            print("\n   First row sample:")
            for col in df.columns[:5]:
                print(f"     {col}: {df[col].iloc[0]}")
            if len(df.columns) > 5:
                print(f"     ... ({len(df.columns) - 5} more columns)")

        except FileNotFoundError:
            print(f"\n❌ {name}: File not found - {filepath}")
        except Exception as e:
            print(f"\n❌ {name}: Error - {e}")

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("\nNext steps:")
    print("  1. Merge tables using scripts/data/prepare_real_data.py")
    print("  2. Run pipeline on merged data")


if __name__ == "__main__":
    main()
