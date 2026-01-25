# Automated Deploy Verification (CVE Mitigation)

This document describes the automated steps to verify the middleware secret-based mitigation (MIDDLEWARE_SHARED_SECRET) and collect auditable evidence for deployment gates.

## Overview

- Ensure the repository secret `MIDDLEWARE_SHARED_SECRET` is set by an admin.
- Run the `Secret check` workflow to confirm presence of the secret.
- Deploy the change to target environment (operator/CI step).
- Run the `Deploy verification` workflow to test the endpoint behavior with and without the secret.
- Collect the workflow run URLs, deployed commit SHA, and verification artifacts (HTTP statuses and response bodies if available).

## Workflows

- `Secret check` - Exists in `.github/workflows/secret-check.yml`. Use `workflow_dispatch` to run.
- `Deploy verification` - Exists in `.github/workflows/deploy-verify.yml`. Use `workflow_dispatch` with `target_url` input.
- `Orchestrate deploy verification` - `.github/workflows/orchestrate-deploy-verify.yml` will ensure the secret is present and dispatch the `Deploy verification` workflow.

## Local script

Use `scripts/deploy_verify.sh` for local pre-flight checks and to speed up evidence collection during manual runs. The script will:

- Print current HEAD and recent commits
- Confirm presence of `MIDDLEWARE_SHARED_SECRET` via `gh` or environment
- Dispatch `secret-check` and `deploy-verify` workflows (requires `GH_TOKEN` or `GITHUB_TOKEN` with repo permissions)
- Poll workflow runs and download artifacts into `tmp/deploy-verify-logs`

Example usage:

```bash
./scripts/deploy_verify.sh --target-url https://staging.example.com
```

## Evidence to collect

- Link to `secret-check` workflow run
- Link to `deploy-verify` workflow run
- Deployed commit SHA and branch/ref
- Artifacts: `no-secret.txt`, `with-secret.txt` or any logs uploaded by the workflow
- cURL outputs and HTTP statuses

## Acceptance criteria

- `Secret check` must pass (secret present)
- `Deploy verification` must demonstrate the endpoint rejects spoofed header without secret and accepts with the secret (expected HTTP statuses)
- Artifacts must be attached to the workflow runs and linked in the PR that closes the mitigation
