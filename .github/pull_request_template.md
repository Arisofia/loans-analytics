# Summary

- [ ] KPI impact: which KPIs/dashboards are affected? Link to `docs/analytics/KPIs.md`.
- [ ] Data sources touched: tables/contracts/migrations updated?
- [ ] Data/PII touched: list fields or confirm none; logging sanitized?
- [ ] Tests: unit/integration/e2e run? attach results.
- [ ] Security/compliance: secrets handled safely, PII masked, audit/logging impact noted.
- [ ] Env/alerts: required env vars set/updated (`NEXT_PUBLIC_ALERT_*`, webhooks, emails)?
- [ ] Runbooks/alerts: updated links or thresholds? next-best actions still valid?
- [ ] Workflow hygiene: PR assigned to `@codex` and reviewers `@sonarqube`, `@coderabbit`, `@sourcery` (auto-assignment workflow runs on open/update).
- [ ] Ownership: reviewers tagged per `docs/workflow-ownership.md` (Workflow/Secrets, Data/Analytics, Security/Compliance, Frontend as applicable).

# Checklist

- [ ] CI passed (lint, type-check, tests, build for web/analytics).
- [ ] SonarCloud coverage/quality gate OK.
- [ ] CodeQL/secret scanning OK.
- [ ] Docs updated (dashboards, runbooks, compliance) if applicable.
