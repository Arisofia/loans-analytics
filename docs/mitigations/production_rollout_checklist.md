# Production rollout checklist — Middleware shared-secret mitigation

Follow this checklist when rolling out the `MIDDLEWARE_SHARED_SECRET`-based mitigation to a deployed environment.

- [ ] Ensure `MIDDLEWARE_SHARED_SECRET` is created in **Repository secrets** (or organization-level secrets) and communicated to runtime owners only via your secret management process.
- [ ] Verify the secret value matches what is configured in the deployed runtime (env var or secret mount).
- [ ] Run `Secret check (manual)` workflow (GitHub Actions) to ensure the repo secret is present.
- [ ] Deploy the application to the target environment (staging/production) with the secret present.
- [ ] Run `Deploy verification (manual)` workflow with `target_url=<deployed-url>` and confirm:
  - Spoofed header without secret → **HTTP 403** (blocked)
  - Spoofed header with secret → **non-403** (allowed)
- [ ] If verification succeeds, monitor observability dashboards (Grafana/Alloy) and logs for anomalies for at least one deployment window.
- [ ] Optionally: apply the WAF rule in **log mode** first, observe traffic for 24–72 hours, then switch to **block** if acceptable.
- [ ] Add a short post-deploy entry to the incident/audit log documenting the verification results and operator that ran them.

**Contacts:** Add the on-call or ops contacts for the environment here.

**Notes:** Do not share the secret in plaintext in PRs, issues, or chat; use repo secrets and the standard rotation process described in `docs/mitigations/rotate_secrets.md`.
