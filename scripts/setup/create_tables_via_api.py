#!/usr/bin/env python3
"""
Create monitoring tables in Supabase via REST API (RPC).
No direct PostgreSQL connection needed.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_env():
    """Load environment variables from .env.local"""
    env_file = project_root / ".env.local"
    env_vars = {}

    if not env_file.exists():
        print(f"❌ Error: {env_file} not found")
        return None

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value

    return env_vars


def create_tables_via_supabase():
    """Create monitoring tables using Supabase SDK"""
    print("🚀 Creating monitoring tables in Supabase...\n")

    # Load environment
    env = load_env()
    if not env:
        return False

    supabase_url = env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL")
    supabase_anon_key = env.get("SUPABASE_ANON_KEY")

    if not (supabase_url and supabase_anon_key):
        print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY not found")
        return False

    print(f"📍 URL: {supabase_url}")

    try:
        from supabase import create_client

        # Create Supabase client
        supabase = create_client(supabase_url, supabase_anon_key)
        print("✅ Connected to Supabase\n")

        # SQL queries to execute

        print("📊 Creating tables and indexes...\n")

        # Execute queries via RPC (using SQL execution)
        # Note: This requires a function in Supabase, so we'll use direct table operations instead

        # Create schema (skip for now as it requires RPC)
        # Instead, we'll create tables directly

        # Check if tables exist
        try:
            supabase.table("monitoring.kpi_definitions").select("*").limit(1).execute()
            print("✅ monitoring.kpi_definitions already exists")
        except Exception:
            print("⚠️  Table creation via SDK might be limited")
            print(
                "   Please create tables manually via: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql"
            )
            return False

        return True

    except ImportError:
        raise ValueError(
            "CRITICAL: Supabase SDK is not installed. Non-deterministic runtime installation is forbidden."
        ) from None
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n   Alternative: Create tables manually via Supabase UI")
        return False


def main():
    """Main execution"""

    # Check if we can use the direct REST API approach
    try:
        import requests
    except ImportError:
        raise ValueError(
            "CRITICAL: 'requests' library is not installed. Non-deterministic runtime installation is forbidden."
        ) from None

    env = load_env()
    if not env:
        return 1

    supabase_url = env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_ANON_KEY")

    print("🚀 Creating monitoring tables via Supabase REST API...\n")
    print(f"📍 Project: {supabase_url}\n")

    # Test connection first
    print("🔍 Testing Supabase connection...")
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/information_schema.tables?limit=1",
            headers={"apikey": supabase_key},
            timeout=5,
        )
        if response.status_code == 200:
            print("✅ Supabase accessible\n")
        else:
            print(f"⚠️  Supabase returned {response.status_code}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}\n")
        return 1

    # Since direct SQL execution via REST API requires a stored procedure,
    # we'll provide instructions instead
    print("=" * 70)
    print("📋 CREATE MONITORING TABLES")
    print("=" * 70)
    print("\nSince direct PostgreSQL connections are blocked, please:")
    print("\n1. Open: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql")
    print("\n2. Run these SQL queries in order:\n")

    queries = [
        ("1. Create Schema", "CREATE SCHEMA IF NOT EXISTS monitoring;"),
        (
            "2. Create KPI Definitions Table",
            """
CREATE TABLE IF NOT EXISTS monitoring.kpi_definitions (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    red_threshold NUMERIC,
    yellow_threshold NUMERIC,
    owner_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);""",
        ),
        (
            "3. Create KPI Values Table",
            """
CREATE TABLE IF NOT EXISTS monitoring.kpi_values (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER REFERENCES monitoring.kpi_definitions(id),
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    status TEXT CHECK (status IN ('green', 'yellow', 'red')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);""",
        ),
        (
            "4. Create Indexes",
            """
CREATE INDEX IF NOT EXISTS idx_kpi_values_timestamp ON monitoring.kpi_values(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_id ON monitoring.kpi_values(kpi_id);""",
        ),
        (
            "5. Insert KPI Definitions",
            """
INSERT INTO monitoring.kpi_definitions (name, category, description, unit) VALUES
('par_30', 'Asset Quality', 'Portfolio % at risk 30+ days', 'percent'),
('par_90', 'Asset Quality', 'Portfolio % at risk 90+ days', 'percent'),
('npl_rate', 'Asset Quality', 'Non-performing loan rate', 'percent'),
('default_rate', 'Asset Quality', 'Default rate', 'percent'),
('write_off_rate', 'Asset Quality', 'Write-off rate', 'percent'),
('collection_rate_6m', 'Cash Flow', '6-month collection rate', 'percent'),
('recovery_rate', 'Cash Flow', 'Recovery rate on defaults', 'percent'),
('portfolio_rotation', 'Growth', 'Portfolio rotation rate', 'percent'),
('disbursement_volume', 'Growth', 'Total disbursement volume', 'units'),
('new_loans', 'Growth', 'New loans originated', 'count'),
('total_aum', 'Portfolio Performance', 'Total assets under management', 'currency'),
('average_loan_size', 'Portfolio Performance', 'Average loan size', 'currency'),
('loan_count', 'Portfolio Performance', 'Total number of loans', 'count'),
('portfolio_yield', 'Portfolio Performance', 'Portfolio yield', 'percent'),
('active_borrowers', 'Customer Metrics', 'Active borrowers', 'count'),
('repeat_borrower_rate', 'Customer Metrics', 'Repeat borrower rate', 'percent'),
('processing_time', 'Operational Metrics', 'Average processing time', 'days'),
('automation_rate', 'Operational Metrics', 'Automation rate', 'percent'),
('portfolio_ghg', 'Environmental', 'Portfolio GHG emissions', 'tons')
ON CONFLICT (name) DO NOTHING;""",
        ),
    ]

    for title, query in queries:
        print(f"\n{title}:")
        print("-" * 70)
        print(query)
        print()

    print("=" * 70)
    print("\n✅ After running the queries, run this command:\n")
    print(
        "   python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv\n"
    )
    print("This will populate monitoring.kpi_values with real KPI data.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
