# Agent/Workflow Secrets Documentation

All required secrets for the Loans Multi-Agent Intelligence Ecosystem are managed
in Azure Key Vault or GitHub Secrets. No manual action is needed for runtime
access.

## Secrets Management Summary

- **Azure Key Vault**: Used for production and sensitive credentials
  (API keys, DB URIs, tokens).
- **GitHub Secrets**: Used for CI/CD, workflow automation, and agent
  orchestration.
- **Environment Variables**: All workflows and agents access secrets via
  environment variables.

## Key Secrets (Examples)

- OPENAI_API_KEY
- SUPABASE_SERVICE_ROLE
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_URL
- SUPABASE_ANON_KEY
- OPIK_TOKEN
- PHOENIX_TOKEN
- CLAUDE_ROCKET_TOKEN
- XAI_TOKEN
- GEMINI_API_KEY
- PERPLEXITY_API_KEY
- TAVILY_KEY
- AMPLITUDE_API_KEY
- META_ACCESS_TOKEN
- SENTRY_DSN
- GOOGLE_SHEETS_CREDENTIALS_JSON (optional in CI; used to materialize credentials/google-service-account.json)
- GOOGLE_SHEETS_CREDENTIALS_PATH (runtime path used by ingestion code)
- GOOGLE_SHEETS_SPREADSHEET_ID

## Best Practices

- Rotate secrets regularly and monitor access logs.
- Use least-privilege principle for all agent/service accounts.
- Validate secret presence in CI/CD before workflow execution.
- Document any new secret in this file and in the vault.

## Validation

- Use workflow checks (`.github/workflows/security-scan.yml` and related CI jobs)
  to confirm required secrets are present in runtime contexts.
- All workflows will fail fast if a required secret is missing.

---

This file is auto-generated and should be updated if new agents or workflows
require additional secrets.
