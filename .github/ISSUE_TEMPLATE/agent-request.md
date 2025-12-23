---
name: Agent change request
about: Request a new or updated agent spec, prompt, or tooling.
title: "[Agent] "
labels: agent
assignees: ''

---

## Summary
- [ ] Describe the desired capability or fix
- [ ] Outline the expected outputs (e.g., Notion page, Figma deck, Slack alert)

## Details
- Agent name / spec: (e.g., C-suite Agent v1)
- Trigger cadence: (e.g., daily after cascade ingest)
- Inputs / data sources: (list tables, KPIs, APIs)
- Tools & guardrails: (SQL runners, API integrations, tone constraints)

## Acceptance criteria
1. [ ] Updated spec/prompt files under `agents/specs/` and `agents/prompts/` reflect the request
2. [ ] Runtime harness (python/agents/*.py or node/agents) can consume the new spec
3. [ ] Downstream docs and CI checks reference the updated agent

## Testing notes
- [ ] Agent harness executed via `python/agents/<agent>.py --run-id TEST --date-range "last 30 days"`
- [ ] Output stored under `data/agents/`
