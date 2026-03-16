# Credit Risk Analysis – Abaco Loans Analytics

**Last Updated:** 2026-03-16  
**Status:** ✅ **PRODUCTION READY**

---

## 📋 Overview

The Abaco credit risk analysis system provides a multi-layered framework for measuring, predicting, and managing credit risk across the loan portfolio. It combines rule-based analytics, statistical KPIs, machine-learning default prediction, and a multi-agent orchestration layer to deliver actionable insights.

### Architecture

```
Raw Loan Data (CSV / Supabase)
        │
        ▼
Advanced Risk Metrics Engine          python/kpis/advanced_risk.py
  ├─ DPD extraction & normalisation
  ├─ Balance & delinquency bucketing
  ├─ Fee / yield computation
  ├─ Default rate & recovery rate
  └─ Concentration & credit quality
        │
        ▼
KPI Service Layer                     python/apps/analytics/api/service.py
  ├─ Aggregates advanced risk metrics
  ├─ Computes NPL, LGD, Cost of Risk, NIM
  ├─ Calculates unit economics
  └─ Risk stratification & decision flags
        │
        ▼
FastAPI Analytics Layer               python/apps/analytics/api/main.py
  ├─ POST /analytics/advanced-risk
  ├─ POST /analytics/risk-alerts
  ├─ POST /analytics/risk-stratification
  ├─ POST /analytics/unit-economics
  ├─ POST /analytics/full-analysis
  └─ POST /predict/default
        │
        ▼
Streamlit Dashboard                   streamlit_app/pages/3_Portfolio_Dashboard.py
  └─ DPD charts, risk flags, heatmap, KPI tiles
```

---

## 📐 Credit Risk Metrics

### Delinquency (PAR – Portfolio at Risk)

| Metric | Definition | Source Field |
|--------|-----------|-------------|
| **PAR30** | Balance of loans ≥ 30 DPD / Total balance (%) | `days_past_due` |
| **PAR60** | Balance of loans ≥ 60 DPD / Total balance (%) | `days_past_due` |
| **PAR90** | Balance of loans ≥ 90 DPD / Total balance (%) | `days_past_due` |

> **Status classification**: Portfolio is flagged as **CRITICAL** when `PAR30 > 10%` or `PAR90 > 5%`.

### Default & Loss

| Metric | Definition |
|--------|-----------|
| **Default Rate** | Number of defaulted loans / Total loans (%) |
| **NPL Ratio** | Balance of 90+ DPD loans / Total balance (%) |
| **LGD** | Loss Given Default – actual loss as % of defaulted exposure |
| **Expected Credit Loss** | Composite metric combining PD, LGD, and EAD |
| **Recovery Rate** | Recoveries collected / Defaulted balance (%) |
| **Cost of Risk** | `NPL Ratio × LGD` expressed as % of portfolio |

### Collections & Yield

| Metric | Definition |
|--------|-----------|
| **Collections Coverage** | Actual collections / Scheduled collections (%) |
| **Fee Yield** | `(Origination fee + taxes) / Principal` (%) |
| **Total Yield** | Interest yield + Fee yield (%) |
| **Portfolio Yield** | Gross interest income / Average balance (%) |
| **Net Interest Margin (NIM)** | Gross yield − Funding cost (%) |
| **Cure Rate** | Delinquent loans that returned to current status (%) |

### Portfolio Quality

| Metric | Definition |
|--------|-----------|
| **Credit Quality Index** | `((avg_bureau_score − 300) / 550) × 100` — normalized to 0–100 |
| **Borrower Concentration (HHI)** | Herfindahl-Hirschman Index of borrower-level exposure |
| **Repeat Borrower Rate** | Borrowers with ≥ 2 loans / Total unique borrowers (%) |

---

## 📦 DPD Bucket Classification

Days Past Due (DPD) values are extracted from the `days_past_due` field, with a fallback text-pattern match on `loan_status`:

