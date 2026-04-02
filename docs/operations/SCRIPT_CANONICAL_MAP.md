# Script Canonical Map

Single source of truth for script execution paths. Use only these commands.

## Data Pipeline

- Run pipeline (CSV): `python3 scripts/data/run_data_pipeline.py --input data/raw/loan_data.csv`
- Run pipeline (Google Sheets): `python3 scripts/data/run_data_pipeline.py --input gsheets://DESEMBOLSOS`
- Analyze real input files: `python3 scripts/data/analyze_real_data.py --data-dir ~/Downloads`

## Google Sheets & Targets

- Setup guide: See `docs/GOOGLE_SHEETS_SETUP.md`
- Credentials: `credentials/google-service-account.json` (gitignored; provide your own)
- Configuration: `config/pipeline.yml` (google_sheets and targets sections)
- Data spreadsheet: `1JbbiNC495Nr4u9jioZrHMK1C8s7olvTf2CMAdwhe-6o`

## Zero-Cost ETL (DuckDB + Parquet — replaces Azure)

> These are the canonical entry points for the zero-cost stack. Use `make` targets when available.

- Full pipeline (ingest + schema + snapshot): `make run`
- Tests only: `make test`
- Ingest only (loan tape or Control de Mora): `make etl-local INPUT=data/raw/<file>.csv`
- Initialise DuckDB star schema: `make zero-cost-schema`
  _(Equivalent: `python3 scripts/data/init_duckdb_schema.py`)_
- Build monthly snapshot: `make snapshot-build MONTH=2026-02-28`
  _(Equivalent: `python3 scripts/data/build_snapshot.py --month 2026-02-28`)_
- Local stack (API + dashboard via Docker): `make zero-cost-up`
- Stop local stack: `make zero-cost-down`

## Maintenance

- Service status report: `python3 scripts/maintenance/generate_service_status_report.py`
- Validate migration index: `python3 scripts/maintenance/validate_migration_index.py`

## ML Training

- Train default risk model: `python3 scripts/ml/train_default_risk_model.py`
- Train WoE/IV scorecard: `python3 scripts/ml/train_scorecard.py`
- Train scorecard only when raw CSV files are ready and persist run metadata: `python3 scripts/ml/train_scorecard_if_ready.py`
- Retrain pipeline: `python3 scripts/ml/retrain_pipeline.py`

## Monitoring

- Auto-start monitoring stack: `bash scripts/monitoring/auto_start_monitoring.sh`
- Monitoring health check: `bash scripts/monitoring/health_check_monitoring.sh`
- Harden RLS on sensitive tables: `DATABASE_URL=... bash scripts/monitoring/harden_rls_sensitive_tables.sh`

## Reporting & Frontend Sync

- Sync latest pipeline outputs to Supabase KV for React frontend: `python3 scripts/reporting/sync_to_supabase.py`

## Validation

- Validate migration order: `python3 scripts/validation/validate_migration_order.py`
- Validate port consistency: `python3 scripts/validation/validate_port_consistency.py`
- Validate full-suite CI baseline: `python3 scripts/validation/check_full_suite_baseline.py --baseline .github/ci-baselines/full-suite-baseline.json --report artifacts/full-suite-report.json`
- Validate doc links: `python3 tools/validate_doc_links.py`

## Performance

- API load test (Locust): `locust -f tests/load/locustfile.py --headless -u 30 -r 5 -t 5m --host http://localhost:8000`

## Rule

- Avoid root-level wrappers and any duplicate command entrypoints.
- Keep one active implementation path per task under `scripts/{data,maintenance,monitoring,deployment,evaluation}`.

## Rules

- **Single Source of Truth**: This map is the canonical reference for all CLI execution commands.
- **No Duplication**: Command examples in README, docs, and tutorials reference this map instead of repeating.
- **Avoid Wrappers**: No root-level scripts that wrap these canonical paths.
- **One Path Per Task**: Keep one active implementation per task under `scripts/{data,maintenance,monitoring,deployment,evaluation}`.
- **Documentation**: Product/operational docs mention "See SCRIPT_CANONICAL_MAP.md for commands" rather than embedding large command blocks.

## Cross-Document Reference Pattern

When documenting a feature, use this pattern:

```markdown
For [feature] execution commands, see **[Canonical Script Map - [Section]](./SCRIPT_CANONICAL_MAP.md#[anchor])**

**Quick example:**
\`\`\`bash
[one example command]
\`\`\`
```

This keeps docs DRY while ensuring all commands stay synchronized.

## Maintenance

When adding new commands:
1. Add to appropriate section in this map
2. Note in commit: "Add canonical command for [feature]"
3. Update docs to reference this map (no inline command blocks)
4. Archive old command references in comments if needed for reference

