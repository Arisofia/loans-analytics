# Production Deployment Guide

## Canonical Production Path (Single Source of Truth)

This repository currently ships **validation and security workflows**, but it does **not** contain a checked-in deployment workflow.

The canonical production procedure is therefore:

1. Build immutable container images from `Dockerfile` and `Dockerfile.dashboard`.
2. Publish those exact images in your deployment system of record.
3. Deploy those exact image digests to your chosen runtime target.

Historical Azure/AWS/GCP examples were removed from this guide because they are not active in this repository.

---

## Required Runtime Services

- API service (`Dockerfile`)
- Streamlit dashboard (`Dockerfile.dashboard`)
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

## Deployment Credentials

Store only the credentials required by your chosen deployment platform in that platform's secret manager.

This repository does not currently define a canonical GitHub Actions deployment workflow, so platform-specific deployment secrets should not be documented as required repository workflow inputs until such a workflow exists.

---

## Deployment Procedure

### 1) Build and publish images

Build the API and dashboard images from the checked-in Dockerfiles and publish them through your deployment pipeline.

### 2) Verify image publication

Confirm GHCR tags exist:

- `ghcr.io/<owner>/loans-analytics-api:sha-<commit>`
- `ghcr.io/<owner>/loans-analytics-dashboard:sha-<commit>`

### 3) Verify runtime health

- API health endpoint: `/health`
- Streamlit health endpoint: `/_stcore/health`

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
