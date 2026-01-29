# 📈 VISUAL WORKFLOW GUIDE

**Process flow diagrams showing how all components connect.**

---

## 🔄 COMPLETE DATA FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UNIFIED PIPELINE EXECUTION                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              ENTRY POINT
                                  ↓
                    scripts/run_data_pipeline.py
                                  ↓
                    src/pipeline/orchestrator.py
                    (Reads config, coordinates phases)
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: INGESTION                                                         │
│  Location: src/pipeline/ingestion.py                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Config ← config/pipeline.yml                                             │
│           (endpoints, auth, validation rules)                             │
│           ↓                                                                │
│  ┌─────────────────────────────┐                                          │
│  │ 1. Read Cascade API config  │ → HTTP_CLIENT                            │
│  ├─────────────────────────────┤                                          │
│  │ 2. Make API request         │ → RETRY + RATE_LIMIT                     │
│  ├─────────────────────────────┤                                          │
│  │ 3. Validate schema          │ → python/models/cascade_schemas.py       │
│  │                             │   (Pydantic)                             │
│  ├─────────────────────────────┤                                          │
│  │ 4. Check duplicates         │ → HASH_VERIFICATION                      │
│  ├─────────────────────────────┤                                          │
│  │ 5. Log structured JSON      │ → python/logging_config.py               │
│  └─────────────────────────────┘                                          │
│           ↓                                                                │
│  ✅ OUTPUT: data/raw/<timestamp>_raw.parquet                              │
│     (with metadata, checksum, run_id)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: TRANSFORMATION                                                    │
│  Location: src/pipeline/transformation.py                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Config ← config/business_rules.yaml                                      │
│           (statuses, buckets, mappings)                                   │
│           ↓                                                                │
│  ┌─────────────────────────────┐                                          │
│  │ 1. Load raw data            │ ← Phase 1 output                          │
│  ├─────────────────────────────┤                                          │
│  │ 2. Apply business rules     │ ← config/business_rules.yaml             │
│  ├─────────────────────────────┤                                          │
│  │ 3. Handle nulls, outliers   │                                          │
│  ├─────────────────────────────┤                                          │
│  │ 4. Normalize types          │                                          │
│  ├─────────────────────────────┤                                          │
│  │ 5. Validate referential int │                                          │
│  └─────────────────────────────┘                                          │
│           ↓                                                                │
│  ✅ OUTPUT: data/clean/<timestamp>_clean.parquet                           │
│     (normalized, deduplicated, validated)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: CALCULATION & ENRICHMENT                                          │
│  Location: src/pipeline/calculation.py + src/kpi_engine_v2.py              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Config ← config/kpis/kpi_definitions.yaml                                │
│           (ALL KPI FORMULAS - SINGLE SOURCE OF TRUTH)                     │
│           ↓                                                                │
│  ┌─────────────────────────────┐                                          │
│  │ 1. Load clean data          │ ← Phase 2 output                          │
│  ├─────────────────────────────┤                                          │
│  │ 2. Read KPI formulas        │ ← config/kpis/kpi_definitions.yaml       │
│  ├─────────────────────────────┤                                          │
│  │ 3. Compute all metrics      │ → KPI_ENGINE_V2                          │
│  ├─────────────────────────────┤                                          │
│  │ 4. Detect anomalies         │ → HISTORICAL_BASELINE_COMPARISON         │
│  ├─────────────────────────────┤                                          │
│  │ 5. AI agent enrichment      │ → python/multi_agent/orchestrator.py     │
│  ├─────────────────────────────┤ (optional risk narratives)               │
│  │ 6. Generate audit manifest  │ → With lineage + ownership               │
│  └─────────────────────────────┘                                          │
│           ↓                                                                │
│  ✅ OUTPUT: data/metrics/<timestamp>_kpi_manifest.json                     │
│     (with full lineage, owners, thresholds, audit trail)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: OUTPUT & DISTRIBUTION                                             │
│  Location: src/pipeline/output.py                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Config ← config/pipeline.yml                                             │
│           (output formats, Supabase config, SLA timers)                   │
│           ↓                                                                │
│  ┌─────────────────────────────┐                                          │
│  │ 1. Format results           │ → Parquet, CSV, JSON                     │
│  ├─────────────────────────────┤                                          │
│  │ 2. Write to Supabase        │ → TRANSACTIONAL (idempotent)             │
│  ├─────────────────────────────┤                                          │
│  │ 3. Generate audit reports   │ → COMPLIANCE_LOGGING                     │
│  ├─────────────────────────────┤                                          │
│  │ 4. Trigger dashboard refresh│ → HTTP_HOOK                              │
│  ├─────────────────────────────┤                                          │
│  │ 5. Monitor SLA timers       │ → ALERTING                               │
│  ├─────────────────────────────┤                                          │
│  │ 6. Store run artifacts      │ → logs/runs/<timestamp>/                 │
│  └─────────────────────────────┘                                          │
│           ↓                                                                │
│  ✅ OUTPUTS:                                                               │
│     • logs/runs/<timestamp>/ (all artifacts)                              │
│     • Supabase database (persistent storage)                              │
│     • Frontend/Dashboard (live refresh)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
                    ┌──────────────┴───────────────┐
                    ↓                              ↓
            streamlit_app.py              apps/analytics/api/
            (Interactive                  (FastAPI endpoints)
             Dashboard)                   
                    ↓                              ↓
            User visualizes             Programmatic access
            KPIs, exports               to KPI results
