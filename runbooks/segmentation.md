# Segmentation KPI Runbook

🔧 Purpose

This runbook documents operational notes for the SegmentationSummary KPI (primary metric: total unique clients in 2025). It explains inputs, how to run and validate the metric, troubleshooting steps, and escalation contacts.

Owner & Contacts

- Owner: Commercial Analytics / KPIAnalyticsAgent

Sources & Inputs

- Primary sources: `fact_loans` (loan rows), `customers` (customer metadata)
- Config pointer: `config/pipeline.yml` -> `pipeline.calculation.metrics` -> `SegmentationSummary`
- Implementation: `src/kpis/segmentation_summary.py` → `calculate_segmentation_summary`
- Expected manifest output: `manifest['metrics']['SegmentationSummary']` and `manifest['metadata']['segmentation_data']` (or `context.segmentation_data`) in run manifest under `logs/runs/<run_id>/*_manifest.json`

When to run

- Automatically: runs as part of the scheduled pipeline / `run_complete_analytics.py` and Prefect flow.
- Manually: for debugging or ad-hoc checks.

Quick local validation

- Unit tests: `pytest tests/test_segmentation_summary.py -q`
- Small smoke run (Python REPL):

```bash
python - <<'PY'
import pandas as pd
from src.kpis.segmentation_summary import calculate_segmentation_summary

data = {
  'Customer ID': [1,2,3],
  'Client Segment': ['A','A','B'],
  'Outstanding Amount':[1000,2000,1500],
  'Approved Amount':[1100,2100,1600],
  'Origination Date':['2025-01-01','2025-02-02','2025-03-03']
}
df = pd.DataFrame(data)
print(calculate_segmentation_summary(df))
PY
```

Expected behaviour & alerts

- Primary metric (total unique clients) should be > 0 when there is data for 2025.
- If `segmentation_data` is missing or empty for a non-empty dataset, trigger an investigation.
- Suggested alert thresholds:
  - Missing segments entirely after a successful run → **Critical**
  - Delinquency rate per segment > 20% → **Warning**

Troubleshooting

1. Manifest missing `segmentation_data`:
   - Check logs under `logs/runs/<run_id>/` for pipeline errors.
   - Ensure `UnifiedOutput.persist` wrote `metrics` and `files` and that `manifest` exists.
2. Unexpected zero or low client counts:
   - Validate ingestion (look for mapping errors, date parsing, or filtering to 2025).
   - Confirm `measurement_date` and `origination_date` logic; verify timezone conversions.
3. High delinquency rates per segment:
   - Drill down into `segmentation_data` rows and raw loan rows; validate `Days Past Due` mapping.
   - Check if there was a data ingestion change that altered dpd or receivable columns.

Remediation steps

- Re-run the pipeline for a specific artifact: `python scripts/run_data_pipeline.py --input <file>` (or trigger Prefect flow via `apps/analytics/api/main.py` endpoint locally).
- If data issues: open a data-quality issue, tag `@data-engineering`, add failing row samples and repeat the run after fixes.
- If a code bug: create a small unit test reproducing the issue and open a PR with the fix.

Postmortem & audit

- For any outage or metric regression, capture: run_id, failing rows, diff vs previous run, and actions taken.
- Update this runbook with the root cause and any permanent fixes, and add regression tests where applicable.

Notes

- Keep the authoritative definition in `config/pipeline.yml`; keep runbook operational (process + troubleshooting) only.
- For dashboarding instructions and design notes (Figma layout), see `docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md` and `src/integrations/figma_client.py`.
