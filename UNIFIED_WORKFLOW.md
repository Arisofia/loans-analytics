# 🔄 UNIFIED PRODUCTION WORKFLOW

**Status**: ✅ ACTIVE (Production) | **Version**: v2.0 | **Updated**: January 29, 2026

---

## 📊 PROCESS OVERVIEW

**Single Sequential Pipeline** from data ingestion to dashboard visualization.

```
INPUT                PHASE 1          PHASE 2            PHASE 3               PHASE 4             OUTPUT
CSV/API         Ingestion &      Transformation     KPI Calculation      Output Layer        Dashboard
                Validation       & Normalization    & Enrichment         (Persistence)       Visualization
  ↓                  ↓                  ↓                  ↓                   ↓                  ↓
[Cascade]  →   [Raw Data]   →   [Clean Data]  →  [Analytics Ready] → [Supabase/Files] → [Frontend/Streamlit]
 Export         with audit         normalized       with lineage         with metadata      KPI metrics
             checksum & logs       validated        aggregated            and freshness       Portfolio
                                  deduplicated      timestamped           SLA monitored       Health Risk
```

---

## 🎯 ACTIVE FOLDERS (PRODUCTION WORKFLOW)

### 1️⃣ **EXECUTION ENTRY POINT**

- **File**: `scripts/run_data_pipeline.py`
- **Purpose**: Main CLI entry point for pipeline execution
- **Triggers**: Manual execution, GitHub Actions, scheduled jobs, webhooks
- **Command**:
  ```bash
  python scripts/run_data_pipeline.py --config config/pipeline.yml [--mode validate|publish]
  ```

### 2️⃣ **CORE PIPELINE ORCHESTRATION**

- **Location**: `src/pipeline/`
- **Modules**:
  - `orchestrator.py` - Coordinates all 4 phases
  - `ingestion.py` - Data collection (Phase 1)
  - `transformation.py` - Data cleaning (Phase 2)
  - `calculation.py` - KPI computation (Phase 3)
  - `output.py` - Result distribution (Phase 4)
  - `config.py` - Configuration management

### 3️⃣ **PHASE 1: INGESTION**

- **Active File**: `src/pipeline/ingestion.py`
- **Support**: `python/models/cascade_schemas.py`
- **Configuration**: `config/pipeline.yml` (endpoints, auth, validation)

**Flow**:

```
1. Read config (endpoints, auth tokens, validation rules)
2. Make HTTP request to Cascade API with retries & rate limiting
3. Validate response schema against Pydantic models
4. Check for duplicates using immutable hashes
5. Persist raw data with timestamp + checksum
6. Log all operations (trace_id, run_id) as structured JSON
```

**Output**: `data/raw/<timestamp>_raw.parquet` (with metadata)

---

### 4️⃣ **PHASE 2: TRANSFORMATION**

- **Active File**: `src/pipeline/transformation.py`
- **Support**: `config/business_rules.yaml`
- **Models**: `python/models/` (Pydantic schemas)

**Flow**:

```
1. Load raw data from Phase 1
2. Apply business rules (status mappings, bucket calculations)
3. Handle null values, outliers, type conversions
4. Validate referential integrity (loans ↔ cashflows ↔ customers)
5. Mask PII if required
6. Generate transformation audit log
```

**Output**: `data/clean/<timestamp>_clean.parquet` (normalized, deduplicated)

---

### 5️⃣ **PHASE 3: KPI CALCULATION & ENRICHMENT**

- **Active Files**:
  - `src/pipeline/calculation.py`
  - `src/kpi_engine_v2.py`
- **KPI Definitions**: `config/kpis/kpi_definitions.yaml` (SOURCE OF TRUTH)
- **AI Enhancement**: `python/multi_agent/orchestrator.py`

**Flow**:

```
1. Load clean data from Phase 2
2. Read KPI formulas from config/kpis/kpi_definitions.yaml
3. Calculate all metrics:
   - Portfolio health scores
   - Risk rankings
   - Growth projections
   - Time-series aggregations (daily/weekly/monthly)
4. Detect anomalies vs historical baselines
5. Enrich with AI agent insights (optional)
6. Generate calculation manifest with lineage & thresholds
```

