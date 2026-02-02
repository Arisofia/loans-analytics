# Data Seeding Guide

## Overview

This guide covers importing, validating, and seeding data into the Abaco Loans Analytics platform for development, testing, and production use.

**Data Sources**: CSV files, Supabase direct imports, third-party APIs (future), synthetic data generation

## Quick Start

### Generate Realistic Sample Data

**Use the built-in sample data generator**:

```bash
# Generate 100 loans with realistic Mexican data
python scripts/generate_sample_data.py \
  --output data/raw/sample_loans.csv \
  --count 100

# Generate specific date range
python scripts/generate_sample_data.py \
  --output data/raw/historical_loans.csv \
  --count 1000 \
  --start-date 2023-01-01 \
  --end-date 2023-12-31

# Reproducible dataset (fixed seed)
python scripts/generate_sample_data.py \
  --output data/raw/test_loans.csv \
  --count 50 \
  --seed 42
```

**Output preview**:

```
✅ Generated 100 realistic loan records in data/raw/sample_loans.csv

Distribution by status:
  current: 68 (68.0%)
  delinquent: 21 (21.0%)
  defaulted: 6 (6.0%)
  paid_off: 5 (5.0%)

File size: 162.5 KB
```

### Run Full Pipeline

**Process the generated data**:

```bash
# Run 4-phase pipeline (ingestion → transformation → calculation → output)
python scripts/run_data_pipeline.py \
  --input data/raw/sample_loans.csv \
  --verbose

# Outputs:
# - data/processed/<run_id>/transformed_loans.parquet
# - data/processed/<run_id>/kpi_results.json
# - data/compliance/<run_id>_compliance.json
```

**Verify outputs**:

```bash
# Check run directory
ls -lh data/processed/$(ls -t data/processed | head -1)/

# View KPI results
cat data/processed/$(ls -t data/processed | head -1)/kpi_results.json | jq '.kpis'
```

## Data Schema

### Required Columns

**Minimum schema** for `fact_loans` table:

| Column              | Type    | Required | Description                         | Example                                          |
| ------------------- | ------- | -------- | ----------------------------------- | ------------------------------------------------ |
| `loan_id`           | string  | ✅       | Unique loan identifier              | "LOAN-2024-001234"                               |
| `borrower_name`     | string  | ✅       | Full name of borrower               | "Juan Pérez García"                              |
| `amount`            | decimal | ✅       | Principal amount (2 decimal places) | 75000.00                                         |
| `rate`              | float   | ✅       | Annual interest rate (decimal)      | 0.34 (34%)                                       |
| `disbursement_date` | date    | ✅       | Date loan was disbursed             | "2024-01-15"                                     |
| `maturity_date`     | date    | ✅       | Expected final payment date         | "2024-07-15"                                     |
| `status`            | string  | ✅       | Loan status (enum)                  | "current", "delinquent", "defaulted", "paid_off" |

### Optional Columns (Enrichment)

| Column             | Type    | Description                 | Example                                     |
| ------------------ | ------- | --------------------------- | ------------------------------------------- |
| `region`           | string  | Geographic region           | "Ciudad de México"                          |
| `industry`         | string  | Borrower industry           | "Retail", "Manufacturing"                   |
| `collateral_value` | decimal | Collateral value if secured | 100000.00                                   |
| `risk_score`       | integer | Credit score (300-850)      | 720                                         |
| `rfc`              | string  | Mexican tax ID              | "PEGJ850101ABC"                             |
| `payment_history`  | json    | Array of payment records    | `[{"date": "2024-02-15", "amount": 12500}]` |
| `days_past_due`    | integer | DPD (calculated field)      | 15                                          |

### Business Rules

**Status definitions** (from `config/business_rules.yaml`):

- **`current`**: All payments on time (DPD = 0)
- **`delinquent`**: 1-179 days past due
- **`defaulted`**: 180+ days past due (Non-Performing Loan)
- **`paid_off`**: Loan fully repaid
- **`written_off`**: Loan charged off (accounting treatment)

