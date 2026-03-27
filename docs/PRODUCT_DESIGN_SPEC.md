# Loans Analytics — Diseño Completo de Producto End-to-End

> **Versión:** 1.0 · **Fecha:** 2026-03-27  
> **Plataforma:** Desktop (1440px+) + Tablet (768px) + Mobile (375px)  
> **Stack UI actual:** Streamlit · Plotly · **Stack objetivo:** React/Next.js + Tailwind

---

## 1. SISTEMA DE DISEÑO (Design Tokens)

### 1.1 Paleta de Colores

| Token | Hex | Uso |
|-------|-----|-----|
| `primary-purple` | `#C1A6FF` | Títulos, acentos, CTAs primarios |
| `purple-dark` | `#5F4896` | Bordes de tarjetas, hover states |
| `dark-blue` | `#0C2742` | Headers secundarios, card backgrounds alt |
| `background` | `#030E19` | Fondo principal de toda la app |
| `white` | `#FFFFFF` | Texto principal en dark mode |
| `light-gray` | `#CED4D9` | Texto de cuerpo, labels |
| `medium-gray` | `#9EA9B3` | Texto secundario, placeholders |
| `dark-gray` | `#6D7D8E` | Texto deshabilitado, captions |
| `success` | `#10B981` | KPIs on-target, badges positivos |
| `success-dark` | `#059669` | Hover de success |
| `warning` | `#FB923C` | Alertas warning, KPIs en rango |
| `warning-dark` | `#EA580C` | Hover de warning |
| `error` | `#DC2626` | Alertas critical, KPIs fuera de rango |
| `error-dark` | `#991B1B` | Hover de error |
| `info` | `#3B82F6` | Links, acciones informativas |
| `info-dark` | `#1D4ED8` | Hover de info |

### 1.2 Gradientes

| Token | Valor | Uso |
|-------|-------|-----|
| `gradient-title` | `linear-gradient(81.74deg, #C1A6FF 5.91%, #5F4896 79.73%)` | Títulos hero, headers de página |
| `gradient-card-primary` | `linear-gradient(135deg, rgba(193,166,255,0.2) 0%, rgba(0,0,0,0.5) 100%)` | Tarjetas de métricas principales |
| `gradient-card-secondary` | `linear-gradient(135deg, rgba(34,18,72,0.4) 0%, rgba(0,0,0,0.6) 100%)` | Tarjetas secundarias |
| `gradient-card-highlight` | `linear-gradient(135deg, rgba(193,166,255,0.25) 0%, rgba(0,0,0,0.8) 100%)` | Tarjetas destacadas/hover |

### 1.3 Tipografía

| Token | Valor | Uso |
|-------|-------|-----|
| `font-primary` | **Lato** (100–900) | Cuerpo de texto, datos, tablas |
| `font-secondary` | **Poppins** (100–700) | Títulos, headings, badges |
| `title-size` | 48px | H1 de página |
| `metric-size` | 48px | Números grandes en KPI cards |
| `label-size` | 16px | Labels de campos, tabs |
| `body-size` | 14px | Texto de cuerpo |
| `description-size` | 12px | Captions, timestamps |

### 1.4 Colorway para Charts (Plotly)

```
["#C1A6FF", "#5F4896", "#10B981", "#FB923C"]
```

- `plot_bgcolor` / `paper_bgcolor`: `#030E19`
- `font_color`: `#CED4D9`
- `title_font_color`: `#C1A6FF`
- Hover row en tablas: `#9EA9B3`

### 1.5 Componentes Base

| Componente | Estilo |
|-----------|--------|
| **Metric Card** | `gradient-card-primary`, borde `1px solid #5F4896`, border-radius `10px`, padding `20px` |
| **Alert Card Critical** | Borde izquierdo `4px solid #DC2626`, fondo `rgba(220,38,38,0.08)` |
| **Alert Card Warning** | Borde izquierdo `4px solid #FB923C`, fondo `rgba(251,146,60,0.08)` |
| **Alert Card Info** | Borde izquierdo `4px solid #3B82F6`, fondo `rgba(59,130,246,0.08)` |
| **Confidence Badge High** | 🟢 verde con label "High Confidence" |
| **Confidence Badge Medium** | 🟡 amarillo con label "Medium Confidence" |
| **Confidence Badge Low** | 🔴 rojo con label "Low Confidence" |
| **KPI Status Badge** | ✅ Normal · ⚠️ Warning · 🔴 Critical · ⊙ Not Configured |

### 1.6 Spacing Scale (8px base)

| Token | Valor |
|-------|-------|
| `space-xs` | 4px |
| `space-sm` | 8px |
| `space-md` | 16px |
| `space-lg` | 24px |
| `space-xl` | 32px |
| `space-2xl` | 48px |
| `space-3xl` | 64px |

---

## 2. ARQUITECTURA DE NAVEGACIÓN

### 2.1 Estructura actual (Streamlit — 10 páginas)

```
🏠 Home (app.py)
├── 01 Executive Command Center
├── 02 Risk Intelligence
├── 03 Collections Operations
├── 04 Treasury & Liquidity
├── 05 Sales & Growth
├── 06 Agent Insights
├── 07 Scenario Engine
├── 08 Reports Center
├── 09 Data Quality
└── 10 AI Decision Center
```

### 2.2 Estructura objetivo completa (Desktop + Mobile)

```
📱 MOBILE NAV (Bottom Tab Bar)
├── 🏠 Home (dashboard resumen)
├── 📊 Portfolio (KPIs core)
├── ⚠️ Alerts (centro de alertas)
├── 🤖 AI (agentes + decisiones)
└── 👤 Profile (settings, admin)

🖥️ DESKTOP NAV (Sidebar colapsable)
├── 📌 OPERATIVO
│   ├── Executive Command Center
│   ├── Portfolio Overview
│   ├── Collections Operations
│   └── Data Quality Gate
│
├── 📈 ANALÍTICA
│   ├── Risk Intelligence
│   ├── Scenario Engine
│   ├── Vintage & Cohort Analysis
│   ├── Concentration & HHI
│   └── Reports Center
│
├── 💰 FINANCIERO
│   ├── Treasury & Liquidity
│   ├── Unit Economics
│   ├── Covenant Compliance
│   └── Capital & ROA/ROE
│
├── 🚀 CRECIMIENTO
│   ├── Sales & Growth
│   ├── Marketing & Retention
│   ├── Pricing Analytics
│   └── Segmentation
│
├── 🤖 INTELIGENCIA
│   ├── AI Decision Center
│   ├── Agent Insights & History
│   ├── Multi-Agent Orchestrator
│   └── Narrative Reports
│
├── ⚙️ ADMIN
│   ├── Data Ingestion
│   ├── Pipeline Monitor
│   ├── API & Integrations
│   ├── User Management
│   └── Settings
│
└── 🔗 EXTERNAL
    ├── Grafana Dashboard
    ├── Supabase Console
    └── API Docs (Swagger)
```

