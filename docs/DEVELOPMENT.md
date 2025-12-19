
## Setup

1. **Clone & Install**

   ```bash
   git clone <repo>
   cd nextjs-with-supabase
   npm ci
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env.local
   ```

   - Get credentials from [Supabase Dashboard](https://supabase.com/dashboard)
   - Add to `.env.local`

3. **Start Development**
   ```bash
   npm run dev
   ```

## Environment Variables & Observability

### Local `.env.local`

- Always copy `apps/web/.env.example` to `.env.local` and keep this file out of source control (`.env.local` is ignored).
- Populate the values before running `npm run dev` so that Supabase, Slack alerts, Sentry, and drill-down links load.
- After editing, restart the dev server and verify that Supabase rows are readable and that the analytics dashboard renders without the "not set" warnings for alerts or drill-downs.

### Frontend variables (apps/web)

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL used by the client and integration helpers. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public (read-only) API key consumed by the React app. Keep this scoped to the client role in Supabase. |
| `NEXT_PUBLIC_SUPABASE_FN_BASE` | Root of Supabase Edge Functions (`https://<project>.functions.supabase.co`). Required by `IntegrationSettings` and synchronization helpers. |
| `NEXT_PUBLIC_DRILLDOWN_BASE_URL` | Base URL for drill-down exports and analytics tables (can point at Supabase Studio, Supabase Edge App, or another analytics surface). |
| `NEXT_PUBLIC_ALERT_SLACK_WEBHOOK` | Optional Slack webhook so the analytics dashboard can dispatch KPI alerts directly to a channel. |
| `NEXT_PUBLIC_ALERT_EMAIL` | Contact email shown alongside alerts (defaults to `alerts@abaco.loans`). |
| `NEXT_PUBLIC_SITE_URL` | Canonical site URL used for metadata, Open Graph, and robots. |
| `NEXT_PUBLIC_SENTRY_DSN` | DSN for Sentry error tracking on both client and server. |

### Shared integration & automation variables

| Variable | Purpose |
| --- | --- |
| `SLACK_WEBHOOK_URL` | Incoming webhook used by `.github/workflows/daily-ingest.yml` to signal successful pipelines. |
| `SLACK_BOT_TOKEN` | Token powering `services/slack_bot` plus the `slack_notify.yml` workflow that posts deployment/failure updates. |
| `SLACK_SIGNING_SECRET` | Slack signing secret required by the Bolt app. |
| `SLACK_CHANNEL` | Target channel for `slack_notify.yml` and for manual Slack bot posts. |
| `SLACK_BOT_AUTOSTART` | Set to `false` to prevent the Slack bot from auto-starting in non-production environments. |
| `KPI_WEBHOOK_URL` | Endpoint the Slack bot consults to load the latest KPIs before responding to mentions. |
| `API_KEY` | Shared bearer token appended to internal KPI and HubSpot calls. |
| `HUBSPOT_API_KEY` | HubSpot CRM sync key used in `services/hubspot_sync`. |
| `KPI_SERVICE_URL` | URL of the KPI microservice that enriches HubSpot contacts/deals. |
| `PIPELINE_INPUT_FILE` | Optional override for `scripts/run_data_pipeline.py` to point at a different CSV. |
| `GITHUB_TOKEN` / `GH_TOKEN` | Grant access to the GitHub API for scripts such as `scripts/pr_status.py` and `scripts/trigger_workflows.py`. |
| `NOTION_DATABASE_ID` | Notion database used by `scripts/import_notion_metrics.py`. |
| `NOTION_META_TOKEN` | Bearer token supporting the Notion Importer. |
| `NOTION_VERSION` | Notion API version (defaults to `2022-06-28` if unset). |
| `OPENAI_API_KEY` | Enables OpenAI-powered summaries inside the Streamlit app and other agents. |
| `GOOGLE_API_KEY` | Required by the Gemini client in `scripts/clients.py`. |
| `GROK_API_KEY` | Required by the Grok client used by `StandaloneAIEngine`. |
| `DATABASE_URL` | Connection string used by `python/agents/orchestrator.py` and other automation helpers. |
| `LOG_LEVEL` | Sets the logging verbosity for the Notion importer (defaults to `INFO`). |

### Vercel & GitHub secrets

- Store all production and preview variables in the Vercel dashboard or via `vercel env`.
- Example CLI workflow:
  ```bash
  vercel login
  vercel env add NEXT_PUBLIC_SUPABASE_URL production
  vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
  vercel env add NEXT_PUBLIC_SENTRY_DSN production
  vercel env add NEXT_PUBLIC_SITE_URL production
  vercel env add NEXT_PUBLIC_ALERT_SLACK_WEBHOOK production
  vercel env add NEXT_PUBLIC_ALERT_EMAIL production
  vercel env add NEXT_PUBLIC_SUPABASE_FN_BASE production
  vercel env add NEXT_PUBLIC_DRILLDOWN_BASE_URL production
  vercel env pull .env.local
  ```
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` are required by the automated GitHub Action that deploys to Vercel and by any `vercel` CLI commands.
- Keep the same set of `NEXT_PUBLIC_*` variables in preview/staging environments so the data flows can be tested before hitting production.

### Monitoring & notifications

- Enable Vercel Analytics from the project dashboard (Performance → Analytics) and run the built-in Speed Insights reports (`https://vercel.com/docs/concepts/analytics` and the `vercel speed` command) to monitor Core Web Vitals over time.
- Sentry is wired up via `NEXT_PUBLIC_SENTRY_DSN` to capture client- and server-side errors. Confirm the DSN is defined in both local and Vercel environments so error pages surface gracefully.
- The analytics dashboard surfaces Slack/email routing status. Configure `NEXT_PUBLIC_ALERT_SLACK_WEBHOOK` (or point to your alert automation) and `NEXT_PUBLIC_ALERT_EMAIL` so teams know where alerts land.
- Deploy/failure notifications use `.github/workflows/slack_notify.yml`, which requires `SLACK_BOT_TOKEN` and `SLACK_CHANNEL` (plus `SLACK_SIGNING_SECRET` for the Bolt app). Keep those secrets in GitHub and rotate the token when Slack permissions change.
- The scheduled pipeline workflow at `.github/workflows/daily-ingest.yml` sends success alerts using `SLACK_WEBHOOK_URL`. Update that webhook to the channel you want KPI completion messages to land in.

### Supabase, backend & pipeline connectivity

- Confirm the deployed app uses `NEXT_PUBLIC_SUPABASE_URL`/`ANON_KEY` to talk to the primary database. Run `npm run dev` and watch for `Supabase` calls in the browser network tab to verify connectivity.
- `NEXT_PUBLIC_SUPABASE_FN_BASE` backs the integration settings UI. Point it to the Supabase Edge Functions base so tokens, sync requests, and drill-down statuses execute securely.
- The Supabase-backed `IntegrationSettings` component, the HubSpot sync service, and analytics exports rely on `KPI_SERVICE_URL`, `API_KEY`, and `HUBSPOT_API_KEY`. Store these in GitHub Secrets or the root `.env` file shared by non-Next services.
- Trigger the pipeline locally with `python scripts/run_data_pipeline.py`; verify that outputs land in `data/metrics` and the manifest/logs directories. The same script runs nightly via `.github/workflows/daily-ingest.yml`, so use `PIPELINE_INPUT_FILE` to test alternate datasets.
- Once the pipeline completes, the Slack webhook configured in `daily-ingest.yml` posts `:tada:` updates so teams can see the ingestion status.

### Integrations & AI secrets

- `services/slack_bot` relies on `KPI_WEBHOOK_URL`, `API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and `SLACK_BOT_AUTOSTART`. Ensure these are synchronized across the deployed bot and GitHub Secrets so KPI mentions and alerts work.
- The Notion metrics importer requires `NOTION_DATABASE_ID`, `NOTION_META_TOKEN`, and `NOTION_VERSION`. Keep these scoped to the Notion workspace that houses the KPI database.
- AI helpers (`StandaloneAIEngine`, `scripts/clients.py`, and `streamlit_app.py`) look for `GROK_API_KEY`, `GOOGLE_API_KEY`, and `OPENAI_API_KEY`. Provide these values only in environments that should reach external AI services.
- `python/agents/orchestrator.py` expects `DATABASE_URL` so agent runs can persist traceability data.

## Code Style

### TypeScript

- Use strict mode (enabled in tsconfig.json)
- Avoid `any` - use `unknown` or proper types
- Define return types for public functions

### React Components

- Prefer Server Components
- Use `"use client"` only when needed
- Keep components focused and reusable

### File Organization

```
components/
  ├── ui/              # Reusable UI components
  ├── forms/           # Form components
  └── layout/          # Layout components

lib/
  ├── utils.ts         # Utility functions
  ├── database.types.ts # Database types
  └── constants.ts     # Constants
```

## Testing

```bash
# Run tests
npm run test

# Watch mode
npm run test -- --watch

# Coverage
npm run test:coverage
```

## Deployment Checklist

- [ ] Run `npm run lint`
- [ ] Run `npm run type-check`
- [ ] Run `npm run test`
- [ ] Build: `npm run build`
- [ ] Test build: `npm run start`

## Troubleshooting

### Port 3000 in use

```bash
PORT=3001 npm run dev
```

### Supabase connection fails

- Check `NEXT_PUBLIC_SUPABASE_URL`
- Check `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Verify Supabase project is active

### Type errors

```bash
npm run type-check
```

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com)
- [TypeScript](https://www.typescriptlang.org)
