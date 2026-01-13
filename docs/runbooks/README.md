# Incident Runbooks

This folder contains short, action-oriented runbooks for the most common production incident scenarios.

## Runbooks

- [Dashboard Down](dashboard-down.md)
- [App Service Diagnostics](app-service-diagnostics.md)
- [Pipeline Failure](pipeline-failure.md)
- [Deployment Blocked](deployment-blocked.md)

## How to use

1. Start at the **Triage** section.
2. Follow the decision flowchart.
3. Capture the evidence listed (logs/URLs/error snippets) and paste it into the incident ticket.

## Conventions

- “Dashboard” = Azure App Service Streamlit app deployed from `dashboard/`.
- “Web app” = Next.js app in `apps/web/` (deployed via SWA workflows).
- “Pipelines” = GitHub Actions scheduled/dispatch workflows that run Python/Node ingestion jobs.
