#!/usr/bin/env python3
"""
Initialize monitoring tables in Supabase automatically.
Run this after creating the tables via Supabase UI.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_env():
    """Load .env.local"""
    env_file = project_root / ".env.local"
    env = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env[key] = val
    return env


def main():
    print("🚀 Initializing monitoring tables...\n")

    env = load_env()
    supabase_url = env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_ANON_KEY")

    print(f"📍 Project: {supabase_url}\n")

    try:
        from supabase import create_client

        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase\n")

        # Step 1: Check if tables exist
        print("🔍 Checking tables...\n")

        try:
            result = supabase.table("monitoring.kpi_definitions").select("*").limit(1).execute()
            print("✅ monitoring.kpi_definitions exists")
            has_defs = True
        except Exception:
            print("❌ monitoring.kpi_definitions doesn't exist")
            has_defs = False

        try:
            result = supabase.table("monitoring.kpi_values").select("*").limit(1).execute()
            print("✅ monitoring.kpi_values exists")
            has_values = True
        except Exception:
            print("❌ monitoring.kpi_values doesn't exist")
            has_values = False

        if not has_defs or not has_values:
            print("\n" + "=" * 70)
            print("CREATE MONITORING TABLES")
            print("=" * 70 + "\n")

            print("Go to: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql")
            print("\nCopy and run this SQL:\n")

            sql = """
CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.kpi_definitions (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.kpi_values (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER REFERENCES monitoring.kpi_definitions(id),
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kpi_values_timestamp ON monitoring.kpi_values(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_id ON monitoring.kpi_values(kpi_id);

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
ON CONFLICT (name) DO NOTHING;
"""
            print(sql)
            print("\nThen run this command again to populate data:")
            print(
                "\n  python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv\n"
            )
            return 1

        # Step 2: Check if definitions are populated
        print("\n🔍 Checking KPI definitions...\n")
        result = (
            supabase.table("monitoring.kpi_definitions").select("count", "exact=true").execute()
        )
        count = result.count
        print(f"✅ Found {count} KPI definitions\n")

        # Step 3: Check if values are populated
        print("🔍 Checking KPI values...\n")
        result = supabase.table("monitoring.kpi_values").select("count", "exact=true").execute()
        count = result.count

        if count > 0:
            print(f"✅ Found {count} KPI values\n")
            print("=" * 70)
            print("✅ MONITORING TABLES ARE READY")
            print("=" * 70)
            print("\nNext: Open Grafana and view dashboards")
            print("  http://localhost:3001 → Dashboards → KPI Monitoring\n")
            return 0
        else:
            print("❌ No KPI values found\n")
            print("Run the pipeline to populate data:")
            print(
                "\n  python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv\n"
            )
            return 1

    except ImportError:
        print("❌ Supabase library not installed")
        print("\nInstall with:")
        print("  pip install supabase\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
