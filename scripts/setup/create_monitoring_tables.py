#!/usr/bin/env python3
"""
Create monitoring tables and populate with sample KPI data in Supabase.
"""

import sys
from datetime import datetime
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

def create_tables(conn):
    """Create monitoring tables"""
    print("📊 Creating monitoring tables...")
    
    with conn.cursor() as cursor:
        # Create schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS monitoring;")
        print("  ✅ Created monitoring schema")
        
        # Create kpi_definitions table
        cursor.execute("""
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
            );
        """)
        print("  ✅ Created kpi_definitions table")
        
        # Create kpi_values table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring.kpi_values (
                id SERIAL PRIMARY KEY,
                kpi_id INTEGER REFERENCES monitoring.kpi_definitions(id),
                value NUMERIC NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                status TEXT CHECK (status IN ('green', 'yellow', 'red')),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        print("  ✅ Created kpi_values table")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_values_timestamp ON monitoring.kpi_values(timestamp DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_id ON monitoring.kpi_values(kpi_id);")
        print("  ✅ Created indexes")
        
        conn.commit()

def populate_kpis(conn):
    """Populate KPI definitions"""
    print("\n📋 Populating KPI definitions...")
    
    kpis = [
        ("par_30", "Asset Quality", "Portfolio % at risk 30+ days", "percent"),
        ("par_90", "Asset Quality", "Portfolio % at risk 90+ days", "percent"),
        ("npl_rate", "Asset Quality", "Non-performing loan rate", "percent"),
        ("default_rate", "Asset Quality", "Default rate", "percent"),
        ("write_off_rate", "Asset Quality", "Write-off rate", "percent"),
        ("collection_rate_6m", "Cash Flow", "6-month collection rate", "percent"),
        ("recovery_rate", "Cash Flow", "Recovery rate on defaults", "percent"),
        ("portfolio_rotation", "Growth", "Portfolio rotation rate", "percent"),
        ("disbursement_volume", "Growth", "Total disbursement volume", "units"),
        ("new_loans", "Growth", "New loans originated", "count"),
        ("total_aum", "Portfolio Performance", "Total assets under management", "currency"),
        ("average_loan_size", "Portfolio Performance", "Average loan size", "currency"),
        ("loan_count", "Portfolio Performance", "Total number of loans", "count"),
        ("portfolio_yield", "Portfolio Performance", "Portfolio yield", "percent"),
        ("active_borrowers", "Customer Metrics", "Active borrowers", "count"),
        ("repeat_borrower_rate", "Customer Metrics", "Repeat borrower rate", "percent"),
        ("processing_time", "Operational Metrics", "Average processing time", "days"),
        ("automation_rate", "Operational Metrics", "Automation rate", "percent"),
        ("portfolio_ghg", "Environmental", "Portfolio GHG emissions", "tons"),
    ]
    
    with conn.cursor() as cursor:
        for name, category, desc, unit in kpis:
            cursor.execute("""
                INSERT INTO monitoring.kpi_definitions (name, category, description, unit)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (name, category, desc, unit))
        
        conn.commit()
    
    print(f"  ✅ Inserted {len(kpis)} KPI definitions")

def populate_sample_data(conn):
    """Populate sample KPI values"""
    print("\n📊 Populating sample KPI values...")
    
    sample_values = [
        (1, 5.2, "green"),      # par_30
        (2, 2.1, "green"),      # par_90
        (3, 7.3, "yellow"),     # npl_rate
        (4, 3.5, "green"),      # default_rate
        (5, 1.2, "green"),      # write_off_rate
        (6, 94.5, "green"),     # collection_rate_6m
        (7, 68.2, "green"),     # recovery_rate
        (8, 15.8, "green"),     # portfolio_rotation
        (9, 12500000, "green"), # disbursement_volume
        (10, 1250, "green"),    # new_loans
        (11, 450000000, "green"), # total_aum
        (12, 18000, "green"),   # average_loan_size
        (13, 25000, "green"),   # loan_count
        (14, 8.5, "green"),     # portfolio_yield
        (15, 18000, "green"),   # active_borrowers
        (16, 42.5, "green"),    # repeat_borrower_rate
        (17, 2.3, "green"),     # processing_time
        (18, 65.0, "green"),    # automation_rate
        (19, 15420, "green"),   # portfolio_ghg
    ]
    
    with conn.cursor() as cursor:
        now = datetime.utcnow()
        
        for kpi_id, value, status in sample_values:
            cursor.execute("""
                INSERT INTO monitoring.kpi_values (kpi_id, value, timestamp, status)
                VALUES (%s, %s, %s, %s);
            """, (kpi_id, value, now, status))
        
        conn.commit()
    
    print(f"  ✅ Inserted {len(sample_values)} sample KPI values")

def verify_data(conn):
    """Verify data was inserted"""
    print("\n✅ Verifying data...")
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM monitoring.kpi_definitions;")
        kpi_count = cursor.fetchone()[0]
        print(f"  ✅ KPI Definitions: {kpi_count} rows")
        
        cursor.execute("SELECT COUNT(*) FROM monitoring.kpi_values;")
        value_count = cursor.fetchone()[0]
        print(f"  ✅ KPI Values: {value_count} rows")

def main():
    """Main execution"""
    print("🚀 Setting up Supabase monitoring tables...\n")
    
    # Load environment
    env = load_env()
    if not env:
        return 1
    
    # Extract credentials
    supabase_url = env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL")
    db_password = env.get("POSTGRES_PASSWORD")
    supabase_project = env.get("SUPABASE_PROJECT_REF")
    
    if not (db_password and supabase_project):
        print("❌ Error: POSTGRES_PASSWORD or SUPABASE_PROJECT_REF not found in .env.local")
        return 1
    
    # Build proper connection string with URL-encoded password
    from urllib.parse import quote_plus
    encoded_password = quote_plus(db_password)
    db_url = f"postgresql://postgres:{encoded_password}@db.{supabase_project}.supabase.co:5432/postgres"
    
    print(f"📍 Project: {supabase_project}")
    print("📍 Connecting to database...")
    
    # Connect to database
    try:
        import psycopg2
        
        # Parse connection string
        conn = psycopg2.connect(db_url)
        print("✅ Connected to Supabase PostgreSQL\n")
        
        # Create tables
        create_tables(conn)
        
        # Populate data
        populate_kpis(conn)
        populate_sample_data(conn)
        
        # Verify
        verify_data(conn)
        
        conn.close()
        
    except ImportError:
        print("❌ Error: psycopg2 not installed")
        print("   Install with: pip install psycopg2-binary")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("\n" + "="*50)
    print("✅ Monitoring tables setup complete!")
    print("="*50)
    print("\n📊 Next steps:")
    print("  1. Open Grafana: http://localhost:3001")
    print("  2. Go to Configuration → Data Sources")
    print("  3. Click 'Test' on Supabase PostgreSQL")
    print("  4. Check dashboards in 'KPI Monitoring' folder")
    print("\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
