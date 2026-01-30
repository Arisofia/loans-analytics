# Security Policy

> **⚠️ Deprecated Integrations (Retired 2026-01)**
>
> The following integrations have been fully retired: Slack, HubSpot, Notion, Cascade, Looker.
> Environment variables referencing these services are no longer required.
> Current stack: Python + Polars pipelines, Streamlit dashboards, Supabase/Postgres, Grafana.

## Required Secrets

- `GEMINI_API_KEY_SIMPLE`: Gemini PR review
- `PERPLEXITY_API_KEY`: Perplexity review

## Workflow Logic

- All workflows linted and scanned for secrets before merge.
- Actions pinned to tags or SHAs.

## Escalation

- Contact: <security@yourdomain.com>
- Rotate secrets quarterly or on role change.
