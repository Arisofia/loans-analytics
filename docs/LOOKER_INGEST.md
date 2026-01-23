# Looker + EEFF Ingest (Cascade Disabled)

This workflow runs the unified pipeline using Looker exports while Cascade ingestion is offline.

## Required Files

- `data/archives/looker_exports/loan_par_balances.csv` (preferred PAR snapshot)
- `data/archives/looker_exports/loans.csv` (fallback when PAR balances are missing)
- `data/archives/financial_statements/*` (optional EEFF exports; CSV/XLSX/XLS)

## Looker Mapping (PAR Balances)

The ingestion layer converts Looker PAR balances into the loan tape schema expected by the pipeline:

- `reporting_date` -> `measurement_date`
- `outstanding_balance_usd` -> `total_receivable_usd`
- `par_90_balance_usd` -> `dpd_90_plus_usd`
- `par_60_balance_usd` -> `dpd_60_90_usd` (net of PAR90)
- `par_30_balance_usd` -> `dpd_30_60_usd` (net of PAR60)
- `par_7_balance_usd` -> `dpd_7_30_usd` (net of PAR30)
- `total_receivable_usd` - `par_7_balance_usd` -> `dpd_0_7_usd`

If `loan_par_balances.csv` is missing, the pipeline can fall back to `loans.csv` and bucket balances by `dpd`.

### Example PAR CSV Format

```csv
reporting_date,outstanding_balance_usd,par_0_balance_usd,par_7_balance_usd,par_30_balance_usd,par_60_balance_usd,par_90_balance_usd
2025-12-31,5000000,4200000,500000,200000,80000,20000
```

## EEFF Mapping (Financial Statements)

EEFF files are optional. If present, the ingestion step maps financial statement metrics into the snapshot using the `pipeline.phases.ingestion.looker.financials_*` settings in `config/pipeline.yml`.

Supported metrics (canonical keys):

- `cash_balance_usd`
- `total_assets_usd`
- `total_liabilities_usd`
- `net_worth_usd` (computed if assets and liabilities exist)
- `net_income_usd`
- `runway_months`
- `debt_to_equity_ratio` (computed if liabilities and net worth exist)

Two formats are supported:

1) **Wide format** (one row per date, metrics in columns)

```csv
reporting_date,cash_balance_usd,total_assets_usd,total_liabilities_usd,net_income_usd
2025-12-31,120000,800000,500000,15000
```

1) **Long format** (one row per metric)

```csv
reporting_date,metric,value
2025-12-31,Total Assets,800000
2025-12-31,Total Liabilities,500000
2025-12-31,Cash Balance,120000
```

If no date column exists, the pipeline uses the file modification date (configurable).

`cash_balance_usd` is used to populate `cash_available_usd` for CollectionRate calculations.

## Configuration

### config/pipeline.yml

```yaml
pipeline:
  phases:
    ingestion:
      source: looker
      looker:
        loans_par_path: data/archives/looker_exports/loan_par_balances.csv
        loans_path: data/archives/looker_exports/loans.csv  # fallback
        financials_path: data/archives/financial_statements/
        financials_format: auto  # auto|wide|long
        financials_date_column: reporting_date
        financials_null_policy: skip  # skip|fill_last|error
```

### Environment-Specific Override

In `config/environments/development.yml`:

```yaml
pipeline:
  phases:
    ingestion:
      looker:
        loans_par_path: ${DATA_DIR:-data/raw}/looker_exports/loan_par_balances.csv
        financials_path: ${DATA_DIR:-data/raw}/financial_statements/
```

## Run the Pipeline

### Default (Uses Config)

```bash
PIPELINE_ENV=development python scripts/run_data_pipeline.py \
  --input data/raw/looker_exports/loan_par_balances.csv
```

### Override PAR Path

```bash
python scripts/run_data_pipeline.py \
  --input /path/to/custom/loans_par.csv \
  --financials-path /path/to/financials/
```

### Dry-Run (Validate Config + Files)

```bash
python scripts/run_data_pipeline.py \
  --input data/raw/looker_exports/loan_par_balances.csv \
  --dry-run
```