| Status Text Pattern | Inferred DPD |
|---------------------|-------------|
| `"90+"`, `"default"`, `"charged"` | 100 |
| `"60-89"`, `"60+"` | 75 |
| `"30-59"`, `"30+"` | 45 |
| Otherwise | 0 |

Loans are then assigned to five DPD buckets:

| Bucket | DPD Range | Risk Level |
|--------|-----------|-----------|
| `Current` | 0 | Low |
| `1_30` | 1–30 | Low-Medium |
| `31_60` | 31–60 | Medium |
| `61_90` | 61–90 | Medium-High |
| `90_plus` | 91+ | Critical |

**Implementation**: `python/kpis/advanced_risk.py`

---

## 🚦 Risk Stratification Framework

The risk stratification layer produces two outputs:

### 1. DPD Bucket Breakdown

The `/analytics/risk-stratification` endpoint returns a `buckets` list (same `DPDBucketBreakdown` objects as `AdvancedRiskResponse.dpd_buckets`), `decision_flags`, and a `summary` string. The `/analytics/full-analysis` endpoint additionally includes a `risk_heatmap` field.

The `risk_heatmap` is built separately via `get_risk_heatmap_summary()` and covers the four delinquent buckets only (current loans are excluded). Each bucket has a per-bucket threshold; intensity is classified as follows:

| Bucket | Threshold (%) | `medium` when | `high` when |
|--------|--------------|---------------|-------------|
| Early (1–30 DPD) | 8.0 | exposure > 8% | exposure > 16% |
| Warning (31–60 DPD) | 4.0 | exposure > 4% | exposure > 8% |
| Severe (61–90 DPD) | 2.0 | exposure > 2% | exposure > 4% |
| NPL (91+ DPD) | 1.0 | exposure > 1% | exposure > 2% |

`risk_intensity` values are `low`, `medium`, or `high`. Buckets with `high` intensity are listed in `critical_buckets`.

### 2. Decision Flags (4-flag Assessment)

| Flag | Signal | Status |
|------|--------|--------|
| **Concentration** | HHI-based borrower exposure concentration | 🟢 Green / 🟡 Yellow / 🔴 Red |
| **Asset Quality** | PAR90 / NPL-based delinquency severity | 🟢 / 🟡 / 🔴 |
| **Liquidity** | Collections coverage vs. scheduled collections | 🟢 / 🟡 / 🔴 |
| **Recovery** | Cure rate on delinquent loans | 🟢 / 🟡 / 🔴 |

**Implementation**: `python/apps/analytics/api/main.py` → `POST /analytics/risk-stratification`

---

## 🔗 API Endpoints

All endpoints accept `Content-Type: application/json` and require a list of loan records (see `LoanPortfolioRequest` in `python/apps/analytics/api/models.py`).

### `POST /analytics/advanced-risk`

Returns PAR30/60/90, default rate, collections coverage, yield metrics, recovery rate, concentration, repeat borrower rate, credit quality index, and a `dpd_buckets` list.

The required `LoanRecord` fields are `loan_amount`, `principal_balance`, `interest_rate`, and `loan_status`. `id` is optional.

Request (abridged):

```json
{
  "loans": [
    {
      "id": "L001",
      "loan_amount": 60000,
      "principal_balance": 50000,
      "interest_rate": 12.0,
      "loan_status": "current",
      "days_past_due": 35
    }
  ]
}
```

Response (abridged — all percentage values are 0–100):

```json
{
  "par30": 18.42,
  "par60": 11.77,
  "par90": 6.31,
  "default_rate": 4.82,
  "collections_coverage": 93.44,
  "fee_yield": 1.25,
  "total_yield": 29.81,
  "recovery_rate": 22.17,
  "concentration_hhi": 846.32,
  "repeat_borrower_rate": 27.9,
  "credit_quality_index": 64.55,
  "total_loans": 1247,
  "dpd_buckets": [
    {"bucket": "current", "loan_count": 1066, "balance": 7421000.54, "balance_share_pct": 83.11},
    {"bucket": "90_plus", "loan_count": 31,   "balance":  563122.11, "balance_share_pct": 6.31}
  ]
}
```

