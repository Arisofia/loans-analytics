# 🎯 QUICK START: UNIFIED WORKFLOW

**For developers who need to know the process in 5 minutes.**

---

## THE PIPELINE (4 PHASES)

```
INPUT DATA → INGESTION → TRANSFORMATION → CALCULATION → OUTPUT → DASHBOARD
   ↓             ↓              ↓                ↓          ↓         ↓
Cascade      Read data      Clean data      Compute     Save to   View KPIs
CSV API      validate        normalize       KPIs        DB/Files  metrics
             dedupe          enrich          trace       audit
```

---

## HOW TO RUN IT

### **Start Pipeline**

```bash
cd /Users/jenineferderas/abaco-loans-analytics
source .venv/bin/activate
python scripts/run_data_pipeline.py
```

### **View Results**

```bash
streamlit run streamlit_app.py
# Opens http://localhost:8501
```

### **Check Logs**

```bash
ls -la logs/runs/  # List all pipeline runs
tail -f logs/runs/latest/orchestrator.log  # Follow latest run
```

---

## THE 4 ACTIVE PHASES

| Phase            | File                             | What it does                        | Config                             |
| ---------------- | -------------------------------- | ----------------------------------- | ---------------------------------- |
| **1. Ingest**    | `src/pipeline/ingestion.py`      | Fetch Cascade data, validate        | `config/pipeline.yml`              |
| **2. Transform** | `src/pipeline/transformation.py` | Clean, normalize, enrich            | `config/business_rules.yaml`       |
| **3. Calculate** | `src/pipeline/calculation.py`    | Compute all KPIs                    | `config/kpis/kpi_definitions.yaml` |
| **4. Output**    | `src/pipeline/output.py`         | Save to DB/files, refresh dashboard | `config/pipeline.yml`              |

**Orchestrator**: `src/pipeline/orchestrator.py` (runs all 4 in sequence)

---

## MASTER CONFIGURATIONS

### `config/pipeline.yml` (Endpoints, auth, validation)

```yaml
endpoints:
  cascade:
    url: 'https://api.cascade.com/...'
    auth: '${CASCADE_API_TOKEN}'
validation:
  ingestion: { strict: true }
  calculation: { precision: 2 }
outputs:
  supabase: { enabled: true }
```

### `config/business_rules.yaml` (Status mappings, buckets)

```yaml
statuses:
  - Active
  - Delinquent
  - Charged-Off
```

### `config/kpis/kpi_definitions.yaml` (ALL KPI FORMULAS - UPDATE HERE!)

```yaml
portfolio_health:
  formula: 'avg(risk_score) weighted by loan_amount'
  owner: 'Data Team'
  threshold: 75
  alert_on_breach: true
```

---

## UPDATE KPI FORMULAS (NO CODE CHANGES!)

1. Edit: `config/kpis/kpi_definitions.yaml`
2. Add/modify formula
3. Restart pipeline
4. New KPI automatically loaded ✅

---

## DIRECTORY STRUCTURE

### ✅ ACTIVE (Use These)

```
src/pipeline/        ← Core pipeline phases
python/              ← Utilities, models, logging
config/              ← Master configuration
scripts/             ← Entry points
apps/                ← Frontend + API
data/                ← Raw input & output
tests/               ← Test suites
```

### 📦 ARCHIVE (Reference Only - Do NOT run)

```
archive_legacy/      ← Old scripts, docs, experiments
                       DO NOT USE IN PRODUCTION
```

---

## COMMON COMMANDS

```bash
# Run pipeline
python scripts/run_data_pipeline.py

# View dashboard
streamlit run streamlit_app.py

# Run tests
pytest tests/ -v

# Check pipeline status
curl http://localhost:8000/api/pipeline/status

# View latest KPIs
curl http://localhost:8000/api/kpis/latest

# Start API service
python apps/analytics/run_report.py
```

---

## WHAT EACH PROJECT DOES

| Folder             | Purpose                         | In Active Workflow? |
| ------------------ | ------------------------------- | ------------------- |
| `src/pipeline/`    | Core 4-phase pipeline           | ✅ YES - Main       |
| `python/`          | Utilities, models, logging      | ✅ YES - Support    |
| `config/`          | Configuration (SOURCE OF TRUTH) | ✅ YES - Critical   |
| `apps/web/`        | Next.js frontend dashboard      | ✅ YES - Output     |
| `apps/analytics/`  | FastAPI backend service         | ✅ YES - Output     |
| `streamlit_app.py` | Interactive dashboard           | ✅ YES - Output     |
| `scripts/`         | CLI entry points                | ✅ YES - Trigger    |
| `tests/`           | Unit & integration tests        | ✅ YES - QA         |
| `data/`            | Raw input & processed output    | ✅ YES - Data       |
| `archive_legacy/`  | Old code, deprecated scripts    | ❌ NO - Archive     |

---

## TROUBLESHOOTING

| Problem              | Check                              | Fix                      |
| -------------------- | ---------------------------------- | ------------------------ |
| Pipeline fails       | `logs/runs/*/`                     | Read error message       |
| KPI wrong            | `config/kpis/kpi_definitions.yaml` | Update formula           |
| Dashboard won't load | Streamlit logs                     | Check DB connection      |
| API timeout          | `config/pipeline.yml`              | Increase timeout         |
| Config not loaded    | Restart pipeline                   | Config reloaded on start |

---

## FILES YOU MIGHT EDIT

- ✏️ `config/kpis/kpi_definitions.yaml` - New KPI formula? Edit here
- ✏️ `config/business_rules.yaml` - New status? Edit here
- ✏️ `config/pipeline.yml` - New endpoint? Edit here
- ✏️ `.env` - Add secrets here (never in code!)
- ❌ Don't edit: `src/pipeline/*.py`, `python/`, `apps/` (unless bug fix)

---

## KEY DOCUMENTS

| Document                   | Purpose                                  |
| -------------------------- | ---------------------------------------- |
| `UNIFIED_WORKFLOW.md`      | **Read this first** - Full process guide |
| `docs/architecture.md`     | System design details                    |
| `docs/OPERATIONS.md`       | Deployment, monitoring, incidents        |
| `docs/DATA_DICTIONARY.md`  | Data field definitions                   |
| `archive_legacy/README.md` | What's in the archive & why              |

---

## EXAMPLE: ADD NEW KPI

**Goal**: Track "average_days_outstanding"

**Steps**:

1. Open: `config/kpis/kpi_definitions.yaml`
2. Add:
   ```yaml
   average_days_outstanding:
     formula: 'mean(current_date - payment_date)'
     owner: 'Your Name'
     threshold: 90
     alert_on_breach: true
   ```
3. Save file
4. Run: `python scripts/run_data_pipeline.py`
5. Check: `streamlit run streamlit_app.py`
6. ✅ New KPI appears in dashboard!

**No code changes needed.** Config-driven design. 🎯

---

## SUMMARY

✅ **Know where to look**: Active folders have production code  
✅ **Know what runs**: Pipeline executes 4 phases sequentially  
✅ **Know how to update**: Edit config files, not code  
✅ **Know what's old**: Archive folder has legacy content (don't use)  
✅ **Know where to start**: `scripts/run_data_pipeline.py`

**Ready to execute.**

---

_Questions? See `UNIFIED_WORKFLOW.md` for complete guide._