**Output**: `data/metrics/<timestamp>_kpi_manifest.json` (with full lineage)

---

### 6️⃣ **PHASE 4: OUTPUT & DISTRIBUTION**

- **Active Files**:
  - `src/pipeline/output.py`
  - `apps/analytics/api/main.py` (FastAPI)
  - `streamlit_app.py` (Dashboard)

**Flow**:

```
1. Format results (Parquet, CSV, JSON)
2. Write to Supabase database (transactional, idempotent)
3. Trigger dashboard refresh endpoints
4. Generate audit/compliance reports
5. Monitor SLA timers and alert if breached
6. Store all artifacts in logs/runs/<timestamp>/
```

**Outputs**:

- `logs/runs/<timestamp>/` - Run directory with all artifacts
- Supabase tables - For persistent storage & historical trending
- `streamlit_app.py` - Live dashboard refresh

---

## 📁 MASTER CONFIGURATION (SINGLE SOURCE OF TRUTH)

### `config/pipeline.yml`

```yaml
endpoints:
  cascade:
    url: 'https://api.cascade.com/...'
    auth: '${CASCADE_API_TOKEN}' # From env
    rate_limit: 100 # req/sec
    retry_count: 3

validation:
  ingestion:
    strict: true
  transformation:
    enforce_types: true
  calculation:
    precision: 2 decimal places

kpi_formulas:
  portfolio_health: 'calculation.py::compute_portfolio_health'
  risk_score: 'kpi_engine_v2.py::calculate_risk'

outputs:
  formats: ['parquet', 'csv', 'json']
  supabase:
    enabled: true
    tables: ['kpi_results', 'audit_logs']
```

### `config/business_rules.yaml`

- Status mappings (Active, Delinquent, Charged-Off, etc.)
- Bucket definitions (Loan amounts, terms)
- Constants and thresholds

### `config/kpis/kpi_definitions.yaml`

- **EVERY KPI FORMULA DEFINED HERE**
- Example:
  ```yaml
  portfolio_health:
    formula: 'avg(risk_score) weighted by loan_amount'
    owner: 'Data Team'
    threshold: 75
    alert_on_breach: true
  ```

---

## 🚀 HOW TO TRIGGER PIPELINE

### **Option 1: Manual CLI**

```bash
cd /Users/jenineferderas/abaco-loans-analytics
source .venv/bin/activate
python scripts/run_data_pipeline.py
```

### **Option 2: GitHub Actions (Scheduled)**

- **Workflow**: `.github/workflows/`
- **Trigger**: Daily at 02:00 UTC
- **Status**: Check GitHub Actions tab

### **Option 3: API Endpoint**

```bash
curl -X POST http://localhost:8000/api/pipeline/trigger \
  -H "Content-Type: application/json"
```

### **Option 4: Webhook (Cascade)**

- Configured in `config/pipeline.yml`
- Triggers on Cascade data updates

---

## 📊 VIEWING RESULTS

### **Option 1: Streamlit Dashboard**

```bash
streamlit run streamlit_app.py
# Opens http://localhost:8501
```

### **Option 2: FastAPI Endpoints**

```bash
# Start API service
python apps/analytics/run_report.py

# Fetch latest KPIs
curl http://localhost:8000/api/kpis/latest

# Trigger new run
curl -X POST http://localhost:8000/api/pipeline/trigger
```

### **Option 3: Raw Artifacts**

- **All run outputs**: `logs/runs/<TIMESTAMP>/`
- **Latest KPI results**: `data/metrics/` (Parquet/CSV/JSON)
- **Supabase database**: Direct query via Supabase Studio

---

## 🔍 MONITORING & OBSERVABILITY

### **Logging**

- **Location**: `logs/runs/<run_id>/`
- **Format**: Structured JSON (trace_id, span_id, severity)
- **Tool**: `python/logging_config.py` configures all logging

### **Distributed Tracing**

- **Tool**: OpenTelemetry + Azure Application Insights
- **Setup**: See `docs/TRACING_OBSERVABILITY.md`
- **Traces all**: Ingestion, transformation, calculation, output phases

