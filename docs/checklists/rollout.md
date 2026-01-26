# Production Rollout Checklist

## Pre-Flight

- [ ] Added `MIDDLEWARE_SHARED_SECRET` to GitHub Secrets.
- [ ] Added `SUPABASE_SERVICE_ROLE_KEY` to GitHub Secrets.
- [ ] Updated `requirements.txt` with `iban>=1.0.0`.

## Deployment

- [ ] Merge `chore/ci-pipeline-integrity` into `main`.
- [ ] Deploy web application to Vercel/Azure Static Web Apps.
- [ ] Deploy analytics pipeline to Azure Functions/Prefect.

## Post-Deployment

- [ ] Run `deploy-verify.yml` workflow.
- [ ] Run `repo_health_check.sh` on production environment.
- [ ] Verify IBAN validation is active in transaction processing.
- [ ] Update `CLAUDE.md` with successful go-live metrics.
