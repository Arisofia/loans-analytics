
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
- After editing, restart the dev server and verify that Supabase rows are readable and that the analytics dashboard renders without the "not set" warnings for alerts or drill-downs.

### Frontend variables (apps/web)

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL used by the client and integration helpers. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public (read-only) API key consumed by the React app. Keep this scoped to the client role in Supabase. |
| `NEXT_PUBLIC_SUPABASE_FN_BASE` | Root of Supabase Edge Functions (`https://<project>.functions.supabase.co`). Required by `IntegrationSettings` and synchronization helpers. |
| `NEXT_PUBLIC_DRILLDOWN_BASE_URL` | Base URL for drill-down exports and analytics tables (can point at Supabase Studio, Supabase Edge App, or another analytics surface). |
| `NEXT_PUBLIC_ALERT_EMAIL` | Contact email shown alongside alerts (defaults to `alerts@abaco.loans`). |
| `NEXT_PUBLIC_SITE_URL` | Canonical site URL used for metadata, Open Graph, and robots. |
| `NEXT_PUBLIC_SENTRY_DSN` | DSN for Sentry error tracking on both client and server. |

### Shared integration & automation variables

| Variable | Purpose |
| --- | --- |
| `PIPELINE_INPUT_FILE` | Optional override for `scripts/run_data_pipeline.py` to point at a different CSV. |
| `GITHUB_TOKEN` / `GH_TOKEN` | Grant access to the GitHub API for scripts such as `scripts/pr_status.py` and `scripts/trigger_workflows.py`. |
| `OPENAI_API_KEY` | Enables OpenAI-powered summaries inside the Streamlit app and other agents. |
| `GOOGLE_API_KEY` | Required by the Gemini client in `scripts/clients.py`. |
| `GROK_API_KEY` | Required by the Grok client used by `StandaloneAIEngine`. |
| `DATABASE_URL` | Connection string used by `python/agents/orchestrator.py` and other automation helpers. |

### Vercel & GitHub secrets

- Store all production and preview variables in the Vercel dashboard or via `vercel env`.
- Example CLI workflow:
  ```bash
  vercel login
  vercel env add NEXT_PUBLIC_SUPABASE_URL production
  vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
  vercel env add NEXT_PUBLIC_SENTRY_DSN production
  vercel env add NEXT_PUBLIC_SITE_URL production
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

### Supabase, backend & pipeline connectivity

- Confirm the deployed app uses `NEXT_PUBLIC_SUPABASE_URL`/`ANON_KEY` to talk to the primary database. Run `npm run dev` and watch for `Supabase` calls in the browser network tab to verify connectivity.
- `NEXT_PUBLIC_SUPABASE_FN_BASE` backs the integration settings UI. Point it to the Supabase Edge Functions base so tokens, sync requests, and drill-down statuses execute securely.
- Trigger the pipeline locally with `python scripts/run_data_pipeline.py`; verify that outputs land in `data/metrics` and the manifest/logs directories. The same script runs nightly via `.github/workflows/daily-ingest.yml`, so use `PIPELINE_INPUT_FILE` to test alternate datasets.

### Integrations & AI secrets

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
