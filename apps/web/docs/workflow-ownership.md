# Workflow Ownership and Runbook

This document keeps workflow steps, roles, and review requirements in one place. Update it whenever a workflow or owner changes.

## Workflows in scope

- CI: `.github/workflows/ci-main.yml` (apps/web lint/build/type-check)
- Deploy: `.github/workflows/deploy.yml` (Vercel deploy; Supabase env injection)
- Data: `.github/workflows/daily-ingest.yml`, `.github/workflows/demo-scripts.yml` (scripts/demo execution + Slack)
- Security/Quality: `.github/workflows/dependency-submission.yml`, `.github/workflows/sonarqube.yml`, `.github/workflows/snyk.yml`
- Review bots: `.github/workflows/coderabbit-pr-review.yml`, `.github/workflows/gemini-pr-review.yml`, `.github/workflows/perplexity-review.yml`
- Notifications: `.github/workflows/slack_notify.yml`

## Secrets and environment

- Supabase: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE`, `SUPABASE_TOKEN`
- Deploy: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
- Compliance/alerts: `SLACK_TOKEN` / `SLACK_WEBHOOK_URL`
- QA/Security: `SONAR_TOKEN`, `SENTRY_AUTH_TOKEN`, `CODECOV_TOKEN`, `SNYK_TOKEN`
- Keep secrets server-side only; do not expose service-role keys to clients.

## Ownership and review

- Pipeline/Deploy owner: Maintains `deploy.yml`, Vercel secrets, Supabase env mapping. Required reviewer for deploy workflow/secrets changes.
- Data/Analytics owner: Maintains ingestion/transformation/KPI code and data workflows (`daily-ingest.yml`, `demo-scripts.yml`). Reviews schema/compliance changes.
- Security/Compliance owner: Reviews use of secrets, PII masking, audit/report logic, and security workflows (`dependency-submission.yml`, `sonarqube.yml`, `snyk.yml`).
- Frontend owner: Reviews CI steps affecting apps/web (`ci-main.yml`, lint/type-check/build commands).

## Update and review process

- Any change to `.github/workflows/*.yml` requires approval from the relevant owner(s) above.
- Changes that add or use secrets must include owner sign-off and a short justification in the PR description.
- Keep this document versioned; when ownership or workflow scope changes, update this file in the same PR.

## Context for PRs

- Always include: which workflow is affected, secrets touched, and expected runtime commands.
- Link to related manifests/audit docs (e.g., compliance reports, pipeline manifests under `logs/runs/`).
