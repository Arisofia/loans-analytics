# Deploy Verification Runbook
## Overview
This runbook describes how to verify that the Middleware Shared Secret protection is working correctly.
## Step 1: Trigger the Verification Workflow
1. Go to the **Actions** tab in the GitHub repository.
2. Select the **Deploy verify** workflow from the sidebar.
3. Click **Run workflow**.
4. Enter the `target_url` (e.g., `https://abaco-analytics-dashboard.azurewebsites.net`).
5. Click **Run workflow**.
## Step 2: Interpret Results
### Negative Test (No Secret)
The workflow sends a request without the secret.
- **Expected**: HTTP 403 Forbidden.
- **Failure**: Any other status code means the middleware is NOT protecting the endpoint.
### Positive Test (With Secret)
The workflow sends a request with the `x-internal-shared-secret` header.
- **Expected**: Non-403 status (e.g., 200 OK).
- **Failure**: HTTP 403 means the secret is mismatched or the middleware is misconfigured.
## Troubleshooting
- **Mismatched Secret**: Ensure `MIDDLEWARE_SHARED_SECRET` in GitHub Secrets matches the environment variable in the target environment.
- **Missing Header**: The middleware requires `x-middleware-subrequest: true` to trigger the spoofing check logic.
