# Real Data Seeding Guide

**Status**: Production-Ready  
**Last Updated**: February 2, 2026  
**Data Protection**: PII Masking Enabled

---

## Table of Contents

1. [Overview](#overview)
2. [Data Requirements](#data-requirements)
3. [Local Development Setup](#local-development-setup)
4. [Production Data Import](#production-data-import)
5. [Data Validation](#data-validation)
6. [Sample Data Generation](#sample-data-generation)
7. [Seeding Scripts](#seeding-scripts)
8. [Best Practices](#best-practices)

---

## Overview

This guide covers seeding real and realistic data into the Abaco Loans Analytics platform. The platform processes lending data across multiple tables with relationships and validation rules.

### Database Schema

```
fact_loans (Primary table)
├── loan_id (PK)
├── borrower_id
├── amount
├── disbursement_date
├── maturity_date
├── interest_rate
├── status
├── days_past_due
└── organization_id

kpi_timeseries_daily (Calculated metrics)
├── kpi_id (PK)
├── date
├── kpi_name
├── kpi_value
├── organization_id
└── metadata

dim_borrowers (Borrower information - optional)
├── borrower_id (PK)
├── borrower_name
├── industry
├── credit_score
└── registration_date
```

---

## Data Requirements

### Required Columns (fact_loans)

```python
REQUIRED_COLUMNS = [
    'loan_id',          # str: Unique loan identifier (e.g., "LOAN-2024-001")
    'borrower_id',      # str: Borrower identifier (e.g., "BRRW-001")
    'amount',           # float: Loan amount (e.g., 50000.00)
    'disbursement_date',# date: When loan was disbursed (YYYY-MM-DD)
    'maturity_date',    # date: Expected repayment date
    'interest_rate',    # float: Annual interest rate (e.g., 36.5 for 36.5%)
    'status',           # str: Loan status (active, delinquent, defaulted, closed)
    'days_past_due',    # int: DPD (0 for current, >0 for delinquent)
]
```

### Optional Columns

```python
OPTIONAL_COLUMNS = [
    'organization_id',  # str: Organization/lender ID (for multi-tenant)
    'term_months',      # int: Loan term in months
    'payment_frequency',# str: monthly, weekly, biweekly
    'collateral_type',  # str: Type of collateral
    'purpose',          # str: Loan purpose (working_capital, equipment, etc.)
    'outstanding_balance', # float: Current balance owed
    'total_paid',       # float: Total amount paid to date
]
```

### Data Validation Rules

**Already Implemented**: `python/validation.py`

```python
# Validation rules enforced:
- loan_id: Non-null, unique, max 50 chars
- amount: Positive float, < 10M (configurable)
- disbursement_date: Valid ISO8601 date, not in future
- maturity_date: After disbursement_date
- interest_rate: 0-100 (percentage)
- status: One of [active, delinquent, defaulted, closed, written_off]
- days_past_due: Non-negative integer
```

---

## Local Development Setup

### Step 1: Configure Environment

```bash
# Copy environment template
cp .env.example .env.local

# Edit .env.local with your Supabase credentials
nano .env.local
```

**Required Environment Variables**:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
PIPELINE_ENV=development
```

### Step 2: Create Database Tables

```bash
# Run table setup script
python scripts/setup_supabase_tables.py --env development

# Verify tables created
python -c "
from python.supabase_pool import get_supabase_client
client = get_supabase_client()
tables = client.table('fact_loans').select('count').execute()
print(f'✅ fact_loans table exists')
"
```

### Step 3: Load Sample Data

```bash
# Load pre-built sample dataset (100 loans)
python scripts/run_data_pipeline.py \
  --input data/raw/sample_loans.csv \
  --mode full

# Or generate fresh sample data
python scripts/generate_sample_data.py \
  --num-loans 100 \
  --start-date 2024-01-01 \
  --end-date 2026-01-31 \
  --output data/raw/generated_loans.csv
```

---

## Production Data Import

### Option 1: CSV Upload (Recommended for <10K records)

**Prepare CSV File**:

```csv
loan_id,borrower_id,amount,disbursement_date,maturity_date,interest_rate,status,days_past_due
LOAN-2024-001,BRRW-1001,50000.00,2024-03-15,2025-03-15,36.5,active,0
LOAN-2024-002,BRRW-1002,75000.00,2024-04-01,2025-04-01,38.2,active,15
LOAN-2024-003,BRRW-1003,100000.00,2024-05-10,2025-05-10,35.0,delinquent,45
LOAN-2024-004,BRRW-1001,60000.00,2024-06-20,2025-06-20,37.5,closed,0
```

**Run Pipeline Import**:

```bash
python scripts/run_data_pipeline.py \
  --input /path/to/production_loans.csv \
  --mode full \
  --env production
```

**Import Steps**:
1. **Phase 1 (Ingestion)**: Read CSV, validate schema, check data types
2. **Phase 2 (Transformation)**: Clean data, mask PII, normalize formats
3. **Phase 3 (Calculation)**: Calculate KPIs (PAR-30, PAR-90, etc.)
4. **Phase 4 (Output)**: Export to Supabase, save results

### Option 2: Direct Database Insert (For >10K records)

**Use Batch Insert Script**:

```python
# scripts/bulk_import_production.py
import pandas as pd
from python.supabase_pool import get_supabase_client
from python.validation import validate_loan_data
import logging

logger = logging.getLogger(__name__)

def bulk_import_loans(csv_path: str, batch_size: int = 1000):
    """
    Bulk import loans with validation and batching.
    
    Args:
        csv_path: Path to CSV file
        batch_size: Number of records per batch insert
    """
    # Load data
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} loans from {csv_path}")
    
    # Validate data
    errors = validate_loan_data(df)
    if errors:
        raise ValueError(f"Validation failed: {errors}")
    
    # Get Supabase client
    client = get_supabase_client()
    
    # Batch insert
    total_inserted = 0
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        records = batch.to_dict('records')
        
        try:
            response = client.table('fact_loans').insert(records).execute()
            total_inserted += len(records)
            logger.info(f"Inserted batch {i//batch_size + 1}: {len(records)} records")
        except Exception as e:
            logger.error(f"Failed to insert batch {i//batch_size + 1}: {e}")
            raise
    
    logger.info(f"✅ Successfully imported {total_inserted} loans")
    return total_inserted

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python bulk_import_production.py <csv_path>")
        sys.exit(1)
    
    bulk_import_loans(sys.argv[1])
```

**Run Import**:

```bash
python scripts/bulk_import_production.py production_loans.csv
```

### Option 3: API Upload (For External Systems)

**Create API Endpoint** (`python/apps/analytics/api/main.py`):

```python
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
import pandas as pd
import io

app = FastAPI()

class LoanData(BaseModel):
    loan_id: str
    borrower_id: str
    amount: float
    disbursement_date: str
    maturity_date: str
    interest_rate: float
    status: str
    days_past_due: int

@app.post("/api/loans/upload")
async def upload_loans(file: UploadFile):
    """Upload CSV file with loan data."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    # Read CSV
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    # Validate
    from python.validation import validate_loan_data
    errors = validate_loan_data(df)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    
    # Import via pipeline
    from scripts.run_data_pipeline import run_pipeline
    result = run_pipeline(
        input_data=df,
        mode='full',
        env='production'
    )
    
    return {
        "status": "success",
        "loans_imported": len(df),
        "kpis_calculated": len(result['kpi_results'])
    }

@app.post("/api/loans/batch")
async def batch_create_loans(loans: list[LoanData]):
    """Create multiple loans via API."""
    # Convert to DataFrame
    df = pd.DataFrame([loan.dict() for loan in loans])
    
    # Validate
    errors = validate_loan_data(df)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    
    # Insert to database
    client = get_supabase_client()
    records = df.to_dict('records')
    response = client.table('fact_loans').insert(records).execute()
    
    return {
        "status": "success",
        "loans_created": len(loans)
    }
```

**Usage**:

```bash
# Upload CSV via API
curl -X POST "https://api.abaco.com/api/loans/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@production_loans.csv"

# Batch create via JSON
curl -X POST "https://api.abaco.com/api/loans/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "loan_id": "LOAN-2024-001",
      "borrower_id": "BRRW-1001",
      "amount": 50000.00,
      "disbursement_date": "2024-03-15",
      "maturity_date": "2025-03-15",
      "interest_rate": 36.5,
      "status": "active",
      "days_past_due": 0
    }
  ]'
```

---

## Data Validation

### Pre-Import Validation

**Run Validation Script**:

```bash
# Validate CSV before import
python scripts/validate_loan_data.py --input production_loans.csv

# Expected output:
# ✅ Schema validation: PASS
# ✅ Data type validation: PASS
# ✅ Business rule validation: PASS
# ✅ Duplicate check: PASS (0 duplicates)
# ✅ Date logic validation: PASS
```

**Validation Script** (`scripts/validate_loan_data.py`):

```python
import pandas as pd
from python.validation import validate_loan_data
import sys

def main(csv_path: str):
    """Validate loan data before import."""
    print(f"Validating {csv_path}...")
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records")
    
    # Run validation
    errors = validate_loan_data(df)
    
    if errors:
        print("\n❌ Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print("\n✅ Validation PASSED")
    print(f"  - {len(df)} loans validated")
    print(f"  - Date range: {df['disbursement_date'].min()} to {df['disbursement_date'].max()}")
    print(f"  - Total amount: ${df['amount'].sum():,.2f}")
    print(f"  - Status breakdown:")
    for status, count in df['status'].value_counts().items():
        print(f"    - {status}: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_loan_data.py <csv_path>")
        sys.exit(1)
    main(sys.argv[1])
```

### Post-Import Validation

```bash
# Verify data imported successfully
python -c "
from python.supabase_pool import get_supabase_client

client = get_supabase_client()

# Count loans
response = client.table('fact_loans').select('count', count='exact').execute()
print(f'Total loans: {response.count}')

# Check status distribution
response = client.table('fact_loans').select('status').execute()
import pandas as pd
df = pd.DataFrame(response.data)
print('\nStatus distribution:')
print(df['status'].value_counts())

# Check date range
response = client.table('fact_loans').select('disbursement_date').order('disbursement_date', desc=False).limit(1).execute()
min_date = response.data[0]['disbursement_date']
response = client.table('fact_loans').select('disbursement_date').order('disbursement_date', desc=True).limit(1).execute()
max_date = response.data[0]['disbursement_date']
print(f'\nDate range: {min_date} to {max_date}')
"
```

---

## Sample Data Generation

### Generate Realistic Loan Data

**Script**: `scripts/generate_sample_data.py`

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_loan_data(
    num_loans: int = 100,
    start_date: str = "2024-01-01",
    end_date: str = "2026-01-31",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate realistic loan data for testing.
    
    Args:
        num_loans: Number of loans to generate
        start_date: Start date for disbursements
        end_date: End date for disbursements
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with loan data
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = (end - start).days
    
    # Generate loan data
    loans = []
    for i in range(num_loans):
        # Random disbursement date
        days_offset = random.randint(0, date_range)
        disbursement = start + timedelta(days=days_offset)
        
        # Loan term (6-24 months)
        term_months = random.choice([6, 12, 18, 24])
        maturity = disbursement + timedelta(days=term_months * 30)
        
        # Loan amount ($10K-$500K, focused around $50K-$100K)
        amount = np.random.lognormal(mean=11, sigma=0.5)
        amount = max(10000, min(500000, amount))
        
        # Interest rate (28%-45%, focused around 35%)
        interest_rate = np.random.normal(loc=36, scale=4)
        interest_rate = max(28, min(45, interest_rate))
        
        # Status distribution (realistic portfolio)
        status_weights = {
            'active': 0.70,      # 70% performing
            'delinquent': 0.20,  # 20% delinquent
            'defaulted': 0.05,   # 5% defaulted
            'closed': 0.05       # 5% closed/repaid
        }
        status = random.choices(
            list(status_weights.keys()),
            weights=list(status_weights.values())
        )[0]
        
        # Days past due based on status
        if status == 'active' or status == 'closed':
            dpd = 0
        elif status == 'delinquent':
            dpd = random.randint(1, 90)
        else:  # defaulted
            dpd = random.randint(91, 365)
        
        # Create loan record
        loan = {
            'loan_id': f'LOAN-{disbursement.year}-{i+1:04d}',
            'borrower_id': f'BRRW-{random.randint(1, num_loans//3):04d}',
            'amount': round(amount, 2),
            'disbursement_date': disbursement.strftime('%Y-%m-%d'),
            'maturity_date': maturity.strftime('%Y-%m-%d'),
            'interest_rate': round(interest_rate, 2),
            'status': status,
            'days_past_due': dpd,
            'term_months': term_months,
            'outstanding_balance': round(amount * random.uniform(0.2, 0.95), 2) if status != 'closed' else 0,
            'total_paid': round(amount * random.uniform(0.05, 0.80), 2),
            'organization_id': 'ORG-001'
        }
        loans.append(loan)
    
    df = pd.DataFrame(loans)
    return df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample loan data')
    parser.add_argument('--num-loans', type=int, default=100, help='Number of loans')
    parser.add_argument('--start-date', default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2026-01-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='data/raw/generated_loans.csv', help='Output CSV path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Generate data
    df = generate_loan_data(
        num_loans=args.num_loans,
        start_date=args.start_date,
        end_date=args.end_date,
        seed=args.seed
    )
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    print(f"✅ Generated {len(df)} loans")
    print(f"   Saved to: {args.output}")
    print(f"\nSummary:")
    print(f"  - Date range: {df['disbursement_date'].min()} to {df['disbursement_date'].max()}")
    print(f"  - Total amount: ${df['amount'].sum():,.2f}")
    print(f"  - Average loan: ${df['amount'].mean():,.2f}")
    print(f"\nStatus distribution:")
    print(df['status'].value_counts())
```

**Usage**:

```bash
# Generate 500 loans for 2024-2025
python scripts/generate_sample_data.py \
  --num-loans 500 \
  --start-date 2024-01-01 \
  --end-date 2025-12-31 \
  --output data/raw/loans_2024_2025.csv

# Generate 1000 loans for testing
python scripts/generate_sample_data.py --num-loans 1000
```

---

## Seeding Scripts

### Supabase KPI Seeding

**Already Implemented**: `scripts/load_sample_kpis_supabase.py`

```bash
# Load sample KPIs for date range
python scripts/load_sample_kpis_supabase.py \
  --supabase-url $SUPABASE_URL \
  --supabase-key $SUPABASE_SERVICE_ROLE_KEY \
  --start-date 2024-01-01 \
  --end-date 2026-01-31
```

**What it does**:
- Generates realistic KPI values for each day
- Inserts into `kpi_timeseries_daily` table
- Creates 19 KPIs × number of days
- Includes PAR-30, PAR-90, default rate, collection rate, etc.

### Complete Database Seeding

**Script**: `scripts/seed_complete_database.sh`

```bash
#!/bin/bash
# Complete database seeding for development/staging

set -e

echo "🚀 Starting complete database seeding..."

# 1. Create tables
echo "📊 Creating database tables..."
python scripts/setup_supabase_tables.py --env development

# 2. Generate sample loans
echo "📝 Generating sample loan data..."
python scripts/generate_sample_data.py \
  --num-loans 500 \
  --start-date 2024-01-01 \
  --end-date 2026-01-31 \
  --output /tmp/sample_loans.csv

# 3. Import loans via pipeline
echo "⚙️  Importing loans via pipeline..."
python scripts/run_data_pipeline.py \
  --input /tmp/sample_loans.csv \
  --mode full \
  --env development

# 4. Load KPI time series
echo "📈 Loading KPI time series..."
python scripts/load_sample_kpis_supabase.py \
  --start-date 2024-01-01 \
  --end-date 2026-01-31

# 5. Verify seeding
echo "✅ Verifying data..."
python -c "
from python.supabase_pool import get_supabase_client
client = get_supabase_client()

loan_count = client.table('fact_loans').select('count', count='exact').execute().count
kpi_count = client.table('kpi_timeseries_daily').select('count', count='exact').execute().count

print(f'Loans: {loan_count}')
print(f'KPIs: {kpi_count}')
print('✅ Database seeding complete!')
"

echo "🎉 Complete! Your database is ready."
```

**Run**:

```bash
chmod +x scripts/seed_complete_database.sh
./scripts/seed_complete_database.sh
```

---

## Best Practices

### Security

✅ **DO:**
- Use service role key for production seeding (not anon key)
- Validate all data before import
- Mask PII automatically (handled by `src/compliance.py`)
- Use batch inserts (1000 records at a time)
- Log all seeding operations
- Take database backup before large imports

❌ **DON'T:**
- Commit production data to Git
- Seed production with unvalidated external data
- Use plain text credentials in scripts
- Skip validation to save time
- Import without logging

### Performance

```python
# ✅ GOOD: Batch insert
for i in range(0, len(df), 1000):
    batch = df.iloc[i:i+1000].to_dict('records')
    client.table('fact_loans').insert(batch).execute()

# ❌ BAD: Row-by-row insert
for _, row in df.iterrows():
    client.table('fact_loans').insert(row.to_dict()).execute()  # Slow!
```

### Data Quality

```python
# Always validate before import
from python.validation import validate_loan_data

errors = validate_loan_data(df)
if errors:
    # Fix errors or reject import
    raise ValueError(f"Validation failed: {errors}")

# Check for duplicates
duplicates = df[df.duplicated(subset=['loan_id'], keep=False)]
if not duplicates.empty:
    raise ValueError(f"Found {len(duplicates)} duplicate loan_ids")

# Verify date logic
invalid_dates = df[df['disbursement_date'] > df['maturity_date']]
if not invalid_dates.empty:
    raise ValueError(f"Found {len(invalid_dates)} loans with invalid dates")
```

### Testing

```bash
# Test on small dataset first
python scripts/run_data_pipeline.py \
  --input data/raw/sample_loans_small.csv \
  --mode dry-run  # Only ingestion, no database writes

# Verify results before production import
python scripts/validate_loan_data.py production_loans.csv
```

---

## Troubleshooting

### Common Issues

**1. "Column not found" error**:
```bash
# Check CSV headers
head -1 production_loans.csv

# Should match: loan_id,borrower_id,amount,disbursement_date,...
```

**2. "Validation failed" error**:
```bash
# Run validation to see specific errors
python scripts/validate_loan_data.py production_loans.csv
```

**3. "Database connection failed"**:
```bash
# Test connection
python scripts/test_supabase_connection.py

# Verify environment variables
env | grep SUPABASE
```

**4. Import too slow**:
```python
# Increase batch size (default: 1000)
bulk_import_loans('file.csv', batch_size=5000)

# Or use direct SQL copy (fastest)
# psql $DATABASE_URL -c "\COPY fact_loans FROM 'file.csv' CSV HEADER"
```

---

## Additional Resources

- **Validation Module**: `python/validation.py`
- **Pipeline Script**: `scripts/run_data_pipeline.py`
- **Sample Data**: `data/raw/sample_loans.csv`
- **Business Rules**: `config/business_rules.yaml`
- **KPI Definitions**: `config/kpis/kpi_definitions.yaml`

---

**Document Version**: 1.0  
**Maintained By**: Data Engineering Team  
**Review Cycle**: Quarterly
