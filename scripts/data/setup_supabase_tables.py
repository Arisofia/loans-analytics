#!/usr/bin/env python3
"""
Setup Supabase tables for the Abaco Loans Analytics pipeline.

This script:

1. Loads Supabase credentials from environment.
2. Verifies that the `kpi_timeseries_daily` table exists and is accessible.
3. Provides clear, production-safe instructions to apply the SQL migration manually.

Usage:
    python scripts/data/setup_supabase_tables.py
    python scripts/data/setup_supabase_tables.py --verify-only
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from supabase import Client, create_client

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))


def load_environment() -> tuple[str, str]:
    """Load Supabase credentials from environment."""
    env_local = project_root / ".env.local"
    env_file = project_root / ".env"

    if env_local.exists():
        load_dotenv(env_local)
        print(f"Loaded environment from {env_local}")
    elif env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")

    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials. Please set:")
        print("  - SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)")
        print("  - SUPABASE_SERVICE_ROLE_KEY (service role key for DDL)")
        sys.exit(1)

    return supabase_url, supabase_key


def verify_table_structure(supabase: Client) -> bool:
    """Verify that kpi_timeseries_daily table exists and is accessible."""
    print("\nVerifying table structure for `kpi_timeseries_daily`...")

    try:
        supabase.table("kpi_timeseries_daily").select("*").limit(0).execute()
        print("Table `kpi_timeseries_daily` exists and is accessible.")
        return True
    except Exception as exc:
        print(f"Table verification failed: {exc}")
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Supabase tables for the Abaco Loans Analytics pipeline."
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify table structure; do not apply migrations.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Abaco Loans Analytics - Supabase Setup")
    print("=" * 60)

    supabase_url, supabase_key = load_environment()
    print(f"Supabase URL: {supabase_url}")

    supabase: Client = create_client(supabase_url, supabase_key)
    print("Connected to Supabase.")

    migration_file = project_root / "db" / "migrations" / "002_create_kpi_timeseries_daily.sql"

    if args.verify_only:
        success = verify_table_structure(supabase)
        sys.exit(0 if success else 1)

    print("\n" + "=" * 60)
    print("MANUAL MIGRATION REQUIRED")
    print("=" * 60)
    print("\nSupabase REST APIs do not support arbitrary SQL execution for DDL.")
    print("Please apply the migration manually using one of the following options:\n")
    print("Option A: Supabase Dashboard (SQL Editor)")
    print("  1. Open Supabase Dashboard → SQL Editor")
    print(f"  2. Open the file: {migration_file}")
    print("  3. Copy its contents into the SQL Editor")
    print("  4. Execute the SQL")
    print("\nOption B: Supabase CLI")
    print("  1. Install Supabase CLI if needed")
    print(f'  2. Run: supabase db execute -f "{migration_file}"')
    print("  3. Confirm the command exits successfully")

    print("\nAfter applying the migration, this script will verify the table:")

    print("\n" + "=" * 60)
    success = verify_table_structure(supabase)
    if not success:
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Supabase setup complete.")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Ensure your data pipeline is configured to write to `kpi_timeseries_daily`.")
    print("  2. Run: python scripts/data/run_data_pipeline.py")
    print("  3. Verify data in Supabase: table `kpi_timeseries_daily` contains records.")
    print("  4. Refresh your production dashboard and validate KPI time series.")


if __name__ == "__main__":
    main()
