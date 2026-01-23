# services/payments/AGENTS.override.md

## Payments service rules

- Use `make test-payments` instead of `npm test`.
- Never rotate API keys without first notifying the #security-incident Slack
  channel and following the "Payments API Key Rotation" runbook in the
  Security > Runbooks > Payments section of the internal wiki.
- Page the on-call via PagerDuty for urgent rotations and escalate to the
  security incident bridge if you cannot reach them within 15 minutes.
