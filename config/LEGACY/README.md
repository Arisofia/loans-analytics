# ⚠️ LEGACY CONFIGURATION FILES - DO NOT USE

This directory contains deprecated configuration files that have been consolidated into the unified pipeline configuration system (as of 2025-12-26).

## Migration Status

All configurations have been merged into:
- **`config/pipeline.yml`** - Master configuration (single source of truth)
- **`config/environments/{development,staging,production}.yml`** - Environment-specific overrides

## Why These Files Are Here

These files are preserved for historical reference only. They were:
1. Analyzed during Phase 1 Comprehensive Audit
2. Consolidated into pipeline.yml during Phase 3.4E (Configuration Consolidation)
3. Archived to LEGACY/ with "DO NOT USE" markers

## Files in This Directory

### integrations/
- `cascade.yaml` → Merged into `pipeline.yml:integrations.cascade`
- `meta.yaml` → Merged into `pipeline.yml:integrations.meta`
- `slack.yaml` → Merged into `pipeline.yml:integrations.slack`
- `perplexity_comet.yaml` → Merged into `pipeline.yml:integrations.perplexity_comet`

### agents/specs/
- `kpi_analytics_agent.yaml` → Merged into `pipeline.yml:agents.kpi_analytics`
- `risk_agent.yaml` → Merged into `pipeline.yml:agents.risk_analysis`
- `c_level_executive_agent.yaml` → Merged into `pipeline.yml:agents.c_level_executive`
- `data_ingestion_transformation_agent.yaml` → Merged into `pipeline.yml:agents.data_ingestion_transformation`

### kpis/
- `kpi_definitions.yaml` → Merged into `pipeline.yml:kpi_definitions`

### pipelines/
- `data_orchestration.yaml` → Concepts merged into orchestrator.py

### data_schemas/
- Legacy schema files (referenced but now in pipeline.yml validation config)

### Root Files
- `kpi_definitions.yml` → Consolidated into unified KPI definitions
- `evaluation-thresholds.yml` → Merged into threshold definitions
- `personas.yml` → Reference only (not part of pipeline)
- `roles_and_outputs.yaml` → Reference only (not part of pipeline)

## How to Update Configuration

### For Local Development:
```bash
export PIPELINE_ENV=development
# orchestrator.py loads config/pipeline.yml + config/environments/development.yml
```

### For Staging:
```bash
export PIPELINE_ENV=staging
# orchestrator.py loads config/pipeline.yml + config/environments/staging.yml
```

### For Production:
```bash
export PIPELINE_ENV=production
# orchestrator.py loads config/pipeline.yml + config/environments/production.yml
```

## Deletion Timeline

These files will be deleted in:
- **v2.0 Release** (Q1 2026) - 90 days after consolidation

## Questions?

Refer to:
- `docs/ARCHITECTURE.md` - System design documentation
- `config/CONFIG_STRATEGY.md` - Original consolidation strategy
- `PROGRESS_REPORT.md` - Consolidation status

---
**Consolidation Date**: 2025-12-26  
**Consolidated By**: Phase 3.4E Engineering Mandate  
**Status**: ✅ Complete