```

---

## 🗂️ FOLDER ORGANIZATION

```
Repository Root
│
├── ✅ ACTIVE PRODUCTION (USE THESE)
│   │
│   ├── src/pipeline/                    ← CORE PIPELINE
│   │   ├── orchestrator.py              (Phases 1-4 coordinator)
│   │   ├── ingestion.py                 (Phase 1)
│   │   ├── transformation.py            (Phase 2)
│   │   ├── calculation.py               (Phase 3)
│   │   └── output.py                    (Phase 4)
│   │
│   ├── python/                          ← SUPPORT MODULES
│   │   ├── config.py                    (Config management)
│   │   ├── logging_config.py            (Structured logging)
│   │   ├── models/                      (Pydantic schemas)
│   │   └── multi_agent/                 (AI enrichment)
│   │
│   ├── config/                          ← MASTER CONFIGURATION
│   │   ├── pipeline.yml                 (Endpoints, auth, validation)
│   │   ├── business_rules.yaml          (Status mappings)
│   │   └── kpis/
│   │       └── kpi_definitions.yaml     (ALL KPI FORMULAS ← EDIT HERE!)
│   │
│   ├── scripts/
│   │   └── run_data_pipeline.py         (Entry point)
│   │
│   ├── apps/                            ← OUTPUT LAYER
│   │   ├── web/                         (Next.js frontend)
│   │   └── analytics/                   (FastAPI API)
│   │
│   ├── streamlit_app.py                 (Interactive dashboard)
│   │
│   ├── data/                            ← DATA LAYER
│   │   ├── raw/                         (Phase 1 output)
│   │   └── metrics/                     (Phase 3 output)
│   │
│   ├── logs/runs/                       ← RUN ARTIFACTS
│   │   └── <timestamp>/                 (All phase outputs + audit)
│   │
│   └── tests/                           ← TEST SUITES
│
├── 📦 ARCHIVED LEGACY (REFERENCE ONLY)
│   │
│   └── archive_legacy/                  (Old docs, scripts, experiments)
│       ├── README.md                    (Explanation)
│       ├── docs/                        (Old documentation)
│       ├── scripts/                     (Deprecated runners)
│       └── python/                      (Old implementations)
│
└── 📖 DOCUMENTATION
    ├── UNIFIED_WORKFLOW.md              (Complete guide)
    ├── QUICK_START.md                   (5-minute reference)
    ├── UNIFICATION_SUMMARY.md           (This process)
    ├── .repo-structure.json             (Machine-readable)
    ├── docs/architecture.md             (System design)
    ├── docs/OPERATIONS.md               (Runbooks)
    └── ...