This validates:

- ✓ File paths exist
- ✓ CSV schema matches expectations
- ✓ Looker columns map to pipeline schema
- ✓ Financial metrics are recognized

## Ingestion Architecture

The `ingest_looker()` function in `src/pipeline/ingestion.py`:

1. **Validate PAR file** — Check for required columns, null percentages, date range
2. **Map PAR columns** — Convert Looker naming to pipeline schema (`par_90_balance_usd` → `dpd_90_plus_usd`)
3. **Load financial statements** (if provided)
   - Auto-detect format (wide vs. long) from structure
   - Map financial metric names to canonical keys
   - Merge with PAR snapshot on `measurement_date`
4. **Archive raw files** — Copy to `data/archive/looker/{date}/` with metadata
5. **Emit snapshot** — Output normalized loan tape ready for staging layer

## Ingestion Metadata (Legacy Helpers)

The legacy helpers used by `scripts/run_data_pipeline.py` enrich ingested rows with run metadata:

- `_ingest_run_id` — unique run identifier for the ingestion call
- `_ingest_timestamp` — ISO 8601 UTC timestamp for the ingestion call

If you need strict schema enforcement for local CSVs, initialize
`UnifiedIngestion(..., strict_validation=True)` to fail fast when required numeric
columns are missing (the ingest returns an empty frame and records an error).

## Troubleshooting

### Missing PAR File (Uses Fallback)

If `loan_par_balances.csv` not found, pipeline attempts `loans.csv`:

```text
[INFO] loan_par_balances.csv not found; using fallback loans.csv
[INFO] Bucketing loans by dpd column into PAR bands
```

If both missing:

```text
[ERROR] Neither loan_par_balances.csv nor loans.csv found
[ERROR] Ingestion failed; check config.pipeline.phases.ingestion.looker.loans_par_path
```

**Solution**: Ensure files exist or verify paths in `config/pipeline.yml`.

### Financial Statement Format Unrecognized

```text
[WARNING] financials_format=auto; detected LONG format
[WARNING] Metric "Total Cash" not in canonical keys; skipping
```

**Solution**: Check metric names in your EEFF file against canonical keys list above. Use `--dry-run` to preview mapping.

### Date Mismatch (PAR ≠ Financial)

```text
[WARNING] Financial reporting_date (2025-11-30) differs from PAR date (2025-12-31)
[WARNING] Using PAR date as measurement_date; financial metrics tagged with source_date
```

**Solution**: Ensure PAR and financial statements have same reporting_date, or manually sync dates before ingestion.

### Null Handling in Financials

By default, missing metrics are skipped (not populated in snapshot):

```text
[INFO] Total Liabilities missing; skipping debt_to_equity computation
```

To fail on nulls:

```yaml
pipeline:
  phases:
    ingestion:
      looker:
        financials_null_policy: error  # fail if any metric missing
```

## Output

After successful ingestion:

- **Loan tape** — Normalized snapshot at `data/staging/loan_tape/{date}/`
- **Archive** — Raw files preserved at `data/archive/looker/{date}/`
- **Metadata** — Ingestion log with row counts, null stats, schema validation results

Example output structure:

```text
data/
├── staging/
│   └── loan_tape/
│       └── 2025-12-31/
│           ├── snapshot.parquet  (normalized loans with dpd bands)
│           └── metadata.json      (schema, row count, validation results)
├── archive/
│   └── looker/
│       └── 2025-12-31/
│           ├── loan_par_balances.csv  (original)
│           ├── financial_statements.xlsx
│           └── ingestion_manifest.json
```

## Next Steps

After Looker ingestion completes:

1. **Validate staging** — Run `python scripts/validate_staging.py` to check data quality
2. **Transform to marts** — Execute dbt models: `dbt run --select tag:looker_dependent`
3. **Update dashboards** — Refresh Streamlit dashboard to show new KPIs
4. **Monitor freshness** — Set up alerts if new PAR files don't arrive by expected time
5. **Plan Cascade migration** — Once Cascade comes online, gradual cutover to `ingest_cascade()` source
