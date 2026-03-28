# Production Deployment Guide

## Canonical Production Path (Single Source of Truth)

This repository supports **one canonical production deployment path**:

1. Build immutable container images from `Dockerfile`, `Dockerfile.dashboard`, and `Dockerfile.pipeline`.
2. Push images to GHCR via `.github/workflows/deploy-free-tier.yml`.
3. Deploy those exact images to **one** free-tier target (`render`, `railway`, or `fly`) using the same workflow.

Historical Azure/AWS/GCP examples were removed from this guide because they are not active in this repository.

---

## Required Runtime Services

- API service (`Dockerfile`)
- Streamlit dashboard (`Dockerfile.dashboard`)
- Pipeline runner (`Dockerfile.pipeline`)
- Supabase/PostgreSQL (managed external dependency)

---

## Required Environment Variables

### Core Data + Auth

```bash
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
API_JWT_SECRET=<32-byte-secret>
```

### Optional LLM Providers (only if enabled)

```bash
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
GOOGLE_API_KEY=<key>
```

### Optional Telemetry

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://<collector>:4318
```

---

## GitHub Secrets Required for Deploy Workflow

Set only the secrets required by your chosen target:

### Always required

- `GITHUB_TOKEN` (provided by Actions runtime)

### Render deployment

- `RENDER_API_KEY`
- `RENDER_SERVICE_ID`

### Railway deployment

- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT_ID`

### Fly.io deployment

- `FLY_API_TOKEN`

---

## Deployment Procedure

### 1) Trigger workflow

Run `.github/workflows/deploy-free-tier.yml` via `workflow_dispatch`:

- `target`: `ghcr`, `render`, `railway`, `fly`, or `all`
- `service`: `api`, `dashboard`, or `pipeline`

### 2) Verify image publication

Confirm GHCR tags exist:

- `ghcr.io/<owner>/loans-analytics-api:sha-<commit>`
- `ghcr.io/<owner>/loans-analytics-dashboard:sha-<commit>`

### 3) Verify runtime health

- API health endpoint: `/health`
- Streamlit health endpoint: `/_stcore/health`
- Pipeline execution logs for explicit success status

---

## Rollback

Rollback is image-tag based:

1. Select previous known-good `sha-<commit>` image tag in GHCR.
2. Redeploy target with that exact tag.
3. Re-run health checks.

Do not roll back by mixing code from one revision with containers from another revision.

---

## Local Validation Before Production

Use the canonical compose stack for pre-prod validation only:

```bash
docker compose up -d --build
curl -f http://localhost:8000/health
curl -f http://localhost:8501/_stcore/health
```

If any check fails, block release.

---

## Release Gate Checklist

- [ ] `tests.yml` passes
- [ ] `security-scan.yml` passes
- [ ] No missing required secrets for chosen deploy target
- [ ] Health endpoints return success after deployment
- [ ] Dashboard and API versions match the deployed image SHA

If any item is false, release is **not production-ready**.
