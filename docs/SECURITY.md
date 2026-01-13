# Security Policy

## Required Secrets

- `GEMINI_API_KEY_SIMPLE`: Gemini PR review
- `PERPLEXITY_API_KEY`: Perplexity review
- `SLACK_WEBHOOK_URL`: Slack notifications

## Workflow Logic

- All workflows linted and scanned for secrets before merge.
- Actions pinned to tags or SHAs.

## Escalation

- Contact: <security@yourdomain.com>
- Rotate secrets quarterly or on role change.
