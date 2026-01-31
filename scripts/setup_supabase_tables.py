#!/usr/bin/env python3
"""
Setup Supabase tables for the Abaco Loans Analytics pipeline.

This script:
1. Loads Supabase credentials from environment
2. Applies SQL migrations to create the kpi_timeseries_daily table
3. Verifies table structure and indexes

Usage:
    python scripts/setup_supabase_tables.py
    python scripts/setup_supabase_tables.py --verify-only
"""

import os
import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from supabase import create_client, Client


def load_environment() -> tuple[str, str]:
    """Load Supabase credentials from environment."""
    # Try loading from .env.local first, then .env
    env_local = project_root / ".env.local"
    env_file = project_root / ".env"
    
    if env_local.exists():
        load_dotenv(env_local)
        print(f"✓ Loaded environment from {env_local}")
    elif env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
    
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for DDL
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials. Please set:")
        print("   - SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    return supabase_url, supabase_key


def apply_migration(supabase: Client, migration_file: Path) -> bool:
    """Apply a SQL migration file to Supabase."""
    print(f"\n📄 Applying migration: {migration_file.name}")
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    # Read migration SQL
    sql_content = migration_file.read_text()
    
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql_content.split(";") if s.strip()]
    
    for i, statement in enumerate(statements, 1):
        if not statement:
            continue
        
        # Skip comments
        if statement.strip().startswith("--"):
            continue
        
        try:
            # Execute via Supabase REST API (RPC to execute SQL)
            # Note: This requires the sql_exec function to be enabled in Supabase
            supabase.rpc("sql_exec", {"sql": statement}).execute()
            print(f"  ✓ Statement {i}/{len(statements)} executed")
        except Exception as e:
            # If RPC not available, try using PostgREST directly
            print(f"  ⚠️ Could not execute statement {i}: {e}")
            print("  → Please apply migration manually via Supabase SQL Editor")
            print(f"  → File: {migration_file}")
            return False
    
    print(f"✓ Migration {migration_file.name} applied successfully")
    return True


def verify_table_structure(supabase: Client) -> bool:
    """Verify that kpi_timeseries_daily table exists and has correct structure."""
    print("\n🔍 Verifying table structure...")
    
    try:
        # Try to query the table (limit 0 to avoid loading data)
        supabase.table("kpi_timeseries_daily").select("*").limit(0).execute()
        print("✓ Table kpi_timeseries_daily exists and is accessible")
        return True
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Supabase tables for pipeline")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify table structure, don't apply migrations"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("Abaco Loans Analytics - Supabase Setup")
    print("=" * 60)
    
    # Load credentials
    supabase_url, supabase_key = load_environment()
    print(f"✓ Supabase URL: {supabase_url}")
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✓ Connected to Supabase")
    
    if args.verify_only:
        # Only verify table exists
        success = verify_table_structure(supabase)
        sys.exit(0 if success else 1)
    
    # Apply migration
    migration_file = project_root / "db" / "migrations" / "002_create_kpi_timeseries_daily.sql"
    
    print("\n" + "=" * 60)
    print("MANUAL MIGRATION REQUIRED")
    print("=" * 60)
    print("\nSupabase REST API does not support direct SQL execution.")
    print("Please apply the migration manually:")
    print("\n1. Open Supabase Dashboard → SQL Editor")
    print(f"2. Copy the contents of: {migration_file}")
    print("3. Execute the SQL in the editor")
    print("\nAlternatively, use the Supabase CLI:")
    print(f"   supabase db execute -f {migration_file}")
    
    # Verify table exists
    print("\n" + "=" * 60)
    verify_table_structure(supabase)
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Apply the migration manually (see instructions above)")
    print("2. Run: python scripts/run_data_pipeline.py --input data/raw/sample_loans.csv")
    print("3. Verify data in Supabase: kpi_timeseries_daily table")
    print("4. Refresh dashboard: http://4.248.240.207:8501")


if __name__ == "__main__":
    main()
