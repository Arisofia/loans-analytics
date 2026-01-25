# Q1 2026 OKRs — Abaco Loans Analytics

## Engineering

Objective 1: Stabilize CI and reduce flaky test runs

- KR1: Fix Playwright workflow so scheduled & PR runs succeed (target: 100% of reruns spawn jobs)
- KR2: Resolve the top 30 ShellCheck warnings that cause functional risk
- KR3: Add CI gating to prevent empty/invalid workflows (validate on PR)

Objective 2: Improve analytical reproducibility

- KR1: Add a reproducible KPI run that can be executed locally and in CI
- KR2: Increase unit test coverage for KPI functions to > 90% for core KPI modules

## Analytics

Objective: Ensure KPI definitions are clear and auditable

- KR1: Publish `config/kpis/kpi_definitions.yml` with schema and usages
- KR2: Provide baseline JSON (`tests/fixtures/baseline_kpis.json`) and CI check for +/- 5% drift

## Product & Design

Objective: Ship a validated KPI dashboard for pilots

- KR1: Embed analytics file and add export guide
- KR2: Fix all dashboard binding regressions blocking Playwright smoke tests

## DevOps / Platform

Objective: Improve CI reliability and observability

- KR1: Add health checks or alerts for scheduled runs failing with no jobs
- KR2: Ensure action versions are kept up-to-date for critical in-repo actions (add auto-bump PRs)

## Growth & Ops

Objective: Operationalize KPI exports

- KR1: Automate monthly KPI dashboard export to `exports/complete_kpi_dashboard.json`