### **Metrics & Alerts**

- **SLA Timers**: Enforced in Phase 4
- **Data Quality Scores**: Included in every run manifest
- **Alert Thresholds**: Defined in `config/kpis/kpi_definitions.yaml`

---

## 🔧 UPDATING KPI FORMULAS

### **No code changes needed!**

1. Edit: `config/kpis/kpi_definitions.yaml`
2. Add/modify KPI formula
3. Restart pipeline → Automatically loads new config
4. Done ✅

**Example**:

```yaml
new_metric:
  formula: 'custom_calculation(column_a, column_b)'
  owner: 'Your Name'
  threshold: 50
  alert_on_breach: true
```

---

## 📝 TESTING

### **Unit Tests**

```bash
pytest tests/ -v
pytest tests/test_ingestion_extra.py  # Phase 1
pytest tests/test_transformation.py   # Phase 2
pytest tests/test_kpi_calculation.py  # Phase 3
```

### **Integration Tests**

```bash
pytest tests/integration/ -v
```

### **Pipeline Validation**

```bash
python scripts/run_data_pipeline.py --mode validate
```

---

## ⚠️ OPERATIONAL RUNBOOKS

See: `docs/OPERATIONS.md`

### **Common Issues**

| Issue                | Location           | Solution                            |
| -------------------- | ------------------ | ----------------------------------- |
| Pipeline fails       | `logs/runs/<id>/`  | Check error logs + Phase logs       |
| KPI mismatch         | `config/kpis/`     | Verify formula in YAML              |
| Supabase write fails | Phase 4 logs       | Check credentials in `.env`         |
| Dashboard won't load | `streamlit_app.py` | Restart + check Supabase connection |
| API timeout          | `apps/analytics/`  | Increase `timeout` in config        |

---

## 📚 ARCHITECTURE DOCUMENTATION

- **System Overview**: `docs/architecture.md`
- **Pipeline Spec**: `docs/PIPELINE_UNIFICATION_PLAN.md`
- **Operations Guide**: `docs/OPERATIONS.md`
- **Monitoring Setup**: `docs/TRACING_OBSERVABILITY.md`
- **Data Dictionary**: `docs/DATA_DICTIONARY.md`

---

## 🗂️ ORGANIZED STRUCTURE

### ✅ ACTIVE (Production Workflow)

```
/
├── src/pipeline/              ← Core pipeline (phases 1-4)
├── python/                    ← Utilities, models, agents
├── config/                    ← Master configuration
├── scripts/                   ← Entry points
├── apps/                      ← Frontend + API
├── data/                      ← Raw input & processed output
├── logs/                      ← Run artifacts
└── tests/                     ← Test suites
```

### 📦 ARCHIVED (Legacy - DO NOT USE)

```
/archive_legacy/
├── docs/                      ← Old documentation
├── scripts/                   ← Deprecated runners
├── python/                    ← Old implementations
├── projects/                  ← Experimental work
└── notebooks/                 ← Ad-hoc analysis
```

**All legacy content is preserved in git history and safely isolated.**

---

## ✨ SUMMARY

| Component       | Location                         | Purpose             | Trigger             |
| --------------- | -------------------------------- | ------------------- | ------------------- |
| **Entry Point** | `scripts/run_data_pipeline.py`   | Start pipeline      | Manual/API/Schedule |
| **Ingestion**   | `src/pipeline/ingestion.py`      | Fetch data          | Phase 1             |
| **Transform**   | `src/pipeline/transformation.py` | Clean data          | Phase 2             |
| **Calculate**   | `src/pipeline/calculation.py`    | Compute KPIs        | Phase 3             |
| **Output**      | `src/pipeline/output.py`         | Distribute results  | Phase 4             |
| **Config**      | `config/pipeline.yml`            | Master settings     | All phases          |
| **Dashboard**   | `streamlit_app.py`               | View results        | Manual              |
| **API**         | `apps/analytics/`                | Programmatic access | Always running      |

---

**🎯 MISSION**: Keep pipeline clean, simple, and production-ready.  
**✅ STATUS**: All projects organized by process flow.  
**🚀 READY**: Execute, monitor, update config, repeat.