**DPD buckets** (for risk segmentation):

- `0-30`: Low risk
- `31-60`: Medium risk
- `61-90`: High risk
- `91-180`: Critical risk
- `180+`: Default (NPL)

## CSV Import

### Format Validation

**Before import**, validate CSV structure:

```python
# Use built-in validator
from python.validation import validate_dataframe
import pandas as pd

df = pd.read_csv("data/raw/loans.csv")
is_valid, errors = validate_dataframe(df)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ CSV is valid")
```

**Common validation errors**:

- Missing required columns (`loan_id`, `amount`, `disbursement_date`)
- Invalid date formats (use ISO 8601: `YYYY-MM-DD`)
- Non-numeric amounts (`amount` must be numeric with 2 decimal places)
- Invalid status values (must be one of: `current`, `delinquent`, `defaulted`, `paid_off`, `written_off`)
- Negative amounts or rates

### Manual CSV Import (Supabase)

**For small datasets** (<1000 rows):

1. Navigate to Supabase Dashboard → Table Editor
2. Select `fact_loans` table
3. Click "Insert" → "Import from CSV"
4. Upload CSV file
5. Map columns to table schema
6. Click "Import"

**Verify import**:

```sql
SELECT COUNT(*) as total_loans FROM fact_loans;
SELECT status, COUNT(*) as count
FROM fact_loans
GROUP BY status;
```

### Programmatic CSV Import

**For large datasets** (>1000 rows):

```python
import pandas as pd
from supabase import create_client
from python.supabase_pool import get_connection_pool

import asyncio

from python.logging_config import get_logger
from python.validation import validate_dataframe

logger = get_logger(__name__)


async def main() -> None:
    # Read CSV
    df = pd.read_csv("data/raw/large_dataset.csv")

    # Validate
    is_valid, errors = validate_dataframe(df)
    if not is_valid:
        raise ValueError(f"Validation failed: {errors}")

    # Convert DataFrame to list of dicts
    records = df.to_dict(orient="records")

    # Batch insert (1000 rows at a time)
    pool = get_connection_pool()
    async with pool.acquire() as conn:
        for i in range(0, len(records), 1000):
            batch = records[i : i + 1000]
            await conn.table("fact_loans").insert(batch).execute()
            logger.info("Inserted %s/%s rows", i + 1000, len(records))

    logger.info("✅ Imported %s loans successfully", len(records))


if __name__ == "__main__":
    asyncio.run(main())
```

### Handling Duplicates

**Prevent duplicate imports**:

```python
# Check if loan_id already exists before insert
existing_loan_ids = set(
    supabase.table("fact_loans")
    .select("loan_id")
    .execute()
    .data
)

new_records = [
    r for r in records
    if r["loan_id"] not in existing_loan_ids
]

print(f"Skipping {len(records) - len(new_records)} duplicates")
print(f"Inserting {len(new_records)} new loans")
```

**Or use upsert** (update if exists, insert if not):

```python
supabase.table("fact_loans").upsert(
    records,
    on_conflict="loan_id"  # Primary key
).execute()
```

## Synthetic Data Generation

### Using generate_sample_data.py

**The script generates realistic Mexican loan data** with proper distributions:

**Features**:

- Spanish names (32 first names × 30 last names = 960 combinations)
- Mexican regions (10 cities: CDMX, Guadalajara, Monterrey, etc.)
- Realistic RFC (Mexican tax ID) generation
- Log-normal amount distribution ($10K-$500K, median ~$75K)
- Normal rate distribution (28%-45%, mean 34%)
- Status distribution: 70% current, 20% delinquent, 5% defaulted, 5% paid_off
- Correlated risk scores (current loans have higher scores)
- Realistic payment histories based on status

**Customization** (edit `scripts/generate_sample_data.py`):

