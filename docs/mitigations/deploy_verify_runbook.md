# Deploy verification runbook

Use this runbook to verify the middleware mitigation after deployment using the built-in GitHub Actions manual workflow.

Prerequisites:

- `MIDDLEWARE_SHARED_SECRET` must be set in **Repository secrets** (or organization-level secrets) before running the workflow.
- A reachable deployment URL (staging or production) to test against.

How to run:

1. Open the Actions tab in GitHub and select **Deploy verification (manual)**, or run from CLI:
   - gh workflow run deploy-verify.yml --repo Arisofia/abaco-loans-analytics --field target_url=https://your-prod.example.com
2. The workflow will perform two checks:
   - Send a request with `x-middleware-subrequest` header (no secret) and expect a 403 response.
   - Send a request with `x-middleware-subrequest` and `x-internal-shared-secret: <secret>` headers and expect a non-403 response.

Interpretation:

- If the first test returns anything other than 403, the mitigation is not functioning—do not consider the deployment safe.
- If the second test returns 403, verify that the correct `MIDDLEWARE_SHARED_SECRET` is set in the repository secrets and that the secret matches what the deployed runtime uses.

Notes:

- This workflow is intentionally manual and requires a human operator to confirm the target environment to avoid accidental execution against internal systems.
- Keep this runbook updated with the production target and the person responsible for executing it.
