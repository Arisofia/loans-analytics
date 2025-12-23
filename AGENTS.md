# AGENTS.md

## Repository expectations

- Run `npm run lint` at the repository root for JS/TS changes (this delegates to the web app lint task). If you update another package with its own lint workflow, run that package's documented lint command instead.
- Document public utilities in `docs/` when you change behavior.

## Unified agents

- **Pipeline orchestration**: ingestion & transformation logging and compliance helpers (owner: data engineering, reviewer: analytics ops) ensures schema verification, lineage capture, and audit metadata are versioned with outputs.
- **Validation & compliance utilities**: `python.validation` enforces required numeric/date columns, while `python.compliance` masks detected PII, records access, and serializes the report (owner: data engineering, reviewer: data privacy) so that workflow context is versioned in `logs/runs`.
- **Collaboration**: key artefacts (manifests, compliance reports, access logs) remain under the pipeline workflow repo path with associated metadata and reviewer approvals in PR descriptions.