```python
# Adjust amount distribution (line 64)
amount = round(random.lognormvariate(11.5, 0.8), 2)  # Higher median

# Adjust status probabilities (line 76)
status = random.choices(
    ["current", "delinquent", "defaulted", "paid_off"],
    weights=[60, 25, 10, 5],  # More delinquent loans
    k=1
)[0]

# Add custom industries (line 18)
INDUSTRIES = ["Retail", "Manufacturing", "Services", "Agriculture", "Construction"]
industry = random.choice(INDUSTRIES)
```

### Realistic vs. Random Data

**Why use realistic data**:

- KPI calculations depend on proper distributions (e.g., PAR-30 calculation)
- Testing edge cases (defaulted loans, early payoffs)
- Demo purposes (stakeholder presentations)
- Load testing with production-like data volumes

**When to use random data**:

- Unit tests (controlled scenarios)
- Schema validation tests
- Negative testing (invalid data)

## Production Data Import

### Pre-Import Checklist

- [ ] **Backup**: Create database backup before large imports

  ```bash
  pg_dump -h db.your-project.supabase.co -U postgres fact_loans > backup_$(date +%F).sql
  ```

- [ ] **Dry run**: Test import with 100-row sample first

  ```python
  python scripts/run_data_pipeline.py --input sample.csv --mode validate
  ```

- [ ] **PII compliance**: Verify PII masking enabled

  ```bash
  grep "PII_MASKING_ENABLED" .env  # Should be "true"
  ```

- [ ] **Data quality**: Run validation script

  ```python
  python python/validation.py --input data/raw/production_data.csv
  ```

- [ ] **Disk space**: Ensure sufficient space (2× file size)
  ```bash
  df -h  # Check available disk space
  ```

### Import Process

**Step 1: Stage the data**

```bash
# Copy production data to staging directory
cp /path/to/production_loans.csv data/raw/production_$(date +%F).csv

# Verify file integrity
md5sum data/raw/production_*.csv
```

**Step 2: Run validation**

```bash
python scripts/run_data_pipeline.py \
  --input data/raw/production_*.csv \
  --mode validate

# Expected output: "✅ Validation passed"
```

**Step 3: Execute pipeline**

```bash
python scripts/run_data_pipeline.py \
  --input data/raw/production_*.csv \
  --verbose 2>&1 | tee logs/import_$(date +%F_%H-%M).log

# Monitor progress
tail -f logs/import_*.log
```

**Step 4: Verify import**

```sql
-- Check row counts
SELECT COUNT(*) FROM fact_loans;

-- Check date range
SELECT MIN(disbursement_date), MAX(disbursement_date) FROM fact_loans;

-- Check status distribution
SELECT status, COUNT(*) as count,
       ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM fact_loans
GROUP BY status
ORDER BY count DESC;

-- Check for nulls in required columns
SELECT
  SUM(CASE WHEN loan_id IS NULL THEN 1 ELSE 0 END) as null_loan_ids,
  SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts,
  SUM(CASE WHEN disbursement_date IS NULL THEN 1 ELSE 0 END) as null_dates
FROM fact_loans;
```

**Step 5: KPI recalculation**

```bash
# Trigger full pipeline run (includes KPI calculation) for all historical data
python scripts/run_data_pipeline.py --input data/raw/historical_loans.csv

# Verify KPIs populated
psql -h db.your-project.supabase.co -U postgres -c \
  "SELECT date, par_30, default_rate FROM kpi_timeseries_daily ORDER BY date DESC LIMIT 10;"
```

### Rollback Procedure

**If import fails**:

```bash
# Restore from backup
psql -h db.your-project.supabase.co -U postgres < backup_2024-01-15.sql

# Or delete imported data by date range
DELETE FROM fact_loans
WHERE created_at > '2024-01-15 00:00:00';

# Vacuum to reclaim space
VACUUM FULL fact_loans;
```

