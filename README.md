# Ábaco Loans Analytics Platform

[![Pipeline](https://img.shields.io/badge/Pipeline-Operational-brightgreen)]()
[![KPIs](https://img.shields.io/badge/KPIs-40%2B_Production-blue)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![Tests](https://img.shields.io/badge/Tests-1027%2B_Passing-success)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

Production-grade lending analytics platform powering portfolio intelligence for factoring and credit operations. Built with financial-precision engineering (Decimal arithmetic, SSOT asset quality, PII redaction) and institutional-level KPI methodology.

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                     │
│   Google Sheets (DESEMBOLSOS) ─── CSV Upload ─── Supabase          │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  PHASE 1        │
         │  Ingestion      │  Google Sheets API / CSV / Parquet
         └────────┬────────┘
         ┌────────▼────────┐
         │  PHASE 2        │
         │  Transformation │  Column normalization, DPD calc, status mapping
         └────────┬────────┘
         ┌────────▼────────┐
         │  PHASE 3        │
         │  Calculation    │  40+ KPIs, EL, Roll Rates, Vintage, HHI, Clustering
         └────────┬────────┘
         ┌────────▼────────┐
         │  PHASE 4        │
         │  Output         │  Parquet/CSV/JSON exports, Supabase, Dashboard
         └────────┴────────┘
                  │
    ┌─────────────┼─────────────────┐
    ▼             ▼                 ▼
 Streamlit    Multi-Agent       ML Models
 Dashboard    (9 agents,       (XGBoost PD,
              22 scenarios)    Scorecard)
```

## KPI Methodology

All KPIs are calculated from **real production data only** — no dummy, sample, or demo data is used in calculations. Data flows exclusively from Google Sheets import or CSV pipeline input.

### Core Asset Quality (SSOT — Single Source of Truth)
| KPI | Formula | Precision |
|-----|---------|-----------|
| PAR 30/60/90 | `Σ(balance where DPD ≥ N) / Σ(total_balance) × 100` | Decimal, ROUND_HALF_UP |
| NPL Ratio | `Σ(balance where status = defaulted) / Σ(total_balance) × 100` | Decimal |
| Default Rate | `COUNT(defaulted) / COUNT(total) × 100` | Decimal |
| Loss Rate | `Σ(written_off) / Σ(disbursed) × 100` | Decimal |
| LGD | `1 - recovery_rate` (from `business_parameters.yml`: 10%) | Decimal |

### Expected Loss (Basel-aligned)
| KPI | Formula |
|-----|---------|
| Expected Loss (EL) | `Σ(PD_i × LGD × EAD_i)` per loan |
| EL Rate | `EL / Σ(EAD) × 100` |
| Weighted Avg PD | `Σ(PD_i × EAD_i) / Σ(EAD_i)` |

PD assignment uses DPD-based risk mapping: Current=0.5%, 30DPD=5%, 60DPD=15%, 90DPD=35%, 180+=70%, Defaulted=100%.

### Portfolio Intelligence
| KPI | Description |
|-----|-------------|
| Roll Rates | DPD bucket migration matrix (Current→30→60→90→NPL) |
| Vintage Analysis | Default/PAR30 rates by origination cohort (monthly) |
| Concentration HHI | Herfindahl-Hirschman Index with Top-1/5/10/20 obligor analysis |
| Recurrent TPV | New/Recurrent/Recovered client volume tracking (NSM) |
| UMAP+HDBSCAN Cohorts | Alfa/Beta/Gamma/Delta risk clustering |

### Financial Metrics
| KPI | Source |
|-----|--------|
| NIM (Net Interest Margin) | `unit_economics.py` |
| Cost of Risk | `unit_economics.py` |
| PPC/PPP (Collection/Payment Periods) | `holding_financial_indicators.py` |
| Cash Conversion Cycle | `holding_financial_indicators.py` |
| Debt Covenants (D/EBITDA, DSCR) | `holding_financial_indicators.py` |
| Liquidity Reserve | `holding_financial_indicators.py` |

### Segment Analytics
All KPIs computed across 7 dimensions: Company, Credit Line, KAM Hunter, KAM Farmer, Government Entity, Industry, Document Type.

## Data Sources

| Source | Connection | Status |
|--------|-----------|--------|
| Google Sheets | Service Account (`abaco-pipeline@...`) via Spreadsheet ID | Production |
| CSV Upload | Pipeline `--input` flag or Streamlit upload | Production |
| Supabase | PostgreSQL via `SUPABASE_URL` + `SUPABASE_KEY` | Optional |

**Pipeline ingestion requires explicit real input. Dummy/sample fallback is disabled.**

## Quick Start

```bash
# Clone
git clone https://github.com/Arisofia/loans-analytics.git
cd loans-analytics

# Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run pipeline (Google Sheets — production)
python3 scripts/data/run_data_pipeline.py --mode full

# Run pipeline (CSV input)
python3 scripts/data/run_data_pipeline.py \
  --input data/raw/your_file.csv --mode full

# Launch dashboard
streamlit run frontend/streamlit_app/app.py

# Quality & testing
make test           # 1027+ tests
make lint           # Code quality
make type-check     # Static type analysis
make format         # Auto-format
```

## Repository Structure

```
backend/
├── src/pipeline/           # 4-phase ETL pipeline
│   ├── orchestrator.py     # Pipeline orchestration
│   ├── ingestion.py        # Google Sheets / CSV / Parquet ingestion
│   ├── transformation.py   # Column normalization, DPD, status mapping
│   ├── calculation.py      # 40+ KPIs, EL, roll rates, vintage, HHI
│   └── output.py           # Export: Parquet/CSV/JSON, Supabase
├── python/
│   ├── kpis/
│   │   ├── engine.py              # KPIEngineV2 (SSOT, Decimal, audit trail)
│   │   ├── ssot_asset_quality.py  # Single Source of Truth PAR/NPL
│   │   ├── unit_economics.py      # NPL, LGD, Cost of Risk, NIM
│   │   ├── holding_financial_indicators.py  # EEFF: PPC/PPP, covenants
│   │   ├── formula_engine.py      # Dynamic KPI formula evaluation
│   │   ├── ltv.py                 # LTV Sintético
│   │   └── collection_rate.py     # Collection rate calculator
│   ├── multi_agent/
│   │   ├── orchestrator.py  # 22 scenarios, 9 agent roles
│   │   ├── protocol.py      # Agent communication protocol
│   │   └── guardrails.py    # PII redaction, input sanitization
│   └── models/
│       └── default_risk_model.py  # XGBoost PD model

config/
├── business_rules.yaml       # Status mappings, DPD buckets, risk categories
├── business_parameters.yml   # Financial guardrails, 2026 targets
├── pipeline.yml              # Pipeline configuration
└── kpis/kpi_definitions.yaml # 40+ KPI formulas and thresholds

frontend/streamlit_app/
├── app.py                         # Executive dashboard
├── pages/
│   ├── 1_New_Analysis.py          # Fresh analysis entry
│   ├── 2_Agent_Insights.py        # Multi-agent output viewer
│   ├── 3_Portfolio_Dashboard.py   # Portfolio deep-dive
│   ├── 4_Usage_Metrics.py         # Platform usage tracking
│   ├── 5_Monitoring_Control.py    # Real-time monitoring
│   ├── 6_Historical_Context.py    # Trend analysis
│   ├── 7_Predictive_Analytics.py  # XGBoost PD model control room
│   ├── 8_Risk_Intelligence.py     # EL, Roll Rates, Vintage, HHI
│   └── 9_Capital_Economics.py     # Unit economics, profitability

models/
├── risk/          # Risk model artifacts
└── scorecard/     # Credit scorecard

scripts/
├── data/          # Pipeline entrypoints
├── monitoring/    # Observability automation
├── ml/            # ML training pipelines
└── maintenance/   # Database maintenance
```

## Output Artifacts

Pipeline runs → `logs/runs/<run_id>/`:

| File | Content |
|------|---------|
| `kpis_output.parquet` | Full KPI results (Parquet) |
| `kpis_output.csv` | KPI results (CSV) |
| `kpis.json` | KPI results (JSON) |
| `segment_kpis.json` | KPIs by 7 dimensions |
| `expected_loss.json` | EL = PD × LGD × EAD analysis |
| `roll_rates.json` | DPD bucket migration matrix |
| `vintage_analysis.json` | Cohort default/PAR rates |
| `concentration_hhi.json` | HHI and obligor concentration |
| `clustering_metrics.json` | UMAP+HDBSCAN cohort analysis |
| `nsm_recurrent_tpv_output.json` | Recurrent client TPV |
| `anomalies.json` | KPI anomaly detection |
| `audit_metadata.json` | Full audit trail |

## Multi-Agent System

9 specialized agents across 22 analytical scenarios:

| Agent | Role |
|-------|------|
| Risk Analyst | Asset quality, delinquency, PD assessment |
| Growth Strategist | Portfolio expansion, market opportunity |
| Ops Optimizer | Operational efficiency, SLA compliance |
| Compliance | Regulatory, governance, audit readiness |
| Collections | Workout strategies, recovery optimization |
| Fraud Detection | Anomaly patterns, fraud indicators |
| Pricing | Rate optimization, spread analysis |
| Customer Retention | Churn prevention, loyalty metrics |
| Database Designer | Schema optimization, query performance |

Providers: OpenAI, Anthropic, Gemini, Grok (xAI-compatible).

## CI/CD & Security

| Workflow | Purpose |
|----------|---------|
| `.github/workflows/tests.yml` | Test suite (1027+ tests) |
| `.github/workflows/pr-checks.yml` | PR quality gates |
| `.github/workflows/security-scan.yml` | Snyk + dependency audit |

## Engineering Standards

- **Financial precision**: `Decimal` arithmetic for all monetary calculations
- **SSOT asset quality**: Single calculation path for PAR/NPL across pipeline
- **PII protection**: All LLM inputs sanitized via `guardrails.py`
- **Audit trail**: Every KPI calculation logged with run_id, actor, timestamp
- **No dummy data**: Pipeline rejects synthetic fallback; real input required

## Documentation

| Document | Purpose |
|----------|---------|
| [Setup Guide](docs/SETUP_GUIDE_CONSOLIDATED.md) | Full environment setup |
| [Operations](docs/OPERATIONS.md) | Runbooks and procedures |
| [Governance](docs/GOVERNANCE.md) | Data governance framework |
| [Observability](docs/OBSERVABILITY.md) | Monitoring and alerting |
| [Security](docs/SECURITY.md) | Security policies |
| [KPI Dictionary](docs/KPI.md) | KPI definitions and methodology |
| [Script Map](docs/operations/SCRIPT_CANONICAL_MAP.md) | Canonical command reference |
| [Deployment](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) | Production deployment |

## License

Proprietary — Ábaco Financial Services.