---

## 3. PANTALLAS DISEÑADAS Y VALIDADAS (Estado actual)

### 3.1 🏠 Home — Loans Financial Intelligence

**Estado: ✅ IMPLEMENTADO Y FUNCIONANDO**

| Elemento | Descripción | Tipo dato |
|----------|-------------|-----------|
| **KPI Snapshot Strip** | Grid 4 columnas: cada KPI con valor + threshold badge (✅⚠️🔴⊙) | `enriched_kpis` dict |
| **Snapshot Month** | Mes del último snapshot (auto-detect de `month`/`month_end`/`date`) | `pd.Timestamp` |
| **Links Panel** | Streamlit local/prod, Grafana, docs | URLs configurables |
| **Strategic Report Button** | Genera JSON + MD en `reports/strategic/` | `build_strategic_summary()` |
| **Cashflow Trends** | Línea temporal: recv_revenue, recv_interest, recv_fee, sched_revenue | `analytics_facts.csv` |
| **Growth Analysis** | Gap vs target, proyección lineal 12 meses | Target configurable sidebar |
| **Category Breakdown** | Pie chart por `categoria` (outstanding_loan_value) | `loan_data` DataFrame |
| **Sales Performance** | Treemap por `sales_agent` o fallback headcount | `data/support/headcount.csv` |
| **Risk Analysis** | PD model (XGBoost), DPD buckets, data quality score | `models/risk/default_risk_xgb.ubj` |
| **Advanced Intelligence** | 5 tabs: Revenue Forecast, Opportunities, Churn, LTV/CAC, Pricing | `extended_kpis` dict |
| **KPI Catalog** | Todos los KPIs con metadata y drill-down | `KPICatalogProcessor` |

