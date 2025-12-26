# Configuration Consolidation Strategy
**Status**: PHASE 3.4E In Progress  
**Date**: 2025-12-26

---

## Current State: Fragmented (18 files, 120KB, 6 directories)

```
config/
├─ pipeline.yml (MAIN - 8KB)
├─ pipelines/data_orchestration.yaml (DUPLICATE?)
├─ integrations/ (4 files: Cascade, Meta, Slack, Perplexity)
├─ agents/specs/ (4 agent configs)
├─ kpis/ (3 KPI definition files)
├─ data_schemas/ (1 schema file)
├─ Other configs (8 more files)
```

**Problem**: No clear hierarchy, unclear which config is active, environment-specific settings unclear

---

## Target State: Unified (Single Source of Truth + Modular Overrides)

### Architecture:

```
config/
├─ pipeline.yml (MASTER - unified everything)
│  ├─ Pipeline phases (ingestion, transformation, calculation, output)
│  ├─ Integration credentials (env vars)
│  ├─ Agent specifications (inline)
│  ├─ KPI definitions (inline)
│  └─ Observability & security
│
├─ environments/ (OVERRIDES by environment)
│  ├─ development.yml
│  ├─ staging.yml
│  └─ production.yml
│
└─ LEGACY/ (ARCHIVED - preserved for reference only)
   ├─ integrations/
   ├─ agents/specs/
   ├─ kpis/
   └─ ... (all other configs marked DO NOT USE)
```

---

## Implementation Plan

### Phase 1: Extend pipeline.yml (TODAY)
1. Add integrations section
2. Add agents section
3. Add kpi_definitions section
4. Use environment variables for all secrets

### Phase 2: Create environment overrides (TOMORROW)
1. development.yml (local testing, mocked credentials)
2. staging.yml (pre-production, real Cascade)
3. production.yml (live, hardened security)

### Phase 3: Archive old configs (WEEK)
1. Move to `/config/LEGACY/` with warning headers
2. Add "DO NOT USE" markers
3. Keep for reference only

### Phase 4: Update all imports (WEEK)
1. Update orchestrator.py to load from single pipeline.yml
2. Remove references to scattered configs
3. Add environment variable resolution

---

## Migration Path

### Before (fragmented):
```python
# Different services loading different configs
ingestion = load_config("config/integrations/cascade.yaml")
agent = load_config("config/agents/specs/c_level_executive_agent.yaml")
kpis = load_config("config/kpi_definitions.yml")
```

### After (unified):
```python
# Single source of truth with environment overrides
config = load_config("config/pipeline.yml", env=os.getenv("ENV", "development"))
# All integrations, agents, KPIs in one place
ingestion = config["integrations"]["cascade"]
agent = config["agents"]["c_level_executive"]
kpis = config["kpis"]
```

---

## Key Principles

1. **Single source of truth**: pipeline.yml is the master
2. **Environment-driven**: development/staging/production override specific values
3. **Secret management**: All credentials from environment variables
4. **Backward compatibility**: Old configs preserved in LEGACY/ for reference
5. **Clear precedence**: pipeline.yml (base) → environment-specific (override)

---

## Action Items

- [ ] Extend config/pipeline.yml with integrations, agents, KPI sections
- [ ] Create config/environments/development.yml|staging.yml|production.yml
- [ ] Update python/pipeline/orchestrator.py to use new structure
- [ ] Move old configs to /config/LEGACY/ with deprecation warnings
- [ ] Update documentation with new config loading pattern
- [ ] Test all environments to confirm configuration works

