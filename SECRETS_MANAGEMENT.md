# Agent/Workflow Secrets Documentation

All required secrets for the Abaco Multi-Agent Intelligence Ecosystem are managed
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
- SLACK_BOT_TOKEN
- OPIK_TOKEN
- PHOENIX_TOKEN
- CLAUDE_ROCKET_TOKEN
- XAI_TOKEN
- GEMINI_API_KEY
- PERPLEXITY_API_KEY
- TAVILY_KEY
- HUBSPOT_TOKEN
- FIGMA_TOKEN
- AMPLITUDE_API_KEY
- META_ACCESS_TOKEN
- SENTRY_DSN

## Best Practices

- Rotate secrets regularly and monitor access logs.
- Use least-privilege principle for all agent/service accounts.
- Validate secret presence in CI/CD before workflow execution.
- Document any new secret in this file and in the vault.

## Validation

- Run `python scripts/validate_secrets.py` to confirm all secrets are available
  to the runtime.
- All workflows will fail fast if a required secret is missing.

---
This file is auto-generated and should be updated if new agents or workflows
require additional secrets.