**Sidebar Controls:**
- Data Source: Local artifacts / Manual upload
- File uploader (CSV/XLSX multi-file)
- Target Outstanding ($) / Target Loans (#)
- Clear Data button

---

### 3.2 📋 Executive Command Center (Página 01)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Fuente de datos | Visualización |
|----------|-----------------|---------------|
| **Business State Indicator** | `decision_state.business_state` | Emoji: 💚 healthy, 🟡 attention, 🔴 critical, ⬛ data_blocked |
| **Confidence Badge** | `decision_state.confidence` | 🟢🟡🔴 inline badge |
| **Key Metrics Strip** | `decision_state.metrics` | Grid 6 columnas con `format_kpi_value()` |
| **Alert List** | `decision_state.alerts` | Cards por severidad (critical/warning/info) |
| **Prioritized Actions** | `decision_state.actions` | Markdown table: Priority / Agent / Action / Routed |
| **Recommendations** | `decision_state.recommendations` | Lista ordenada |

**Datos cargados de:** `logs/runs/<timestamp>/decision_center_state.json`

---

### 3.3 🔍 Risk Intelligence (Página 02)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Agent Response Browser** | Carga JSONs de `data/agent_outputs/<timestamp>_<agent>_response.json` |
| **Filters** | Multi-select agentes, date range picker |
| **Metrics Row** | Total interactions, tokens used, cost ($), success rate (%) |
| **Tab: Conversations** | Expandibles por agente con JSON raw toggle |
| **Tab: Summary Table** | Tabla exportable CSV con todas las respuestas |
| **Tab: Analytics** | Timeline de interacciones, cost breakdown por agente |

---

### 3.4 📞 Collections Operations (Página 03)

**Estado: ✅ IMPLEMENTADO — Página más compleja**

| Elemento | Descripción |
|----------|-------------|
| **Data Preparation Pipeline** | 25+ alias, canonicalización de status, DPD calc, exposure derivation |
| **Portfolio Metrics Strip** | Portfolio value, weighted rate, delinquency, PAR 30/60/90, defaults, collections, borrowers |
| **KPI Methodology Deep Dive** | Expandible con fórmulas, numeradores, denominadores, valores |
| **Delinquency Trend Chart** | Plotly line chart con evolución temporal |
| **Multi-Agent Orchestration** | Ejecuta `MultiAgentOrchestrator` con callbacks, persiste en `data/agent_outputs/` |
| **Borrower Metrics** | Active borrowers, repeat rate computada |
| **DPD & PAR Metrics** | Delinquency buckets (Current, 1-30, 31-60, 61-90, 90+), PAR rates |

---

### 3.5 💰 Treasury & Liquidity (Página 04)

**Estado: ✅ IMPLEMENTADO (parcial)**

| Elemento | Descripción |
|----------|-------------|
| **Usage Metrics** | Total events, unique features, unique actions |
| **Event Log Table** | Tabla ordenada por timestamp descendente |
| **Feature Usage Breakdown** | Bar chart por feature |
| **Export Options** | JSON, CSV, Parquet download |

---

### 3.6 📈 Sales & Growth (Página 05)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Live Event Feed** | Filtros: severity, source, limit; fetch desde `/monitoring/events` |
| **Event Acknowledge** | Acknowledge individual por UUID |
| **Command Panel** | Types: rerun_pipeline, notify_team, scale_up, acknowledge_alert |
| **Command Requester** | operator, n8n, auto_rule + JSON params |
| **Command Status** | Filter by: all, pending, running, completed, failed |

---

### 3.7 🎯 Agent Insights (Página 06)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Historical Context Provider** | MOCK o REAL mode via `HistoricalContextProvider` |
| **Trend Analysis** | Tendencias históricas por agente |
| **Context Display** | Expandibles con contexto por agente |

---

### 3.8 🔮 Scenario Engine (Página 07)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Scenario Strip** | Side-by-side cards Base/Downside/Stress |
| **Per-scenario Details** | Título, triggers (⚡), narrative, top 5 projected metrics |
| **Model Retraining** | Trigger de retrain desde UI |
| **Assumptions Display** | De `config/scenarios/scenario_assumptions.yaml` |

---

### 3.9 📊 Reports Center (Página 08)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Risk Analytics** | Expected Loss, Roll Rates, Vintage analysis, HHI concentration |
| **Report Generation** | Executive, regulatory, operational reports |
| **Export Formats** | PDF, JSON, CSV |

---

### 3.10 🛡️ Data Quality (Página 09)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Capital & Economics** | Capital indicators display |
| **Quality Scores** | Completeness, freshness, duplicates |
| **Blocking Policy** | Visual indicator si DQ < 85% bloquea downstream |

---

### 3.11 🤖 AI Decision Center (Página 10)

**Estado: ✅ IMPLEMENTADO**

| Elemento | Descripción |
|----------|-------------|
| **Decision Metrics** | Métricas del decision engine |
| **Action Items** | Lista priorizada de acciones |
| **Agent Status** | Estado de cada agente (16 agentes en 5 layers) |

---

## 4. PANTALLAS PENDIENTES POR DISEÑAR E IMPLEMENTAR

### 4.1 🆕 Onboarding & Authentication

**Estado: ❌ NO EXISTE — PRIORIDAD ALTA**

#### 4.1.1 Login Screen
```
┌─────────────────────────────────────────────┐
│                                             │
│        [Logo - gradient title]        │
│        Loans Financial Intelligence         │
│                                             │
│   ┌─────────────────────────────────────┐   │
│   │  📧 Email                           │   │
│   └─────────────────────────────────────┘   │
│   ┌─────────────────────────────────────┐   │
│   │  🔒 Password                        │   │
│   └─────────────────────────────────────┘   │
│                                             │
│   [══════ Sign In (gradient-title) ══════]  │
│                                             │
│   ─────── or sign in with ───────           │
│   [Google]  [Microsoft]  [SSO]              │
│                                             │
│   Forgot password? · Request access         │
│                                             │
│   bg: #030E19 · accent: #C1A6FF             │
└─────────────────────────────────────────────┘
```

**API Backend:** `/auth/confirm` (OTP), `/auth/signout` ya existen en OpenAPI  
**Auth Provider:** Supabase Auth (JWT, bearer token)

#### 4.1.2 Role-Based Access
| Rol | Acceso |
|-----|--------|
| `viewer` | Solo lectura dashboard + reports |
| `analyst` | + Data upload, scenario engine, agents |
| `manager` | + Collections ops, commands, decisions |
| `admin` | + Pipeline control, user management, API keys |
| `executive` | + Strategic reports, narrative, CFO dashboard |

---

### 4.2 🆕 Portfolio Overview (Pantalla nueva)

**Estado: ❌ NO EXISTE — PRIORIDAD ALTA**

```
┌────────────────────────────────────────────────────────────────┐
│ Portfolio Overview                              [Export ▾] 🔔  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ AUM      │ │ Active   │ │ Avg APR  │ │ Default  │         │
│  │ $9.4M    │ │ Loans    │ │ 36.2%    │ │ Rate     │         │
│  │ +5.2% ▲  │ │ 1,247    │ │ target   │ │ 4.1% ⚠️ │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                │
│  ┌─────────────────────────────────┐ ┌────────────────────────┐│
│  │ Outstanding by Month            │ │ Status Distribution    ││
│  │ [Area chart - 12m trend]        │ │ [Donut: Active/Delq/   ││
│  │ Target line: $8.5M→$12M        │ │  Default/Closed]       ││
│  │ Colors: #C1A6FF actual,         │ │                        ││
│  │         #5F4896 target          │ │                        ││
│  └─────────────────────────────────┘ └────────────────────────┘│
│                                                                │
│  ┌─────────────────────────────────┐ ┌────────────────────────┐│
│  │ DPD Aging Heatmap               │ │ Concentration          ││
│  │ [Heatmap: month x bucket]       │ │ [Bar: Top 10 obligors] ││
│  │ Buckets: Current,1-30,31-60,    │ │ HHI: 0.0847            ││
│  │ 61-90,90-179,180+               │ │ Max single: 3.2%       ││
│  └─────────────────────────────────┘ └────────────────────────┘│
│                                                                │
│  ┌──────────────────────────────────────────────────────────── ┐│
│  │ Loan-Level Table (searchable, sortable, paginated)          ││
│  │ Cols: Loan ID | Borrower | Amount | Status | DPD | APR |   ││
│  │       PAR Flag | Company | Credit Line | KAM               ││
│  └─────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

**Datos:** `loan_data` + `customer_data` merged  
**Targets 2026:** $8.5M (Ene) → $12M (Dic) de `config/business_parameters.yml`  
**Variance Status:** ON_TRACK (≥95%) · MONITOR (90-95%) · AT_RISK (<90%) · EXCEEDED

---

### 4.3 🆕 Vintage & Cohort Analysis (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA INDEPENDIENTE**

```
┌────────────────────────────────────────────────────────────┐
│ Vintage & Cohort Analysis                                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [Cohort selector: Alfa│Beta│Gamma│Delta] [Period: M/Q/Y] │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Vintage Default Rate Curves                          │  │
│  │ [Line chart: MOB vs default rate by vintage month]   │  │
│  │ X: Months on Book (0-36)                             │  │
│  │ Y: Cumulative Default Rate %                         │  │
│  │ Lines: Jan-26, Feb-26, Mar-26... color per vintage   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────┐ ┌──────────────────────────┐  │
│  │ Roll Rate Matrix        │ │ Cure Rate Trend          │  │
│  │ [Heatmap: from→to]      │ │ [Line: cure rate by MOB] │  │
│  │ Current→30, 30→60,      │ │ Target: maintain > 60%   │  │
│  │ 60→90, 90→default       │ │                          │  │
│  └─────────────────────────┘ └──────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Cohort Performance Table                             │  │
│  │ Cohort │ Count │ Balance │ PAR30 │ Default │ Avg DPD │  │
│  │ Alfa   │ 324   │ $2.1M   │ 3.2%  │ 1.1%    │ 8      │  │
│  │ Beta   │ 289   │ $1.8M   │ 5.7%  │ 2.3%    │ 15     │  │
│  │ Gamma  │ 198   │ $1.2M   │ 8.1%  │ 3.8%    │ 22     │  │
│  │ Delta  │ 112   │ $0.7M   │ 12%   │ 6.2%    │ 38     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/python/kpis/advanced_risk.py` — vintage_default_rate, vintage_par30_rate, vintage_avg_dpd
- `backend/python/multi_agent/agents/cohort_vintage_agent.py`
- `backend/src/pipeline/calculation.py` — cohort analysis (Alfa/Beta/Gamma/Delta)
- Roll rate migrations entre DPD buckets

---

### 4.4 🆕 Unit Economics Dashboard (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA**

```
┌────────────────────────────────────────────────────────────┐
│ Unit Economics                                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ LTV      │ │ CAC      │ │ LTV/CAC  │ │ Payback  │     │
│  │ $4,250   │ │ $890     │ │ 4.8x ✅  │ │ 5.2 mo   │     │
│  │ target   │ │          │ │ min 3.0x │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ NIM      │ │ CoR      │ │ ROA      │ │ ROE      │     │
│  │ 22.4%    │ │ 3.1%     │ │ 8.7%     │ │ 15.2%    │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Unit Economics Reconciliation                        │  │
│  │ Default Rate: 5.96% (UNIT-EC) vs 0.44% (ER-CONS)   │  │
│  │ [Sankey: Revenue → Interest / Fees / CoR / OpEx →   │  │
│  │          Net Margin]                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────┐ ┌──────────────────────────┐  │
│  │ Gross Margin Trend      │ │ Ticket Segmentation      │  │
│  │ [Line chart: GPM %]     │ │ [Stacked bar: Bands A-H] │  │
│  │ Target range shown      │ │ A: >$50K, B: $25-50K...  │  │
│  └─────────────────────────┘ └──────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/src/kpi_engine/unit_economics.py`
- `backend/python/kpis/unit_economics.py`
- `config/holding_projections.yml` — GPM, ROA, ROE, ROS targets
- Ticket tiers A-H en `config/kpis/kpi_definitions.yaml`

---

### 4.5 🆕 Covenant Compliance Monitor (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA**

```
┌────────────────────────────────────────────────────────────┐
│ Covenant Compliance Monitor                    🟢 COMPLIANT│
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Repline Distribution                                 │  │
│  │ ┌─────────┬──────────┬──────────┬──────────┐         │  │
│  │ │ Bucket  │ Actual   │ Max      │ Status   │         │  │
│  │ ├─────────┼──────────┼──────────┼──────────┤         │  │
│  │ │ 0-30d   │ 42.1%    │ 45%      │ ✅       │         │  │
│  │ │ 31-60d  │ 28.7%    │ 35%      │ ✅       │         │  │
│  │ │ 61-90d  │ 15.3%    │ 20%      │ ✅       │         │  │
│  │ │ 90+d    │ 13.9%    │ —        │ ⚠️       │         │  │
│  │ └─────────┴──────────┴──────────┴──────────┘         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────┐ ┌──────────────────────────┐  │
│  │ Key Covenants           │ │ Collection Rate          │  │
│  │ Advance Rate: 80%       │ │ [Gauge: 98.7% vs 98.5%  │  │
│  │ DSCR: 1.35 (min 1.2)   │ │  minimum] ✅             │  │
│  │ Max Default: 4% (3.8%)  │ │                          │  │
│  │ Collection: ≥98.5%      │ │ Trend: last 6 months    │  │
│  │ Top10 Conc: ≤30%        │ │                          │  │
│  └─────────────────────────┘ └──────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Lender Pack Preview (Monthly report for fund)        │  │
│  │ [Generate PDF] [Send to Lender] [Schedule Monthly]   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/python/multi_agent/agents/covenant_agent.py`
- `backend/src/kpi_engine/covenants.py`
- `config/business_parameters.yml` — all covenant thresholds
- `config/holding_projections.yml` — debt covenants, repline distribution

---

### 4.6 🆕 Holding & Multi-Entity View (Pantalla nueva)

**Estado: ❌ NO EXISTE**

```
┌────────────────────────────────────────────────────────────┐
│ Holding Financial Overview                                 │
├──────────────┬─────────────────────────────────────────────┤
│              │                                             │
│  ENTITIES    │  [Entity selector: AT | AF | GAS | GT |    │
│  ─────────   │   NI | CR | DO | EC | PE]                  │
│  AT Tech     │                                             │
│  AF Finance  │  ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  GAS Hold    │  │ Revenue │ │ OpEx    │ │ EBITDA  │      │
│  Guatemala   │  │ $2.4M   │ │ $1.8M   │ │ $620K   │      │
│  Nicaragua   │  └─────────┘ └─────────┘ └─────────┘      │
│  Costa Rica  │                                             │
│  Dom. Rep.   │  Growth Scenario: [Base▾] 5.5%/mo AT      │
│  Ecuador     │                                             │
│  Peru        │  ┌──────────────────────────────────────┐  │
│              │  │ Entity Portfolio Composition          │  │
│  TOTAL       │  │ [Stacked area: entity contribution]  │  │
│  Equity:     │  │ 24 investment rounds                 │  │
│  $4.79M      │  │ Total equity: $4.79M                 │  │
│              │  └──────────────────────────────────────┘  │
└──────────────┴─────────────────────────────────────────────┘
```

**Backend existente:**
- `config/holding_projections.yml` — 9 entities, 3 scenarios, financial indicators
- `backend/python/kpis/holding_financial_indicators.py`

---

### 4.7 🆕 Concentration & Segmentation (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA INDEPENDIENTE**

```
┌────────────────────────────────────────────────────────────┐
│ Concentration & Segmentation Analysis                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ HHI      │ │ Top 1    │ │ Top 10   │ │ Segments │     │
│  │ 0.0847   │ │ 3.2%     │ │ 24.1%    │ │ 8 active │     │
│  │ max 0.15 │ │ max 4%   │ │ max 30%  │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌──────────────────────────┐ ┌─────────────────────────┐  │
│  │ Concentration by Company │ │ PAR30 by Segment        │  │
│  │ [Treemap: company size]  │ │ [Heatmap: segment x     │  │
│  │                          │ │  risk metric]            │  │
│  └──────────────────────────┘ └─────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────┐ ┌─────────────────────────┐  │
│  │ By Credit Line           │ │ By KAM Hunter/Farmer    │  │
│  │ [Bar chart]              │ │ [Bar chart]              │  │
│  └──────────────────────────┘ └─────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Industry Default Rate                                │  │
│  │ [Horizontal bar: industry code x default rate]       │  │
│  │ Highlight: government_sector_exposure                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/src/kpi_engine/concentration.py`
- `backend/python/multi_agent/agents/concentration_agent.py`
- `backend/python/multi_agent/agents/segmentation_agent.py`
- KPIs: top_1/10 obligor, HHI, PAR30 by company/credit_line/KAM, default by industry

---

### 4.8 🆕 Pricing & Revenue Analytics (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA INDEPENDIENTE**

```
┌────────────────────────────────────────────────────────────┐
│ Pricing & Revenue Analytics                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Wtd APR  │ │ Fee Rate │ │ Eff Rate │ │ NIM      │     │
│  │ 36.8%    │ │ 2.1%     │ │ 38.9%    │ │ 22.4%    │     │
│  │ 34-40%   │ │          │ │          │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Revenue Waterfall                                    │  │
│  │ [Waterfall: Interest + Fees - CoR - OpEx = Net]     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────┐ ┌─────────────────────────┐  │
│  │ APR Distribution         │ │ Revenue Forecast (6M)   │  │
│  │ [Histogram: loan count   │ │ [Line: forecast with    │  │
│  │  by APR bucket]          │ │  confidence bounds]     │  │
│  └──────────────────────────┘ └─────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Pricing Governance Score: 94/100                     │  │
│  │ Data freshness: 2h · Quality: 98%                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/python/multi_agent/agents/pricing_agent.py`
- `backend/src/kpi_engine/revenue.py`
- KPIs: portfolio_yield, NIM, fee_rate, effective_rate
- Analytics tabs already compute: weighted APR, fee rate, effective rate, 6M forecast

---

### 4.9 🆕 Marketing & Retention (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA**

```
┌────────────────────────────────────────────────────────────┐
│ Marketing & Retention                                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ New Loans│ │ Repeat   │ │ Churn 90d│ │ CAC      │     │
│  │ MTD: 47  │ │ Rate     │ │ 8.2%     │ │ $890     │     │
│  │          │ │ 34.2%    │ │          │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌──────────────────────────┐ ┌─────────────────────────┐  │
│  │ Recurrent TPV (12M)      │ │ Channel Performance     │  │
│  │ [Area chart: recurrent   │ │ [Bar: spend vs          │  │
│  │  vs new TPV]             │ │  acquisition by channel]│  │
│  │ NSM metric: recurrent_%  │ │ From marketing_spend.csv│  │
│  └──────────────────────────┘ └─────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Churn Risk Segments                                  │  │
│  │ [Scatter: segment x churn probability]               │  │
│  │ Retention actions from retention_agent               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/python/multi_agent/agents/marketing_agent.py`
- `backend/python/multi_agent/agents/retention_agent.py`
- `data/support/marketing_spend.csv`
- KPIs: new_loans_count_mtd, repeat_borrower_rate, churn_90d, recurrent_tpv_12m

---

### 4.10 🆕 Pipeline Monitor & Data Ingestion Admin (Pantalla nueva)

**Estado: ❌ NO EXISTE COMO PANTALLA INDEPENDIENTE**

```
┌────────────────────────────────────────────────────────────┐
│ Pipeline Monitor                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Latest Run: 2026-03-27T08:15:00   Status: ✅ COMPLETED   │
│  Duration: 4m 23s   Records: 1,247   Phases: 5/5          │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Phase Timeline                                       │  │
│  │ ████ Ingestion (45s) → ████ Transform (1m20s) →     │  │
│  │ ████ Calculation (1m45s) → ████ Output (33s) →      │  │
│  │ ████ Decision (1m)                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────┐ ┌─────────────────────────┐  │
│  │ Run History (last 30)    │ │ Data Sources            │  │
│  │ [Table: timestamp,       │ │ ● Google Sheets: 🟢    │  │
│  │  status, records, dur]   │ │ ● Supabase: 🟢         │  │
│  │                          │ │ ● CSV Upload: 🟢       │  │
│  │                          │ │ ● Meta Ads: 🟡         │  │
│  └──────────────────────────┘ └─────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Data Quality Gate                                    │  │
│  │ Completeness: 97.2% │ Duplicates: 0.3% │ Fresh: 2h │  │
│  │ Quality Score: 94/100 — ✅ Gate PASSED               │  │
│  │ Blocking threshold: < 85% blocks ALL downstream      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [🔄 Rerun Pipeline] [📥 Upload New Data] [📋 View Logs]  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/src/pipeline/orchestrator.py` — 5-phase orchestrator
- `logs/runs/<timestamp>/manifest.json` — run metadata
- `backend/src/data_quality/engine.py` — DQ scoring
- Pipeline alerts en `config/rules/pipeline_alerts.yml`
- API: `/monitoring/events`, `/monitoring/commands`

---

### 4.11 🆕 Notifications & Alert Center (Mobile-first)

**Estado: ❌ NO EXISTE**

```
┌──────────────────────────┐
│ 🔔 Alerts           [≡]  │
├──────────────────────────┤
│                          │
│ TODAY                    │
│ ┌────────────────────── ┐│
│ │ 🔴 PAR90 > 4%         ││
│ │ Portfolio at Risk 90   ││
│ │ exceeded threshold     ││
│ │ 2h ago · Risk Agent    ││
│ │ [View] [Acknowledge]   ││
│ └────────────────────── ┘│
│ ┌────────────────────── ┐│
│ │ ⚠️ Collection Rate     ││
│ │ 98.3% < 98.5% min     ││
│ │ 5h ago · Covenant      ││
│ │ [View] [Acknowledge]   ││
│ └────────────────────── ┘│
│ ┌────────────────────── ┐│
│ │ 🔵 Pipeline completed  ││
│ │ 1,247 records, 4m23s   ││
│ │ 8h ago · System        ││
│ └────────────────────── ┘│
│                          │
│ YESTERDAY                │
│ ┌────────────────────── ┐│
│ │ ✅ All covenants met   ││
│ │ Monthly check passed   ││
│ └────────────────────── ┘│
│                          │
│ [Load More]              │
└──────────────────────────┘
```

**Backend existente:**
- `config/rules/kpi_threshold_alerts.yml` — alert definitions
- `config/rules/pipeline_alerts.yml`
- `config/rules/supabase_alerts.yml`
- API: `/monitoring/events`
- Alertmanager: `config/alertmanager.yml.template`

---

### 4.12 🆕 Mobile Dashboard (Responsive)

**Estado: ❌ NO EXISTE — Actualmente solo desktop Streamlit**

```
┌──────────────────────────┐
│ Loans Analytics      🔔 3│
├──────────────────────────┤
│                          │
│  AUM          $9.4M ▲5%  │
│  ┌────────────────────┐  │
│  │ ████████████████ ▲  │  │
│  │ [Sparkline 30d]     │  │
│  └────────────────────┘  │
│                          │
│  ┌──────┐ ┌──────┐      │
│  │ PAR30│ │ Dflt │      │
│  │ 3.2% │ │ 4.1% │      │
│  │  ✅  │ │  ⚠️  │      │
│  └──────┘ └──────┘      │
│  ┌──────┐ ┌──────┐      │
│  │ Coll │ │ NIM  │      │
│  │98.7% │ │22.4% │      │
│  │  ✅  │ │  ✅  │      │
│  └──────┘ └──────┘      │
│                          │
│  ── Quick Actions ──     │
│  [📊 Full Report]        │
│  [🤖 Ask AI Agent]       │
│  [📞 Collections]        │
│  [📥 Upload Data]        │
│                          │
├──────────────────────────┤
│ 🏠  📊  ⚠️  🤖  👤    │
└──────────────────────────┘
```

---

### 4.13 🆕 API Integration Hub (Pantalla nueva)

**Estado: ❌ NO EXISTE**

```
┌────────────────────────────────────────────────────────────┐
│ API & Integrations                                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ ACTIVE INTEGRATIONS ──────────────────────────────┐   │
│  │                                                     │   │
│  │ 🟢 OpenAI (4 keys)      │ Agents, Scenarios       │   │
│  │ 🟢 Anthropic Claude     │ Narrative summaries      │   │
│  │ 🟢 Google Gemini        │ Backup LLM              │   │
│  │ 🟢 HuggingFace          │ Model hosting           │   │
│  │ 🟢 Tavily Search        │ Market research         │   │
│  │ 🟢 Supabase             │ PostgreSQL + Auth       │   │
│  │ 🟢 Grafana Cloud        │ KPI monitoring          │   │
│  │ 🟢 Vercel               │ Frontend deploy         │   │
│  │ 🟢 Meta Ads             │ Marketing data          │   │
│  │ 🟡 Google Sheets        │ Data ingestion          │   │
│  │                                                     │   │
│  │ ── INACTIVE / EXPIRED ─────────────────────────    │   │
│  │ 🔴 Perplexity           │ Expired                 │   │
│  │ 🔴 Notion               │ Invalid key             │   │
│  │ 🔴 Figma (old tokens)   │ Need rotation           │   │
│  │ 🔴 HubSpot              │ All 5 variants invalid  │   │
│  │ 🔴 Codecov              │ Token expired           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  [🔑 Rotate Keys] [📋 API Docs] [🧪 Test Connection]     │
└────────────────────────────────────────────────────────────┘
```

---

### 4.14 🆕 Multi-Agent Orchestrator Visualization

**Estado: ❌ NO EXISTE COMO VISUALIZACIÓN**

```
┌────────────────────────────────────────────────────────────┐
│ Multi-Agent Decision Pipeline                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Layer 0: DATA QUALITY GATE                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [data_quality] → Score: 94% ✅ GATE PASSED          │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                │
│  Layer 1: CORE ANALYTICS                                   │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐       │
│  │ risk     │  │cohort_vintage│  │concentration  │       │
│  │ PAR:3.2% │  │ Alfa/Beta    │  │ HHI: 0.08    │       │
│  └──────────┘  └──────────────┘  └───────────────┘       │
│        │              │                 │                  │
│  Layer 2: STRATEGY                                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐       │
│  │ pricing  │  │segmentation  │  │ sales          │       │
│  │ APR:36%  │  │ 8 segments   │  │ MTD: 47 new   │       │
│  └──────────┘  └──────────────┘  └───────────────┘       │
│        │              │                 │                  │
│  Layer 3: OPERATIONS                                       │
│  ┌────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │collect.│  │marketing│  │liquidity│  │covenant │      │
│  └────────┘  └─────────┘  └─────────┘  └─────────┘      │
│        │              │         │            │             │
│  Layer 4: EXECUTIVE                                        │
│  ┌──────────────┐  ┌──────────┐  ┌─────────┐  ┌─────┐   │
│  │revenue_strat.│  │retention │  │narrative│  │ cfo │   │
│  └──────────────┘  └──────────┘  └─────────┘  └─────┘   │
│                          │                                 │
│  Layer 5: ORCHESTRATOR                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ decision_orchestrator — Conflict Resolution          │   │
│  │ Priority: data_integrity > regulatory > liquidity    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  Cadence: per_run (6) · daily (5) · weekly (5) · monthly(3)│
└────────────────────────────────────────────────────────────┘
```

**Backend existente completo:**
- 16 agentes en `backend/python/multi_agent/agents/`
- Registry: `agents.yaml`, `cadences.yaml`, `ownership.yaml`, `surfaces.yaml`
- Orchestrator con dependency graph y priority rules

---

### 4.15 🆕 Liquidity Dashboard

**Estado: ❌ LA PÁGINA 04 ES SOLO "USAGE METRICS", NO TREASURY REAL**

```
┌────────────────────────────────────────────────────────────┐
│ Treasury & Liquidity                                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Cash     │ │ Liq.     │ │ Liq.     │ │ Advance  │     │
│  │ Reserve  │ │ Ratio    │ │ Floor    │ │ Rate     │     │
│  │ $520K    │ │ 7.8%     │ │ $200K ✅ │ │ 80%      │     │
│  │ min 5%   │ │ tgt 8%   │ │ piso abs │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Cash Flow Projection (12 weeks)                      │  │
│  │ [Stacked area: Inflows vs Outflows vs Net Position]  │  │
│  │ Collections + Disbursements + Operating Expenses     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────┐ ┌──────────────────────────┐  │
│  │ Utilization Bands       │ │ Eligible Portfolio       │  │
│  │ [Bar: utilization %]    │ │ Total: $7.5M             │  │
│  │ Target: 75-90%          │ │ Eligible: $6.0M (80%)    │  │
│  │ Current: 82% ✅         │ │ Funded: $4.8M            │  │
│  └─────────────────────────┘ └──────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**Backend existente:**
- `backend/src/kpi_engine/liquidity.py`
- `backend/python/multi_agent/agents/liquidity_agent.py`
- Guardrails: `min_liquidity_reserve_pct: 0.05`, `target: 0.08`, `floor: $200K`
- `utilization_min: 0.75`, `utilization_max: 0.90`

---

## 5. ESTRUCTURA DE EJECUCIÓN POR FASES

### Fase 1: Foundation (Semanas 1-3) — ALTA PRIORIDAD

| # | Tarea | Estado | Dependencia |
|---|-------|--------|-------------|
| 1.1 | **Authentication & RBAC** | ❌ Pendiente | Supabase Auth ya integrado |
| 1.2 | **Portfolio Overview** (nueva pantalla) | ❌ Pendiente | KPI engine + loan data |
| 1.3 | **Mobile responsive layout** | ❌ Pendiente | Design tokens definidos |
| 1.4 | **Navigation restructure** (sidebar + bottom tabs mobile) | ❌ Pendiente | Todas las páginas |
| 1.5 | Refactor Treasury p.04 → **Liquidity real** | ❌ Pendiente | `liquidity.py` existe |

**Entregable:** App funcional con login, portfolio view, mobile basic, navegación restructurada.

---

### Fase 2: Financial Intelligence (Semanas 4-6) — ALTA PRIORIDAD

| # | Tarea | Estado | Dependencia |
|---|-------|--------|-------------|
| 2.1 | **Unit Economics Dashboard** | ❌ Pendiente | `unit_economics.py` existe |
| 2.2 | **Covenant Compliance Monitor** | ❌ Pendiente | `covenants.py`, covenant_agent |
| 2.3 | **Pricing & Revenue Analytics** | ❌ Pendiente | pricing_agent, revenue.py |
| 2.4 | **Vintage & Cohort Analysis** (pantalla independiente) | ❌ Pendiente | cohort_vintage_agent |
| 2.5 | Enriquecer **Executive Command Center** con covenant status | ✅ Parcial | Fase 2.2 |

**Entregable:** Suite financiera completa: unit economics, covenants, pricing, vintage.

---

### Fase 3: Growth & Operations (Semanas 7-9)

| # | Tarea | Estado | Dependencia |
|---|-------|--------|-------------|
| 3.1 | **Concentration & Segmentation** (pantalla independiente) | ❌ Pendiente | concentration.py, segmentation_agent |
| 3.2 | **Marketing & Retention** | ❌ Pendiente | marketing_agent, retention_agent |
| 3.3 | **Holding & Multi-Entity View** | ❌ Pendiente | holding_projections.yml |
| 3.4 | **Notification Center** (mobile-first) | ❌ Pendiente | Alert rules ya definidas |
| 3.5 | Refactor Sales p.05 → **Sales + Growth real** con funnel | ❌ Pendiente | sales_agent |

**Entregable:** Vistas de crecimiento, concentración, multi-entity, alertas mobile.

---

### Fase 4: Intelligence & Automation (Semanas 10-12)

| # | Tarea | Estado | Dependencia |
|---|-------|--------|-------------|
| 4.1 | **Multi-Agent Orchestrator Visualization** | ❌ Pendiente | 16 agentes, DAG exists |
| 4.2 | **Pipeline Monitor Admin** | ❌ Pendiente | orchestrator.py, manifest.json |
| 4.3 | **API Integration Hub** | ❌ Pendiente | Keys ya validadas |
| 4.4 | **AI Chat Interface** (conversational agent) | ❌ Pendiente | Multi-agent protocol.py |
| 4.5 | **Report Builder** (dynamic, scheduled) | ❌ Pendiente | surfaces.yaml cadences |

**Entregable:** Visualización de agentes, pipeline admin, chat AI, reports automatizados.

---

### Fase 5: Production Polish (Semanas 13-15)

| # | Tarea | Estado | Dependencia |
|---|-------|--------|-------------|
| 5.1 | **Dark/Light mode toggle** | ❌ Pendiente | Tokens ya definidos |
| 5.2 | **Export center** (PDF, Excel, scheduled emails) | ❌ Pendiente | Report outputs |
| 5.3 | **Onboarding wizard** (first-time user) | ❌ Pendiente | Auth + RBAC |
| 5.4 | **Keyboard shortcuts & command palette** | ❌ Pendiente | — |
| 5.5 | **Performance optimization** (caching, lazy loading) | ❌ Pendiente | — |
| 5.6 | **Accessibility audit** (WCAG 2.1 AA) | ❌ Pendiente | — |
| 5.7 | **E2E tests** (Playwright) | ❌ Pendiente | All pages |

**Entregable:** Producto pulido, accesible, performante, con tests E2E.

---

## 6. INVENTARIO COMPLETO: BACKEND LISTO vs UI PENDIENTE

| Capacidad Backend | Archivo | UI Existente | UI Pendiente |
|-------------------|---------|:---:|:---:|
| 40+ KPIs (PAR, NPL, EL, CoR, NIM...) | `kpi_definitions.yaml` | ✅ Snapshot strip | ❌ Drill-down por KPI |
| Scorecard model (LR + WOE/IV) | `scorecard_model.py` | ❌ | ❌ Scorecard viewer |
| Default risk model (XGBoost) | `default_risk_model.py` | ✅ Risk page | — |
| Portfolio clustering (HDBSCAN) | `calculation.py` | ❌ | ❌ Cluster explorer |
| Star schema (dim/fact) | `create_star_schema.sql` | ❌ | ❌ Data explorer |
| 6 domain marts | `builder.py` | ❌ | ❌ Mart browser |
| Feature store (5 modules) | `feature_store/` | ❌ | ❌ Feature catalog |
| 16 agent registry | `agents.yaml` | ✅ Básico | ❌ DAG visual |
| Agent cadences | `cadences.yaml` | ❌ | ❌ Schedule viewer |
| Agent ownership | `ownership.yaml` | ❌ | ❌ RACI matrix |
| 7 output surfaces | `surfaces.yaml` | ❌ | ❌ Surface router |
| 20+ scenarios | `orchestrator.py` | ✅ Partial | ❌ Scenario builder |
| Holding projections (9 entities) | `holding_projections.yml` | ❌ | ❌ Entity dashboard |
| Covenants (replines, advance rate) | `business_parameters.yml` | ❌ | ❌ Covenant monitor |
| Graph analytics | `graph_analytics.py` | ❌ | ❌ Network view |
| Health score (composite) | `health_score.py` | ❌ | ❌ Health gauge |
| Strategic reporting | `strategic_reporting.py` | ✅ Button | ❌ Report viewer |
| WOE/IV engine | `woe_iv_engine.py` | ❌ | ❌ IV ranking viewer |
| Meta Ads adapter | `meta_ads_adapter.py` | ❌ | ❌ Ads dashboard |
| Google Sheets adapter | `google_sheets_adapter.py` | ✅ Pipeline | — |
| WebSocket streaming | `kpi_websocket_client.py` | ✅ Configured | ❌ Live ticker |
| Rate limiter | `rate_limiter.py` | ✅ Active | — |
| PII guardrails | `guardrails.py` | ✅ Active | — |
| Financial precision (Decimal) | `financial_precision.py` | ✅ Active | — |
| Connection pool (asyncpg) | `supabase_pool.py` | ✅ Active | — |
| 2026 targets ($8.5M→$12M) | `business_parameters.yml` | ❌ | ❌ Target tracker |
| Anomaly detection | `anomaly_detection.py` | ❌ | ❌ Anomaly explorer |
| Blocking policy (DQ gate) | `blocking_policy.py` | ❌ | ❌ Gate visualization |
| OpenTelemetry tracing | `tracing_setup.py` | ✅ Active | ❌ Trace viewer |
| Sentry error tracking | `main.py` | ✅ Active | — |
| Prometheus metrics | `prometheus.yml` | ✅ Active | — |
| Grafana dashboards | `provision_*.py` | ✅ Active | — |

---

## 7. DATA MODEL REFERENCE

### Star Schema (Supabase PostgreSQL)

```
dim_time ─────────┐
  time_id          │
  snapshot_month   │
  year/month/qtr   │
                   ├──→ fact_disbursement
dim_client ───────┤     (loan_sk, client_sk, time_id,
  client_sk        │      principal_amount, channel)
  client_id        │
  client_name      ├──→ fact_payment
                   │     (loan_sk, client_sk, time_id,
dim_loan ─────────┤      principal_paid, interest_paid, fees_paid)
  loan_sk          │
  lend_id          ├──→ fact_monthly_snapshot
  product_type     │     (loan_sk, client_sk, time_id,
  interest_rate    │      principal_outstanding, dpd,
  term_months            mora_bucket, par_1/30/60/90,
  original_principal     months_on_book)
```

### API Endpoints (OpenAPI 3.0.3)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/analytics/full-analysis` | Análisis completo de portafolio |
| GET | `/api/analytics/kpis` | Todos los KPIs con thresholds |
| GET | `/api/analytics/kpis/par30` | PAR30 individual |
| GET | `/api/analytics/kpis/par90` | PAR90 individual |
| GET | `/api/analytics/kpis/collection-rate` | Collection rate |
| GET | `/api/analytics/kpis/portfolio-health` | Health score |
| GET | `/api/analytics/kpis/ltv` | LTV ratio |
| GET | `/api/analytics/kpis/dti` | DTI ratio |
| GET | `/api/analytics/kpis/portfolio-yield` | Portfolio yield |
| POST | `/api/analytics/risk-stratification` | Risk stratification |
| POST | `/api/analytics/risk-alerts` | Risk alerts |
| POST | `/api/data-quality/profile` | Data quality profiling |
| POST | `/api/data-quality/validate` | Data validation |
| POST | `/decision/metrics` | Execute metric engine |
| GET | `/decision/agents` | List agents |
| POST | `/decision/center` | Run decision center |
| POST | `/decision/scenarios` | Run scenarios |
| POST | `/decision/reports` | Generate reports |
| POST | `/decision/quality` | Data quality analysis |
| WS | `/analytics/kpis/stream` | Real-time KPI streaming |
| GET | `/monitoring/events` | Operational events |
| POST | `/monitoring/commands` | Execute commands |
| POST | `/auth/confirm` | OTP confirmation |
| POST | `/auth/signout` | Sign out |

---

## 8. RESUMEN EJECUTIVO

### Lo que YA está (✅ 11 pantallas + backend robusto)

- **10 páginas Streamlit** funcionando con datos reales
- **40+ KPIs** calculados con precision financiera (Decimal)
- **16 agentes AI** con orchestration, dependency graph, cadences
- **5-phase pipeline** (ingestion → output → decision)
- **Star schema** en Supabase PostgreSQL
- **20+ scenarios** pre-configurados
- **Design system** completo (colores, gradientes, tipografía, componentes)
- **API REST** con 20+ endpoints + WebSocket
- **Monitoring** (Grafana, Prometheus, Sentry, OpenTelemetry)
- **Security** (RLS, PII redaction, rate limiting, JWT auth)

### Lo que FALTA (❌ 15+ pantallas/features)

1. **Authentication & RBAC** — Pantalla de login, roles, permisos
2. **Portfolio Overview** — Vista consolidada de cartera
3. **Mobile responsive** — Layout adaptativo completo
4. **Unit Economics** — Dashboard de economía unitaria
5. **Covenant Compliance** — Monitor de covenants con lenders
6. **Vintage & Cohort** — Análisis independiente con curvas
7. **Pricing & Revenue** — Analytics de pricing y revenue
8. **Concentration & Segmentation** — Vista independiente
9. **Marketing & Retention** — Dashboard de crecimiento
10. **Holding Multi-Entity** — Vista de holding (9 entidades)
11. **Liquidity real** — Treasury actual es solo usage metrics
12. **Pipeline Monitor** — Admin de pipeline y data sources
13. **Notification Center** — Alertas mobile-first
14. **Agent DAG Visualization** — Flujo visual de 16 agentes
15. **API Integration Hub** — Estado de integraciones

### Proporción: ~40% UI completada sobre backend 100% listo
