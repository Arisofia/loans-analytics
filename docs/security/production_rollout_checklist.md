# Production Rollout Checklist - PR #41

## 1. Pre-Deployment (Secret Setup)
- [ ] Add `MIDDLEWARE_SHARED_SECRET` to repository secrets (Settings → Secrets and Variables → Actions).
- [ ] Generate a strong shared secret (e.g., 32+ characters).
- [ ] Verify secret presence by running the **Secret check** manual workflow.

## 2. Deployment
- [ ] Deploy the latest application code with the new secret in the target environment.
- [ ] Ensure `MIDDLEWARE_SHARED_SECRET` environment variable is mapped in the production environment.

## 3. Verification
- [ ] Run the **Deploy verify** manual workflow with `target_url`.
- [ ] Confirm HTTP 403 when spoofing headers without the secret.
- [ ] Confirm successful access when `x-internal-shared-secret` and `x-middleware-subrequest` are provided.

## 4. Monitoring & Audit
- [ ] Review observability dashboards for anomalies.
- [ ] Review logs for "Blocked unauthorized API access attempt" messages.
- [ ] Document final verification results here.

## 5. Final Approval
- [ ] Assign Ops/Security reviewers.
- [ ] Mark PR as "Ready for review".
- [ ] Merge PR #41.