### `POST /analytics/risk-stratification`

Returns `buckets` (same `DPDBucketBreakdown` objects as above), `decision_flags` (the 4-flag assessment), and a `summary` string.

### `POST /analytics/risk-alerts`

Identifies high-risk loans based on configurable LTV and DTI thresholds. Returns a `high_risk_count`, `risk_ratio`, and a list of flagged loans with individual scores and alert messages.

### `POST /analytics/unit-economics`

Returns NPL, LGD, Cost of Risk, NIM, CAC payback period, cure rate, and a DPD migration table with per-bucket risk levels and recommended actions.

### `POST /analytics/full-analysis`

Integrates advanced risk, risk stratification, vintage curves, layered insights, unit economics, and portfolio health into a single orchestrated response. Includes a `risk_heatmap` summary.

### `POST /predict/default`

Runs a loan through the default prediction model (XGBoost or PyTorch).

Request:

```json
{
  "loan_amount": 20000,
  "interest_rate": 0.18,
  "term_months": 24,
  "ltv_ratio": 0.75,
  "dti_ratio": 0.35,
  "credit_score": 640,
  "days_past_due": 15,
  "monthly_income": 3500,
  "employment_length_years": 3,
  "num_open_accounts": 4
}
```

Response:

```json
{
  "probability": 0.52,
  "risk_level": "high",
  "model_version": "xgb-v1"
}
```

**Risk Level Classification**:

| Risk Level | Probability Range |
|------------|------------------|
| `low` | < 0.15 |
| `medium` | 0.15 – 0.40 |
| `high` | 0.40 – 0.70 |
| `critical` | ≥ 0.70 |

---

## 🤖 Machine Learning Models

### XGBoost Default Prediction (production)

**File**: `python/models/default_risk_model.py`

| Property | Value |
|----------|-------|
| Algorithm | XGBoost Classifier (gradient boosted trees) |
| Target | Binary (1 = Default, 0 = Not Default) |
| Train / test split | 80 / 20, stratified |
| Early stopping | 30 rounds |
| Regularisation | L1 `alpha=1.0`, L2 `lambda=5.0` |
| Max depth | 4 |
| Min child weight | 10 |
| Class imbalance | Auto-scaled `pos_weight` |
| Serialisation | UBJ binary + JSON metadata sidecar |

**Input features (13)**:

| Feature | Type |
|---------|------|
| `principal_amount` | Numeric |
| `interest_rate` | Numeric |
| `term_months` | Numeric |
| `collateral_value` | Numeric |
| `outstanding_balance` | Numeric |
| `tpv` | Numeric |
| `equifax_score` | Numeric |
| `last_payment_amount` | Numeric |
| `total_scheduled` | Numeric |
| `origination_fee` | Numeric |
| `days_past_due` | Numeric |
| `ltv_ratio` *(engineered)* | `outstanding_balance / collateral_value * 100` |
| `payment_ratio` *(engineered)* | `last_payment_amount / total_scheduled * 100` (clamped to 0 when `total_scheduled = 0`) |

**Evaluation metrics**: AUC-ROC, accuracy, precision, recall, F1, cross-validation AUC.

### PyTorch MLP (research / alternative)

**File**: `python/models/default_risk_torch_model.py`

| Property | Value |
|----------|-------|
| Architecture | 3-layer FC: Input → 64 (ReLU) → 32 (ReLU) → 1 (Sigmoid) |
| Input features | 10 (see below) |
| Normalisation | Per-feature z-score (mean/std stored alongside checkpoint) |

**Input features (10)**: `loan_amount`, `interest_rate`, `term_months`, `ltv_ratio`, `dti_ratio`, `credit_score`, `days_past_due`, `monthly_income`, `employment_length_years`, `num_open_accounts`.

