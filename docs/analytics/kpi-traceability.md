# KPI Traceability, Dashboards, and GitHub Workflow Playbook

This playbook keeps every KPI, dashboard, and visualization traceable end-to-end so decisions stay actionable, auditable, and secure.

## Roles and decision rights

- **KPI Owner**: Defines success criteria, thresholds, and next-best actions; approves changes to definitions and dashboards.
- **Data Steward**: Guarantees schema contracts, freshness SLAs, and PII masking; owns lineage documentation and data quality alerts.
- **Analytics Lead**: Designs dashboard narrative, drill-down tables, and experiments; ensures KPIs map to business objectives and runbooks.
- **Engineering (PR Assignee)**: Implements changes, ships tests, and updates observability; assigns PRs to `@codex`, requests reviews from `@coderabbit` and `@sourcery`, and ensures SonarCloud gates are green.
- **Risk & Compliance**: Reviews PII/PCI impact, verifies audit logging, and signs off on retention or export changes.

## Traceability and measurement

1. **Definition source of truth**: Update `docs/analytics/KPIs.md` with owner, formula, thresholds, and linked runbook before coding.
2. **Data lineage**: Document table/contract, upstream system, and refresh cadence in the PR description; add data-quality checks (freshness, null %, duplicates, schema drift).
3. **Dashboard contract**: Each chart records owner, drill-down table, alert channel, and runbook link in `docs/analytics/dashboards.md`.
4. **Versioned artifacts**: Tag dashboard releases or dbt model versions in PRs; keep a changelog entry when thresholds or filters change.
5. **Observability**: Emit metrics for data freshness, query latency, and alert MTTR/MTTD; route alerts to Slack/email configured via `NEXT_PUBLIC_ALERT_*`.

## GitHub workflow (standardized)

1. Branch naming: `feature/kpi-*`, `fix/dashboard-*`, or `chore/data-*` with issue reference.
2. PR template: fill KPI impact, data/PII touched, tests, and alert updates; link dashboards and runbooks touched.
3. Assign and reviewers: set assignee to `@codex`; request reviews from `@coderabbit` and `@sourcery`, and confirm SonarCloud/SAST gates are green. The workflow `.github/workflows/pr-auto-assign.yml` applies this automatically on open/sync; rerun the workflow if the state drifts.
4. Checks: require CodeQL, SonarCloud, and CI (web + analytics) to pass; block merge on coverage or data-quality regression.
5. Auditability: attach screenshots of dashboard changes and include query hashes or dataset versions in the PR for reproducibility.

## Step-by-step change recipe

1. **Frame intent**: Describe KPI objective, owner, and decision it will drive; state acceptance criteria.
2. **Design**: Map fields and filters; specify drill-down table, alert thresholds, and runbook link.
3. **Implement**: Add ingestion/transform, tests, and dashboard component; ensure PII is masked and logging is sanitized.
4. **Validate**: Run CI, data-quality checks, and alert simulations; paste results in PR.
5. **Release**: Update docs (`KPIs.md`, `dashboards.md`, runbooks), tag versions, and ensure alert webhooks are configured.
6. **Learn**: Capture postmortem entries for breaches or model drift, recording MTTR/MTTD and remediation steps.

## Compliance, security, and audit

- No secrets or API keys in the repo; rely on vault/Actions secrets and rotate regularly.
- Enforce least privilege for data sources; log access and mutations with immutable storage.
- Mask PII in exports, logs, and dashboards; redact before sharing downstream.
- Maintain retention schedules per table; document deletion/DSAR handling in runbooks.
- Keep SBOM/dependency scans in CI and document exceptions with owner approval.

## Dashboard evidence checklist

- KPI formula + threshold linked to owner and runbook.
- Data source, refresh SLA, and schema version documented.
- Drill-down table URL and alert channel validated.
- Screenshot or Loom linked in PR to prove UX and filtering behavior.
- Post-release review scheduled to confirm decisions made and hypotheses learned.
