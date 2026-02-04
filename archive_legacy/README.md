# Archive Legacy

This directory contains **ARCHIVED LEGACY CONTENT** that is no longer part of the active production workflow.

## ⚠️ WARNING: DO NOT USE FOR ACTIVE DEVELOPMENT

All content in this directory is **ARCHIVED** and should **NOT** be used for active development or production operations.

## Purpose

This archive preserves historical code, documentation, and experiments for:
- Historical reference
- Audit compliance
- Understanding past decisions
- Migration context
- Learning from previous approaches

## Contents

### `archive_legacy/docs/`
**Archived Documentation**
- Old migration guides (v1 → v2)
- Legacy architecture diagrams
- Emergency response plans (archive versions)
- Deprecated technical specs
- Historical audit reports

**Reason for archival**: Reference only - not used in current operations

### `archive_legacy/scripts/`
**Archived Scripts**
- Legacy pipeline runners (old versions of `run_data_pipeline.py`)
- Deprecated ingestion scripts
- Manual ETL helpers
- One-off analysis scripts

**Reason for archival**: Replaced by unified pipeline orchestrator

### `archive_legacy/python/`
**Archived Python Modules**
- Old `agents/` implementations
- Deprecated workflow modules
- Legacy KPI engines (v1)
- Older utility functions

**Reason for archival**: Superseded by current `python/` and `src/pipeline/` modules

### `archive_legacy/projects/`
**Archived Projects**
- Experimental features
- Proof-of-concept implementations
- Student/contractor work
- Incomplete initiatives

**Reason for archival**: Not integrated into main workflow

### `archive_legacy/notebooks/`
**Archived Jupyter Notebooks**
- Data exploration notebooks
- Data science experiments
- Manual KPI verification notebooks
- Ad-hoc analysis

**Reason for archival**: Ad-hoc analysis - not automated

## When to Reference Legacy Code

✅ **Appropriate uses:**
- Understanding historical context for current features
- Audit trail for compliance reviews
- Learning from past implementation decisions
- Recovering specific logic that may be reusable

❌ **Do NOT:**
- Copy code directly from archive to active codebase
- Reference for current best practices
- Use as documentation for active features
- Deploy or run archived scripts in production

## Active Production Workflow

Instead of archived content, use:

### Active Pipeline
```bash
# Run current pipeline
python scripts/run_data_pipeline.py

# View current config
config/pipeline.yml
config/business_rules.yaml
config/kpis/kpi_definitions.yaml
```

### Active Code Locations
- **Pipeline**: `src/pipeline/` (orchestrator, ingestion, transformation, calculation, output)
- **Utilities**: `python/` (config, logging, models, multi-agent)
- **Dashboard**: `streamlit_app.py` or `apps/web/` (future)
- **Tests**: `tests/`

### Documentation
- **Architecture**: `docs/architecture.md`
- **Operations**: `docs/OPERATIONS.md`
- **Quick Start**: `docs/operations/QUICK_START.md`
- **Unified Workflow**: `docs/operations/UNIFIED_WORKFLOW.md`

## Retention Policy

**Git History**: All archived content is preserved in git history and can be recovered if needed.

**Review Schedule**: 
- Quarterly review of archive necessity
- Remove truly obsolete content after 2 years
- Keep compliance-relevant content indefinitely

**Before Archiving New Content:**
1. Ensure it's documented in commit messages
2. Update `.repo-structure.json` if needed
3. Add entry to `CHANGELOG.md`
4. Create this archive entry

## Structure Definition

This structure is defined in `.repo-structure.json` under `LEGACY_ARCHIVED_CONTENT`.

For the active production workflow, see:
```bash
# View repository structure
cat .repo-structure.json

# Validate structure
python scripts/validate_structure.py
```

## Migration History

**v1 → v2 Unification (2026-01-29)**
- Consolidated multiple pipeline implementations into single orchestrator
- Archived old agents, workflows, and KPI engines
- Unified configuration under `config/`
- See: `docs/PIPELINE_UNIFICATION_PLAN.md`

## Questions?

For questions about:
- **Active features**: See `docs/operations/QUICK_START.md`
- **Architecture**: See `docs/architecture.md`
- **Why something was archived**: Check git history and `CHANGELOG.md`

---

**Last Updated**: 2026-02-02  
**Status**: Archive container created per `.repo-structure.json`  
**Next Review**: 2026-05-02
