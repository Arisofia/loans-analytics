# Security Policy

> **⚠️ Deprecated Integrations (Retired 2026-01)**
>
> The following integrations have been fully retired: Slack, HubSpot, Notion, Cascade, Looker.
> Environment variables referencing these services are no longer required.
> Current stack: Python + Polars pipelines, Streamlit dashboards, Supabase/Postgres, Grafana.

## Required Secrets

- `GEMINI_API_KEY_SIMPLE`: Gemini PR review
- `PERPLEXITY_API_KEY`: Perplexity review

## Supabase Secrets

- `SUPABASE_URL`: The URL of your Supabase project.
- `SUPABASE_ANON_KEY`: The anonymous/public API key.
- `SUPABASE_SERVICE_ROLE_KEY`: The service role key for server-side operations.

**Policy:**

- **Never commit secrets to Git.** All secrets, especially `SUPABASE_SERVICE_ROLE_KEY`, must be stored as environment variables or in a secure secrets manager.
- For local development, use a `.env.local` file (which is gitignored).
- For production/CI, use GitHub Actions secrets or your deployment platform's secret management.

## Workflow Logic

- All workflows linted and scanned for secrets before merge.
- Actions pinned to tags or SHAs.

## Escalation

- Contact: <security@yourdomain.com>
- Rotate secrets quarterly or on role change.