```

---

## 🎯 CONFIG HIERARCHY

```
┌──────────────────────────────────────────────────────────────┐
│         MASTER CONFIGURATION SINGLE SOURCE OF TRUTH          │
└──────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ↓                     ↓                     ↓
  config/pipeline.yml   config/business_rules.yaml  config/kpis/
  ├─ Endpoints         ├─ Statuses                  └─ kpi_definitions.yaml
  ├─ Auth tokens       ├─ Buckets                     ├─ Portfolio health
  ├─ Validation rules  ├─ Constants                   ├─ Risk score
  ├─ Output formats    └─ Mappings                    ├─ Growth projects
  └─ Supabase config                                  └─ Time-series
                                                         aggregations
        │                     │                     │
        ↓                     ↓                     ↓
  Phase 1: Ingestion  Phase 2: Transform  Phase 3: Calculate
  Reads endpoints,    Reads business      Reads KPI formulas,
  auth, validation    rules for mapping   computes metrics
```

---

## 🚀 EXECUTION PATHS

### **Path 1: Manual CLI**
```
User executes: python scripts/run_data_pipeline.py
                    ↓
          orchestrator reads config/
                    ↓
          Phases 1-4 run sequentially
                    ↓
          Results in logs/runs/<timestamp>/
                    ↓
          User runs: streamlit run streamlit_app.py
                    ↓
          Views KPIs in dashboard
```

### **Path 2: GitHub Actions**
```
Scheduled trigger (.github/workflows/)
                    ↓
          Calls: scripts/run_data_pipeline.py
                    ↓
          Same as Path 1 (Phases 1-4)
                    ↓
          Results in logs/runs/<timestamp>/
                    ↓
          API notified, dashboard auto-refreshes
```

### **Path 3: API Endpoint**
```
External system calls: POST /api/pipeline/trigger
                    ↓
          apps/analytics/api/ receives request
                    ↓
          Calls: scripts/run_data_pipeline.py
                    ↓
          Same as Path 1 (Phases 1-4)
                    ↓
          Response includes run_id for status tracking
```

---

## 📊 CONFIGURATION FLOW

```
Environment Variables
  ├─ CASCADE_API_TOKEN
  ├─ SUPABASE_URL
  ├─ DATABASE_URL
  └─ ...
          ↓
      Python loads .env
          ↓
    config.py reads env
          ↓
  ┌─────────────────────────────┐
  │  Master Config Manager      │
  │  python/config.py           │
  ├─────────────────────────────┤
  │ Merges:                     │
  │ • .env (secrets)            │
  │ • config/pipeline.yml       │
  │ • config/business_rules.yml │
  │ • config/kpis/*             │
  └─────────────────────────────┘
          ↓
  Unified config object
  (used by all phases)
```

---

## 🔄 ACTIVE vs ARCHIVE

```
REPOSITORY STRUCTURE

┌─────────────────────────────────┐
│  ACTIVE (What Runs Daily)       │
├─────────────────────────────────┤
│                                 │
│  src/pipeline/          ← Core  │
│  python/                ← Libs  │
│  config/                ← Conf  │
│  scripts/               ← CLI   │
│  apps/                  ← UI    │
│  data/                  ← Data  │
│  logs/                  ← Logs  │
│  tests/                 ← QA    │
│                                 │
│  ✅ Executed daily               │
│  ✅ Maintained constantly        │
│  ✅ Tested regularly             │
│  ✅ Documented completely        │
│                                 │
└─────────────────────────────────┘

                ↓↓↓

┌─────────────────────────────────┐
│  ARCHIVE (Legacy Reference)     │
├─────────────────────────────────┤
│                                 │
│  archive_legacy/        ← Old   │
│  ├─ docs/               (Ref)   │
│  ├─ scripts/            (Deprecated)│
│  ├─ python/             (Old)   │
│  ├─ projects/           (Exp)   │
│  └─ notebooks/          (Ad-hoc)│
│                                 │
│  ❌ NOT executed                 │
│  ❌ Preserved for reference      │
│  ❌ In git history forever       │
│  ✅ Safe & isolated              │
│                                 │
└─────────────────────────────────┘
```

---

## 💡 KEY INSIGHTS

```
BEFORE UNIFICATION:
  • Repository had 92+ documents
  • Mix of active and legacy code
  • Unclear which code to run
  • Confusing folder structure
  • Multiple similar implementations
  → 😕 Developers skipped through chaos

AFTER UNIFICATION:
  • 4 clear reference documents
  • Active code in obvious locations
  • Legacy safely archived
  • One unified pipeline
  • Single source of truth (config/)
  → ✅ Developers follow clean workflow
```

---

**For complete details, see `UNIFIED_WORKFLOW.md`**
