import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def load_env():
    env_file = project_root / '.env.local'
    env = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and (not line.startswith('#')) and ('=' in line):
                key, val = line.split('=', 1)
                env[key] = val
    return env

def main():
    print('🚀 Initializing monitoring tables...\n')
    env = load_env()
    supabase_url = env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL')
    supabase_key = env.get('SUPABASE_ANON_KEY')
    print(f'📍 Project: {supabase_url}\n')
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        print('✅ Connected to Supabase\n')
        print('🔍 Checking tables...\n')
        try:
            supabase.table('monitoring.kpi_definitions').select('*').limit(1).execute()
            print('✅ monitoring.kpi_definitions exists')
            has_defs = True
        except Exception:
            print("❌ monitoring.kpi_definitions doesn't exist")
            has_defs = False
        try:
            supabase.table('monitoring.kpi_values').select('*').limit(1).execute()
            print('✅ monitoring.kpi_values exists')
            has_values = True
        except Exception:
            print("❌ monitoring.kpi_values doesn't exist")
            has_values = False
        if not has_defs or not has_values:
            print('\n' + '=' * 70)
            print('CREATE MONITORING TABLES')
            print('=' * 70 + '\n')
            print('Go to: https://supabase.com/dashboard/project/sddviizcgheusvwqpthm/sql')
            print('\nCopy and run this SQL:\n')
            sql = "\nCREATE SCHEMA IF NOT EXISTS monitoring;\n\nCREATE TABLE IF NOT EXISTS monitoring.kpi_definitions (\n    id SERIAL PRIMARY KEY,\n    name TEXT UNIQUE NOT NULL,\n    category TEXT NOT NULL,\n    description TEXT,\n    unit TEXT,\n    created_at TIMESTAMPTZ DEFAULT NOW()\n);\n\nCREATE TABLE IF NOT EXISTS monitoring.kpi_values (\n    id SERIAL PRIMARY KEY,\n    kpi_id INTEGER REFERENCES monitoring.kpi_definitions(id),\n    value NUMERIC NOT NULL,\n    timestamp TIMESTAMPTZ NOT NULL,\n    status TEXT,\n    created_at TIMESTAMPTZ DEFAULT NOW()\n);\n\nCREATE INDEX IF NOT EXISTS idx_kpi_values_timestamp ON monitoring.kpi_values(timestamp DESC);\nCREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_id ON monitoring.kpi_values(kpi_id);\n\nINSERT INTO monitoring.kpi_definitions (name, category, description, unit) VALUES\n('par_30', 'Asset Quality', 'Portfolio % at risk 30+ days', 'percent'),\n('par_90', 'Asset Quality', 'Portfolio % at risk 90+ days', 'percent'),\n('npl_rate', 'Asset Quality', 'Non-performing loan rate', 'percent'),\n('default_rate', 'Asset Quality', 'Default rate', 'percent'),\n('write_off_rate', 'Asset Quality', 'Write-off rate', 'percent'),\n('collection_rate_6m', 'Cash Flow', '6-month collection rate', 'percent'),\n('recovery_rate', 'Cash Flow', 'Recovery rate on defaults', 'percent'),\n('portfolio_rotation', 'Growth', 'Portfolio rotation rate', 'percent'),\n('disbursement_volume', 'Growth', 'Total disbursement volume', 'units'),\n('new_loans', 'Growth', 'New loans originated', 'count'),\n('total_aum', 'Portfolio Performance', 'Total assets under management', 'currency'),\n('average_loan_size', 'Portfolio Performance', 'Average loan size', 'currency'),\n('loan_count', 'Portfolio Performance', 'Total number of loans', 'count'),\n('portfolio_yield', 'Portfolio Performance', 'Portfolio yield', 'percent'),\n('active_borrowers', 'Customer Metrics', 'Active borrowers', 'count'),\n('repeat_borrower_rate', 'Customer Metrics', 'Repeat borrower rate', 'percent'),\n('processing_time', 'Operational Metrics', 'Average processing time', 'days'),\n('automation_rate', 'Operational Metrics', 'Automation rate', 'percent'),\n('portfolio_ghg', 'Environmental', 'Portfolio GHG emissions', 'tons')\nON CONFLICT (name) DO NOTHING;\n"
            print(sql)
            print('\nThen run this command again to populate data:')
            print('\n  python scripts/data/run_data_pipeline.py --input data/samples/loans_sample_data_20260202.csv\n')
            return 1
        print('\n🔍 Checking KPI definitions...\n')
        result = supabase.table('monitoring.kpi_definitions').select('count', 'exact=true').execute()
        count = result.count
        print(f'✅ Found {count} KPI definitions\n')
        print('🔍 Checking KPI values...\n')
        result = supabase.table('monitoring.kpi_values').select('count', 'exact=true').execute()
        count = result.count
        if count > 0:
            print(f'✅ Found {count} KPI values\n')
            print('=' * 70)
            print('✅ MONITORING TABLES ARE READY')
            print('=' * 70)
            print('\nNext: Open Grafana and view dashboards')
            print('  http://localhost:3001 → Dashboards → KPI Monitoring\n')
            return 0
        else:
            print('❌ No KPI values found\n')
            print('Run the pipeline to populate data:')
            print('\n  python scripts/data/run_data_pipeline.py --input data/samples/loans_sample_data_20260202.csv\n')
            return 1
    except ImportError:
        print('❌ Supabase library not installed')
        print('\nInstall with:')
        print('  pip install supabase\n')
        return 1
if __name__ == '__main__':
    sys.exit(main())
