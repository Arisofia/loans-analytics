# Loans Analytics — Decision Intelligence Platform

[![Pipeline](https://img.shields.io/badge/Pipeline-Operational-brightgreen)]()
[![KPIs](https://img.shields.io/badge/KPIs-40%2B_Production-blue)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue)]()
[![Tests](https://img.shields.io/badge/Tests-CI_Verified-success)]()
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
         └────────┬────────┘
         ┌────────▼────────┐
         │  PHASE 5        │
         │  Decision       │  15 AI agents, data marts, scenario engine,
         │  Intelligence   │  feature store, decision orchestrator
         └────────┴────────┘
                  │
    ┌─────────────┼─────────────────┐
    ▼             ▼                 ▼
 Streamlit    Multi-Agent       ML Models
 Dashboard    (15 decision +   (XGBoost PD,
 (10 pages)   9 LLM agents)    Scorecard)
```

## Decision Intelligence Platform

Phase 5 transforms raw analytics into **controlled action selection** — answering: What is deteriorating? What is most profitable? What should we stop? What should we scale? What must be approved now?

### Architecture Layers

| Layer | Purpose | Components |
|-------|---------|------------|
| 0 — Data Quality | Gate-keep data integrity | `data_quality_agent` |
| 1 — Risk Foundation | Risk metrics & vintage analysis | `risk`, `cohort_vintage`, `concentration` |
| 2 — Margin & Segmentation | Pricing, segments, sales | `pricing`, `segmentation`, `sales` |
| 3 — Operations | Collections, marketing, liquidity, covenants | `collections`, `marketing`, `liquidity`, `covenant` |
| 4 — Strategy | Revenue, retention, executive narrative | `revenue_strategy`, `retention`, `narrative` |
| 5 — CFO | Capital adequacy, covenant & ROE oversight | `cfo` |

### Decision Flow

```
Canonical DataFrame → Data Marts (6) → Feature Store → Metrics Registry
                                                              │
                                      Scenario Engine ────────┤
                                      (base/downside/stress)  │
                                                              ▼
                                      Decision Orchestrator ──→ DecisionCenterState
                                      (15 agents, topological │
                                       order, conflict         ▼
                                       resolution)       AI Decision Center
                                                         (Streamlit page 10)
```

### Priority Hierarchy

Agents resolve conflicts using priority rules — higher priority agents block lower ones:

1. **Data Integrity** — data_quality (blocks all if score < 0.85)
2. **Regulatory / Covenant** — covenant (blocks growth agents on breach)
3. **Liquidity** — liquidity (stress-scenario aware)
4. **Risk** — risk, cohort_vintage, concentration
5. **Margin** — pricing, revenue_strategy
6. **Growth** — sales, marketing, retention
7. **Expansion** — segmentation, narrative

## KPI Methodology

All KPIs are calculated from **real production data only** — no dummy, sample, or demo data is used in calculations. Data flows exclusively from Google Sheets import or CSV pipeline input.

### Core Asset Quality (SSOT — Single Source of Truth)
| KPI | Formula | Precision |
|-----|---------|-----------|
| PAR 30/60/90 | `Σ(balance where DPD ≥ N) / Σ(total_balance) × 100` | Decimal, ROUND_HALF_UP |
| NPL Ratio | `Σ(balance where DPD ≥ 90 OR status = defaulted) / Σ(total_balance) × 100` | Decimal |
| NPL 90 Ratio | `Σ(balance where DPD ≥ 90) / Σ(total_balance) × 100` | Decimal |
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
| NIM (Net Interest Margin, proxy) | `config/kpis/kpi_definitions.yaml` = `(AVG(interest_rate) - 0.08) * 100` |
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
| Google Sheets | Service Account (pipeline SA) via Spreadsheet ID | Production |
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
make test           # Full project suite
make lint           # Code quality
make type-check     # Static type analysis
make format         # Auto-format
```

## CI Runtime Guarantees (Applied)

- Python environment is standardized with `actions/setup-python@v4` and `cache: "pip"` in CI workflows.
- DB-backed jobs run with local `postgres:16-alpine` service and an explicit `pg_isready` readiness gate before tests/pipeline execution.
- ETL pipeline job explicitly installs `sentry-sdk` after lockfile dependency install to avoid runtime import failures.

## Repository Structure

```
backend/
├── src/pipeline/           # 5-phase ETL + Decision pipeline
│   ├── orchestrator.py     # Pipeline orchestration (Phases 1-5)
│   ├── ingestion.py        # Google Sheets / CSV / Parquet ingestion
│   ├── transformation.py   # Column normalization, DPD, status mapping
│   ├── calculation.py      # 40+ KPIs, EL, roll rates, vintage, HHI
│   ├── output.py           # Export: Parquet/CSV/JSON, Supabase
│   └── decision_phase.py   # Phase 5: Decision Intelligence bridge
├── src/contracts/          # Pydantic data contracts
│   ├── raw_schema.py       # RawLoanRecord (post-ingestion)
│   ├── mart_schema.py      # 6 domain mart record models
│   ├── metric_schema.py    # MetricResult envelope
│   ├── agent_schema.py     # AgentOutput, DecisionCenterState
│   ├── types.py            # Type aliases (RunId, MetricId, AgentId, MartBundle)
│   └── report_schema.py    # ExecutiveBrief, InvestorSummary, LenderPack, WeeklyMemo
├── src/marts/              # Data mart builders (one per domain)
│   ├── builder.py          # Utility helpers
│   ├── portfolio_mart.py   # Loan-level mart
│   ├── finance_mart.py     # P&L / balance sheet mart
│   ├── sales_mart.py       # Origination / KAM mart
│   ├── marketing_mart.py   # Channel / campaign mart
│   ├── collections_mart.py # Delinquency / recovery mart
│   ├── treasury_mart.py    # Aggregate cash-flow mart
│   └── build_all_marts.py  # Assembly entrypoint (all 6)
├── src/semantic/           # Semantic metrics layer
│   ├── metrics_registry.py # MetricsRegistry (loads YAML)
│   ├── metric_contracts.py # MetricContract, ThresholdBand, MetricUnit
│   ├── business_dimensions.py # 9 standard business dimensions
│   └── semantic_resolver.py   # Resolve raw → contracted metrics
├── src/kpi_engine/         # KPI Engine v3 (Decimal, modular)
│   ├── risk.py             # PAR, NPL, default, EL, roll rates, cure
│   ├── revenue.py          # AUM, yield, NIM, collection rate
│   ├── liquidity.py        # Liquidity ratio, funding utilization
│   ├── concentration.py    # HHI, top-N obligor analysis
│   ├── unit_economics.py   # Avg ticket, repeat rate, contribution margin
│   ├── cohorts.py          # Vintage cohort builder
│   ├── capital.py          # D/E, leverage, ROE, ROA, ROCE
│   ├── covenants.py        # Eligible ratio, aging compliance, capital gap
│   └── engine.py           # Unified run_metric_engine() facade
├── src/scenario_engine/    # Scenario projection engine
│   ├── engine.py           # ScenarioEngine class + ScenarioResult
│   ├── assumptions.py      # YAML-driven assumption loader
│   ├── base_case.py        # Base case scenario runner
│   ├── downside_case.py    # Downside scenario with risk triggers
│   └── stress_case.py      # Stress test with extreme triggers
├── src/data_quality/       # Data quality gate engine
│   ├── rules.py            # Severity enum, Rule/RuleResult dataclasses
│   ├── validators.py       # 5 built-in validators
│   ├── anomaly_detection.py # Z-score + IQR outlier detection
│   ├── blocking_policy.py  # BLOCKING severity enforcement
│   └── engine.py           # run_quality_engine() facade
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
│   │   ├── orchestrator.py         # LLM-based: 22 scenarios, 9 agent roles
│   │   ├── protocol.py             # Agent communication protocol
│   │   ├── guardrails.py           # PII redaction, input sanitization
│   │   ├── decision_orchestrator.py # Backward-compat monolithic orchestrator
│   │   ├── orchestrator/           # Modular decision orchestrator subpackage
│   │   │   ├── decision_orchestrator.py # Main orchestrator (15+ agents)
│   │   │   ├── priority_rules.py       # 7-level priority hierarchy
│   │   │   ├── dependency_graph.py     # Topological sort (Kahn's)
│   │   │   └── action_router.py        # Handler registry + routing
│   │   ├── agents/                 # Decision intelligence agents
│   │   │   ├── decision_agent_base.py  # ABC base + AgentContext
│   │   │   ├── data_quality_agent.py   # Layer 0: data gate-keep
│   │   │   ├── risk_agent.py           # Layer 1: PAR/NPL/EL
│   │   │   ├── cohort_vintage_agent.py # Layer 1: vintage analysis
│   │   │   ├── concentration_agent.py  # Layer 1: HHI, top-N
│   │   │   ├── pricing_agent.py        # Layer 2: yield/NIM/margin
│   │   │   ├── segmentation_agent.py   # Layer 2: segment profiles
│   │   │   ├── sales_agent.py          # Layer 2: disbursement targets
│   │   │   ├── collections_agent.py    # Layer 3: collection rate
│   │   │   ├── marketing_agent.py      # Layer 3: channel analysis
│   │   │   ├── liquidity_agent.py      # Layer 3: stress-aware
│   │   │   ├── covenant_agent.py       # Layer 3: 7-covenant check
│   │   │   ├── revenue_strategy_agent.py # Layer 4: NIM strategy
│   │   │   ├── retention_agent.py      # Layer 4: repeat customers
│   │   │   ├── narrative_agent.py      # Layer 4: executive narrative
│   │   │   └── cfo_agent.py            # Layer 5: CFO oversight
│   │   ├── registry/
│   │   │   ├── agents.yaml         # 16 agent definitions
│   │   │   ├── surfaces.yaml       # 7 output surfaces
│   │   │   ├── ownership.yaml      # Team ownership map
│   │   │   └── cadences.yaml       # Execution cadences
│   │   └── feature_store/          # Feature engineering
│   │       ├── loan_features.py    # Per-loan features
│   │       ├── customer_features.py # Per-customer aggregates
│   │       ├── segment_features.py # Ticket/risk segments
│   │       ├── campaign_features.py # Marketing channel features
│   │       ├── treasury_features.py # Cash-flow features
│   │       └── builder.py          # Feature orchestrator
│   ├── apps/analytics/api/
│   │   ├── main.py                # FastAPI app (20+ endpoints + decision routes)
│   │   ├── service.py             # KPIService (portfolio analytics)
│   │   ├── models.py             # Pydantic API models
│   │   └── routes/               # Decision Intelligence API
│   │       ├── metrics.py        # /decision/metrics/run
│   │       ├── agents.py         # /decision/agents/*
│   │       ├── decisions.py      # /decision/center/run
│   │       ├── scenarios.py      # /decision/scenarios/*
│   │       ├── reports.py        # /decision/reports/*
│   │       └── quality.py        # /decision/quality/run
│   └── models/
│       └── default_risk_model.py  # XGBoost PD model

config/
├── business_rules.yaml       # Status mappings, DPD buckets, risk categories
├── business_parameters.yml   # Financial guardrails, 2026 targets
├── pipeline.yml              # Pipeline configuration
├── kpis/kpi_definitions.yaml # 40+ KPI formulas and thresholds
├── metrics/metric_registry.yaml # 20 semantic metric definitions
└── scenarios/scenario_assumptions.yaml # Base/downside/stress assumptions

frontend/streamlit_app/
├── app.py                         # Executive dashboard
├── decision_api_client.py         # Decision Intelligence API client
├── decision_loader.py             # Pipeline artefact loaders
├── components/
│   ├── alert_cards.py             # Alert card components
│   ├── decision_table.py          # Prioritised action table
│   ├── scenario_strip.py          # Side-by-side scenario cards
│   └── confidence_badge.py        # Confidence level badge
├── pages/
│   ├── 01_Executive_Command_Center.py  # Business state + KPI strip
│   ├── 02_Risk_Intelligence.py         # Risk metrics, EL, vintage
│   ├── 03_Collections_Operations.py    # Collection rate, cures
│   ├── 04_Treasury_Liquidity.py        # Cash-flow, liquidity
│   ├── 05_Sales_Growth.py              # Origination, KAM tracking
│   ├── 06_Agent_Insights.py            # Agent output viewer
│   ├── 07_Scenario_Engine.py           # Base/downside/stress
│   ├── 08_Reports_Center.py            # Report generation
│   ├── 09_Data_Quality.py              # DQ rules, anomalies
│   └── 10_AI_Decision_Center.py        # Decision Intelligence dashboard

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
| `decision/decision_center_state.json` | Decision Intelligence output (Phase 5) |
| `decision/data_quality.json` | Data quality rule results & anomalies |
| `decision/metrics.json` | Unified metric engine output |

## Decision Intelligence API

The FastAPI application exposes decision intelligence via `/decision/*` routes:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/decision/metrics/run` | POST | Run unified metric engine |
| `/decision/agents/` | GET | List all registered agents |
| `/decision/agents/{id}` | GET | Single agent registry entry |
| `/decision/center/run` | POST | Full orchestrator pipeline run |
| `/decision/scenarios/{case}` | POST | Run base/downside/stress scenario |
| `/decision/scenarios/compare` | POST | Compare all 3 scenarios |
| `/decision/reports/{type}` | POST | Generate executive/investor/lender/weekly report |
| `/decision/quality/run` | POST | Run data quality engine |

## Multi-Agent System

### Decision Intelligence Agents (Rule-Based — Phase 5)

15 agents organized in 6 layers, executing in topological order with priority-based conflict resolution:

| Agent | Layer | Priority | Role |
|-------|-------|----------|------|
| `data_quality` | 0 | 1 | Completeness, duplicates, freshness gate |
| `risk` | 1 | 4 | PAR, NPL, default rate, expected loss |
| `cohort_vintage` | 1 | 4 | Vintage analysis, trend detection |
| `concentration` | 1 | 4 | HHI, top-N obligor analysis |
| `pricing` | 2 | 5 | Yield/NIM vs target APR band |
| `segmentation` | 2 | 7 | Segment profiles, concentration |
| `sales` | 2 | 6 | Disbursement MTD vs targets |
| `collections` | 3 | 6 | Collection rate vs 98.5%, cure rate |
| `marketing` | 3 | 6 | Channel analysis, repeat vs new |
| `liquidity` | 3 | 3 | Ratio/utilization, stress scenario |
| `covenant` | 3 | 2 | 7-covenant check, blocks growth |
| `revenue_strategy` | 4 | 5 | NIM analysis, revenue leakage |
| `retention` | 4 | 6 | Repeat rate, at-risk customers |
| `narrative` | 4 | 7 | Board-ready executive narrative |
| `cfo` | 5 | 15 | Capital adequacy, covenant & ROE oversight |

### LLM-Based Agents (Scenarios)

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
| `.github/workflows/tests.yml` | Main test suite (unit, integration, e2e gates) |
| `.github/workflows/pr-checks.yml` | PR quality gates |
| `.github/workflows/etl-pipeline.yml` | ETL tests + ingest/snapshot pipeline |
| `.github/workflows/security-scan.yml` | Snyk + dependency audit |

## Forensic Formula Audit Artifacts

Repository-level formula/KPI forensic outputs are generated under `audit_artifacts/`:

- `forensic_audit_report.md`
- `reviewed_file_manifest.csv`
- `formula_inventory.csv`
- `critical_findings.csv`
- `duplicate_shadow_map.csv`

Regenerate with:

```bash
python scripts/full_repo_formula_audit.py
```

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

Proprietary — All rights reserved.