## Data Migration (External Sources)

### From Spreadsheets (Excel/Google Sheets)

**Excel to CSV**:

```python
import pandas as pd

# Read Excel file
df = pd.read_excel("loans.xlsx", sheet_name="Loans")

# Export to CSV (UTF-8 encoding for Spanish characters)
df.to_csv("data/raw/loans_from_excel.csv", index=False, encoding="utf-8")
```

**Google Sheets to CSV**:

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate (requires service account JSON)
scope = ["https://spreadsheets.google.com/feeds"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open spreadsheet and export
sheet = client.open("Abaco Loans").worksheet("Jan 2024")
df = pd.DataFrame(sheet.get_all_records())
df.to_csv("data/raw/loans_from_sheets.csv", index=False)
```

### From Legacy Systems (APIs)

**Example: REST API extraction**:

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

# Fetch loans from legacy API
base_url = "https://legacy-system.com/api/v1"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

loans = []
page = 1
while True:
    response = requests.get(
        f"{base_url}/loans",
        headers=headers,
        params={"page": page, "per_page": 1000}
    )

    if not response.ok:
        break

    data = response.json()
    loans.extend(data["loans"])

    if len(data["loans"]) < 1000:
        break

    page += 1

# Convert to DataFrame
df = pd.DataFrame(loans)

# Transform to Abaco schema
df_transformed = df.rename(columns={
    "id": "loan_id",
    "customer_name": "borrower_name",
    "principal": "amount",
    "interest_rate": "rate",
    "funded_date": "disbursement_date",
    "due_date": "maturity_date",
    "loan_status": "status"
})

# Save
df_transformed.to_csv(f"data/raw/legacy_migration_{datetime.now():%Y%m%d}.csv", index=False)
```

### From Database Dumps

**PostgreSQL dump to CSV**:

```bash
# Extract loans table from legacy DB
psql -h legacy-db.com -U user -d loans_db -c \
  "COPY (SELECT * FROM loans WHERE created_at >= '2023-01-01') TO STDOUT WITH CSV HEADER" \
  > data/raw/legacy_loans.csv
```

**MySQL dump to CSV**:

```bash
mysql -h legacy-db.com -u user -p loans_db -e \
  "SELECT * FROM loans WHERE created_at >= '2023-01-01' INTO OUTFILE '/tmp/legacy_loans.csv'
   FIELDS TERMINATED BY ','
   ENCLOSED BY '\"'
   LINES TERMINATED BY '\n';"

cp /tmp/legacy_loans.csv data/raw/
```

## Data Quality Checks

### Automated Validation

**Run before every import**:

```python
from python.validation import validate_dataframe
import pandas as pd

df = pd.read_csv("data/raw/import.csv")

# Run validation
is_valid, errors = validate_dataframe(df)

if not is_valid:
    print("❌ Validation failed:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

# Additional custom checks
assert df["amount"].min() > 0, "Negative loan amounts detected"
assert df["rate"].max() <= 1.0, "Interest rates exceed 100%"
assert df["disbursement_date"].max() <= datetime.now().date(), "Future disbursement dates detected"

print("✅ All validation checks passed")
```

### Data Quality Report

**Generate quality report after import**:

```python
import pandas as pd

df = pd.read_csv("data/processed/latest/transformed_loans.parquet")

print("Data Quality Report")
print("=" * 50)

# Completeness
print("\n1. Completeness (% non-null):")
completeness = (1 - df.isnull().sum() / len(df)) * 100
print(completeness.round(2))

# Uniqueness
print(f"\n2. Uniqueness:")
print(f"  Total rows: {len(df)}")
print(f"  Unique loan_ids: {df['loan_id'].nunique()}")
print(f"  Duplicates: {len(df) - df['loan_id'].nunique()}")

# Value distributions
print(f"\n3. Status Distribution:")
print(df["status"].value_counts(normalize=True).mul(100).round(2))

# Outliers
print(f"\n4. Outlier Detection:")
print(f"  Amounts >$1M: {(df['amount'] > 1000000).sum()}")
print(f"  Rates >50%: {(df['rate'] > 0.5).sum()}")
print(f"  Loans >365 days: {((df['maturity_date'] - df['disbursement_date']).dt.days > 365).sum()}")

# PII masking check
print(f"\n5. PII Masking:")
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
print(f"  Unmasked emails: {df['borrower_name'].str.contains(email_pattern, regex=True).sum()}")
```

## Performance Optimization

### Batch Processing

**For large datasets** (>100K rows):

```python
# Process in chunks
chunk_size = 10000
for chunk in pd.read_csv("large_file.csv", chunksize=chunk_size):
    # Validate chunk
    is_valid, _ = validate_dataframe(chunk)
    if not is_valid:
        continue

    # Insert chunk
    records = chunk.to_dict(orient="records")
    supabase.table("fact_loans").insert(records).execute()

    print(f"Processed {len(records)} rows")
```

### Parallel Processing

**Use multiprocessing for CPU-bound tasks**:

```python
from multiprocessing import Pool
import pandas as pd

def process_chunk(chunk):
    # Validation, transformation, etc.
    return chunk

# Split DataFrame into chunks
chunks = np.array_split(df, 8)  # 8 cores

# Process in parallel
with Pool(processes=8) as pool:
    results = pool.map(process_chunk, chunks)

# Combine results
df_processed = pd.concat(results)
```

### Database Indexing

**Speed up queries after import**:

```sql
-- Create indexes on commonly queried columns
CREATE INDEX IF NOT EXISTS idx_loans_status ON fact_loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_disbursement_date ON fact_loans(disbursement_date);
CREATE INDEX IF NOT EXISTS idx_loans_region ON fact_loans(region);

-- Composite index for date range queries
CREATE INDEX IF NOT EXISTS idx_loans_date_status
ON fact_loans(disbursement_date, status);

-- Refresh statistics for query planner
ANALYZE fact_loans;
```

## Troubleshooting

### Common Import Errors

**Error: "Column not found"**

- **Cause**: CSV header doesn't match expected schema
- **Fix**: Check column names in `python/validation.py` required columns list

**Error: "Invalid date format"**

- **Cause**: Dates not in ISO 8601 format (`YYYY-MM-DD`)
- **Fix**: Convert dates before import:
  ```python
  df["disbursement_date"] = pd.to_datetime(df["disbursement_date"]).dt.strftime("%Y-%m-%d")
  ```

**Error: "Duplicate key value violates unique constraint"**

- **Cause**: `loan_id` already exists in database
- **Fix**: Use upsert or filter duplicates (see "Handling Duplicates" section)

**Error: "Out of memory"**

- **Cause**: Attempting to load entire large CSV into memory
- **Fix**: Use chunked reading (see "Batch Processing" section)

### Data Anomalies

**Anomaly: "PAR-30 = 0% after import"**

- **Check**: Verify `days_past_due` calculated correctly
- **Fix**: Recalculate DPD by running the full pipeline:
  ```bash
  python scripts/run_data_pipeline.py --input data/raw/imported_loans.csv
  ```

**Anomaly: "All loans show 'current' status"**

- **Check**: Status field mapped correctly during import
- **Fix**: Review business rules in `config/business_rules.yaml`

## Additional Resources

- **Pipeline documentation**: [DEVELOPMENT.md](./DEVELOPMENT.md)
- **Schema reference**: [DATA_DICTIONARY.md](./DATA_DICTIONARY.md)
- **API integration**: [API_SECURITY_GUIDE.md](./API_SECURITY_GUIDE.md)
- **Deployment**: [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)

---

**Last Updated**: 2026-02-02  
**Maintained By**: Data Engineering Team  
**Review Frequency**: After schema changes or major imports
