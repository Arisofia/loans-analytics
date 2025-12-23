# Abaco Cascade Ingest + C-Suite Agent (v1)

Production assets for automated Cascade debt exports and the executive agent runbook.

- `scripts/cascade_ingest.py` runs Playwright against the Cascade export URL with retries and validation.
- `python/ingest/transform.py` canonicalizes loan tape columns (loan_id, balance, DPD, dates, ingest timestamp).
- `agents/specs/c_suite_agent.yaml` / `agents/prompts/c_suite_prompt.md` define the executive agent tools, guardrails, and outputs.
- `orchestration/github/workflows/cascade_ingest.yml` and `vibe_quality_gate.yml` run the ingestion pipeline and enforce Vibe Solutioning quality checks.

See `docs/README_CASCADE_INGEST.md` for the full runbook, secrets, and debugging steps.