**Backend selection**: Set environment variable `DEFAULT_RISK_MODEL_BACKEND=torch` (default: `xgb`).

---

## ⚙️ Rules-Based Risk Action Engine

**File**: `python/financial_engine/risk_calculator.py`

A Polars-native vectorised engine that assigns recourse strategies to delinquent loans:

| Strategy | Trigger | Action |
|----------|---------|--------|
| **Recourse** | `days_overdue` > 90 | `recourse_action` = `chargeback` |
| **Non-Recourse** | `days_overdue` > 90 and insolvency flag set | `recourse_action` = `insurance_claim` |
| **Hybrid** | Combined recourse / non-recourse portfolio rules | Portfolio-level mix of `chargeback` / `insurance_claim` in `recourse_action` |

---

## 🗄️ SQL Views

### `v_loan_risk_drivers`

**File**: `sql/models/v_loan_risk_drivers.sql`

Surfaces risk drivers aggregated by product (`analytics.v_loan_risk_drivers` grouped by `product_id`):

| Column | Description |
|--------|-------------|
| `loan_count` | Number of loans for the product |
| `total_balance` | Total outstanding balance for the product |
| `par_30_balance` | Balance with DPD ≥ 30 for the product |
| `par_90_balance` | Balance with DPD ≥ 90 for the product |
| `avg_days_past_due` | Average days past due across loans for the product |
| `max_days_past_due` | Maximum days past due for any loan in the product |
| `pct_roll_30` | % of loans for the product rolling to 30+ DPD |
| `pct_roll_90` | % of loans for the product rolling to 90+ DPD |

---

## 📊 Dashboard Visualisations

| Component | Location | Renders |
|-----------|----------|---------|
| DPD bucket distribution bar chart | `streamlit_app/components/sales_risk.py` | Plotly interactive chart |
| Risk heatmap | `streamlit_app/pages/3_Portfolio_Dashboard.py` | Intensity grid |
| Data quality audit score | `streamlit_app/components/sales_risk.py` | Score badge |
| NSM Recurrent TPV | `streamlit_app/pages/3_Portfolio_Dashboard.py` | KPI tile + trend line |

---

## 🧪 Testing

| Test File | Scope |
|-----------|-------|
| `tests/test_default_risk_model.py` | XGBoost: loading, prediction bounds, batch inference, API contracts |
| `python/tests/test_advanced_risk.py` | KPI metric calculations (PAR, default rate, credit quality index) |
| `python/tests/test_advanced_risk_api.py` | API endpoints: advanced risk, full analysis, risk stratification |
| `tests/agents/test_concrete_agents/test_risk_agent.py` | Multi-agent risk analysis agent |

Run all credit risk tests:

```bash
pytest tests/test_default_risk_model.py python/tests/test_advanced_risk.py python/tests/test_advanced_risk_api.py -v
```

---

## 🔑 Key Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `DEFAULT_RISK_MODEL_BACKEND` | `xgb` | ML backend: `xgb` (XGBoost) or `torch` (PyTorch) |
| `SUPABASE_URL` | — | Supabase project URL for persistent storage |
| `SUPABASE_KEY` | — | Supabase service role key |

Model artefacts are stored under `models/risk/` and are lazy-loaded and cached on the first `/predict/default` request; they are reloaded only when `DEFAULT_RISK_MODEL_BACKEND` changes.

---

## 📚 Related Documentation

- [`docs/KPI_CATALOG.md`](KPI_CATALOG.md) – Full KPI definitions and SQL views
- [`docs/DATA_DICTIONARY.md`](DATA_DICTIONARY.md) – Canonical field names and aliases
- [`docs/GOVERNANCE.md`](GOVERNANCE.md) – Data governance and access controls
- [`docs/ML_CONTINUOUS_LEARNING_ROADMAP.md`](ML_CONTINUOUS_LEARNING_ROADMAP.md) – Model retraining strategy
- [`docs/API_SECURITY_GUIDE.md`](API_SECURITY_GUIDE.md) – Authentication and rate limiting
