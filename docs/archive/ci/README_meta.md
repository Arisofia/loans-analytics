# Meta Integration CI/CD

## Required Secrets

- `META_SYSTEM_USER_TOKEN`: System user access token for Meta Graph API
- `META_REFRESH_TOKEN`: (optional) Refresh token if using long-lived tokens

## Setup

1. Add the above secrets to your GitHub repository (Settings → Secrets → Actions).
2. Ensure your config/integrations/meta.yaml is present and correct.
3. The pipeline will use these secrets for all Meta API calls.

## Safe Steps

- Never commit real tokens or secrets to the repo.
- Rotate tokens regularly and update secrets in GitHub.
- Audit workflow logs for failed API calls or rate limit errors.
