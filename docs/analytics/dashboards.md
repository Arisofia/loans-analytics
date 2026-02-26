# Dashboards & Drill-downs

Principles: every chart links to a drill-down table, owner, runbook, SLA, and next-best action. Alerts include KPI owner and remediation link.

## Exec Dashboard

- Metrics: NSM, NPL/PAR trend, book growth vs target, CAC/LTV, approval rate, ECL vs plan.
- Drill-downs: delinquency cohorts, channel profitability, approval funnel.
- Alerts: NPL/PAR breach → `runbooks/kpi-breach.md`; data freshness breach → `runbooks/ingestion-failure.md`.

## Streamlit Executive Dashboard (ABACO Financial Intelligence)

- Local URL: `http://localhost:8501`
- Deployed URL: `https://abaco-analytics-dashboard.azurewebsites.net`
- Grafana URL: `http://localhost:3001/dashboards`
- Strategic report output: `reports/strategic/strategic_report_latest.md`
- Generation command: `make report-strategic`
- Data sources: pipeline outputs under `data/metrics/` and dashboard exports under `exports/`.
- KPI tiles: 52 KPIs from `analytics_facts.csv` plus scalar KPIs from `complete_kpi_dashboard.json` in the exports directory.
- Cashflow: uses `recv_revenue_for_month`, `recv_interest_for_month`, `recv_fee_for_month`, and `sched_revenue`.
- Agent info: sales agent volume from loan data when `sales_agent` exists, otherwise headcount from `data/support/headcount.csv`.
- KPI exports: use the sidebar "Generate KPI exports" button to regenerate `exports/complete_kpi_dashboard.json` and `exports/analytics_facts.csv` from data.
- Historical page: `streamlit_app/pages/6_Historical_Context.py`
- Historical page scope: trend direction/strength, seasonality factors, and forecast confidence bands
  powered by `python/multi_agent/historical_context.py`.

## Risk Ops Dashboard

- Metrics: roll-rate matrix, PD/LGD calibration, exceptions aging, auto-decision rate, TAT.
- Drill-down: cell-level loan list, rule hits, manual review queue, latency per step.
- Next-best actions: tighten/loosen rules, re-route manual reviews, retrain model (with version link).
- Alerts: calibration drift or auto-decision drop → `runbooks/kpi-breach.md`; schema drift → `runbooks/schema-drift.md`.

## Collections Dashboard

- Metrics: cure rate, promise-to-pay kept, agent productivity, queue health.
- Drill-down: borrower/agent table per segment; promises schedule with outcomes.
- Next-best actions: contact cadence change, settlement offers, reassign agent.
- Alerts: promise kept < target or cure rate drop → `runbooks/kpi-breach.md`.

## Product Funnel Dashboard

- Metrics: upload/ingest success, parsing errors, conversion by segment, drop-off by step.
- Drill-down: failed rows with reasons, feature flag state, device/channel breakdown.
- Alerts: ingest failure spikes → `runbooks/ingestion-failure.md`; schema drift → `runbooks/schema-drift.md`.

## Data Quality Dashboard

- Metrics: freshness, completeness, duplicates, schema drift, PII checks.
- Drill-down: failed expectations, column-level stats, offending rows (masked PII).
- Alerts: any red check → `runbooks/schema-drift.md` or `runbooks/ingestion-failure.md`.

## Alert routing

- Severity tags: Red = page owner + backup; Amber = owner notification.
- Every alert message: KPI, threshold, current value, owner, runbook link, next-best action, ETA/SLA.
