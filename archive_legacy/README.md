# 📦 ARCHIVED LEGACY CONTENT

**Purpose**: Safe storage for obsolete, experimental, or reference-only materials.  
**Status**: ⚠️ NOT FOR PRODUCTION USE  
**Preservation**: All content preserved in git history for reference.

---

## ⚠️ DO NOT USE IN ACTIVE WORKFLOW

This folder contains:

- ❌ Legacy scripts (replaced by unified pipeline)
- ❌ Old documentation (superseded by current docs/)
- ❌ Deprecated implementations (use current versions)
- ❌ Experimental features (incomplete, untested)
- ❌ Ad-hoc notebooks (not automated)

**If you're looking for something to run**, check the main `UNIFIED_WORKFLOW.md` instead.

---

## 📋 WHAT'S IN ARCHIVE_LEGACY

### `archive_legacy/docs/`

**Purpose**: Historical and obsolete documentation

**Contents**:

- `MIGRATION_v1_to_v2.md` - Legacy migration guide (pipeline already migrated)
- `ARCHITECTURE_OLD.md` - Pre-unification architecture (obsolete)
- `EMERGENCY_RESPONSE_PLAN.md` - Old incident runbooks (use OPERATIONS.md)
- `TECH_SPEC_OLD.md` - Earlier technical specifications
- `AUDIT_REPORTS_*` - Historical audit snapshots

**When to reference**:

- Understanding historical decisions
- Git archaeology (why was decision X made?)
- NOT for current implementation guidance

---

### `archive_legacy/scripts/`

**Purpose**: Deprecated pipeline runners and one-off helpers

**Examples**:

- `legacy_run_data_pipeline.py` (v1) → Use `scripts/run_data_pipeline.py` (v2)
- `ingest_cascade_old.py` → Use `src/pipeline/ingestion.py`
- `manual_etl_helpers.py` → Use automated pipeline phases
- `one_off_analysis.py` → Not part of scheduled workflow

**Why archived**:

- Functionality moved to unified pipeline
- Code duplication eliminated
- Better implementations available in current structure

---

### `archive_legacy/python/`

**Purpose**: Older module versions and experimental code

**Contains**:

- `python/agents_v1/` - Old agent implementations (use `python/multi_agent/`)
- `python/legacy_workflows/` - Deprecated workflow runners
- `python/kpi_engine_v1.py` - First KPI engine (use `src/kpi_engine_v2.py`)
- `python/old_utilities/` - Outdated helper functions

---

### `archive_legacy/projects/`

**Purpose**: Experimental and incomplete initiatives

**Examples**:

- `kotlin_services_poc/` - Proof-of-concept (not integrated)
- `student_work/` - Educational projects (not production-ready)
- `contractor_experiments/` - External work (incomplete)

---

### `archive_legacy/notebooks/`

**Purpose**: Jupyter notebooks for manual analysis

**Contents**:

- `eda_exploration.ipynb` - Exploratory data analysis
- `kpi_verification_manual.ipynb` - Manual KPI checks
- `data_quality_analysis.ipynb` - Ad-hoc quality reviews

**Status**:

- ✅ Good for understanding data
- ❌ NOT part of automated pipeline
- ⚠️ Results not guaranteed fresh

---

## 🔄 HOW CONTENT WAS ORGANIZED

### **Decision Criteria**

Content was moved to archive if it:

1. **Functionality replaced** - Newer version exists in active folders
2. **No longer runs** - Deprecated entry points (not called)
3. **Experimental** - Incomplete features, POCs, side projects
4. **Reference-only** - Historical documentation, old specs
5. **Ad-hoc** - Notebooks, one-off scripts, manual helpers

### **What Stayed in ACTIVE Folders**

Only content that:

1. ✅ Executes in production workflow
2. ✅ Has clear ownership & SLA
3. ✅ Receives active maintenance
4. ✅ Required for daily operations
5. ✅ Tested and documented

---

## 🔍 FINDING SOMETHING

### **If you need KPI formulas**

→ `config/kpis/kpi_definitions.yaml` (ACTIVE)

### **If you need pipeline code**

→ `src/pipeline/` (ACTIVE)

### **If you need to understand old decisions**

→ `archive_legacy/docs/` (REFERENCE)

### **If you want to explore data manually**

→ `archive_legacy/notebooks/` (NOT AUTOMATED)

### **If you want to run an experiment**

→ Create new folder outside archive, or use archived code as reference

---

## 🚫 DANGER: DO NOT RESTORE

Unless you're:

1. **Git archaeology** - Understanding historical context
2. **Compliance/audit** - Need to prove something worked
3. **Development reference** - Learning from old implementations

**DO NOT** use archived code as-is in production. It's likely:

- Missing bug fixes (newer versions have them)
- Using old APIs/libraries
- Without proper error handling
- Not integrated with current configs

---

## 📚 RETENTION POLICY

| Category           | Retention | Why                    |
| ------------------ | --------- | ---------------------- |
| Old docs           | Forever   | Compliance, history    |
| Deprecated code    | 1 year    | Reference, then delete |
| Failed experiments | 6 months  | Learning, then archive |
| Obsolete scripts   | 6 months  | Reference, then delete |

**All content is in git history**, so nothing is truly lost.

---

## ✅ SUMMARY

- 📦 **Archive is isolated** from active workflow
- ⚠️ **Nothing here runs automatically**
- 🔍 **Everything is preserved** in git
- 📝 **Reference-only** for understanding decisions
- 🚫 **DO NOT restore** to production without review

**Active projects** are in the main folder structure.  
**Legacy content** is safely here.  
**Everyone knows the difference.** ✨

---

_Last updated: January 29, 2026_
