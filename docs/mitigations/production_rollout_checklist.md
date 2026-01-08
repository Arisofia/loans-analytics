# Production Rollout Checklist

Follow these steps to safely roll out the middleware mitigation for CVE-2025-29927.

## Phase 1: Configuration
- [ ] Add `MIDDLEWARE_SHARED_SECRET` to Repository or Organization secrets (required).
- [ ] Run **Secret check (manual)** workflow to confirm secret presence.

## Phase 2: Deployment
- [ ] Deploy the application to the target environment (staging or production) with the secret present in the environment variables.

## Phase 3: Verification
- [ ] Run **Deploy verification (manual)** workflow with `target_url` set to the deployed environment.
- [ ] Confirm: Spoofed header WITHOUT secret (`x-middleware-subrequest`) -> **HTTP 403**.
- [ ] Confirm: Spoofed header WITH secret (`x-internal-shared-secret`) -> **non-403**.

## Phase 4: Monitoring
- [ ] Monitor observability dashboards for anomalies.
- [ ] Document verification results in the audit log.
