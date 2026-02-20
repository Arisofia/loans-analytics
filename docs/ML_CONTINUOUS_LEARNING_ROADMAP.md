# 🔮 Machine Learning & Continuous Learning Roadmap

**Strategic plan for implementing predictive models and automated learning pipelines in Abaco Loans Analytics**

---

## 📊 Current State: Rule-Based + AI Hybrid

### What We Have Now ✅

1. **Multi-Agent AI System**
   - 9 specialized LLM agents (GPT-4, Claude, Gemini)
   - Natural language query interface
   - Real-time insights and recommendations
   - Location: `python/multi_agent/`

2. **KPI Calculation Engine**
   - 19 financial metrics with formulas
   - Threshold-based alerting
   - Trend analysis capabilities
   - Location: `python/kpis/`

3. **Data Pipeline**
   - 4-phase ETL (Ingestion → Transformation → Calculation → Output)
   - Historical data storage (Supabase)
   - Time series tracking
   - Location: `src/pipeline/`

4. **Analytics Dashboard**
   - Interactive Streamlit interface
   - Real-time KPI visualization
   - Data exploration tools
   - Location: `streamlit_app/`

### What We DON'T Have Yet ❌

1. **Traditional ML Models**
   - scikit-learn, XGBoost, LightGBM models
   - Structured prediction pipelines
   - Model versioning and registry

2. **Automated Retraining**
   - Scheduled model updates
   - Performance monitoring
   - Drift detection

3. **Prediction APIs**
   - Default risk scoring
   - Churn probability
   - Dynamic pricing suggestions

4. **A/B Testing Framework**
   - Experiment tracking
   - Statistical validation
   - Gradual rollout

---

## 🎯 Implementation Roadmap

### Phase 1: Data Foundation (COMPLETE ✅)

**Duration**: Already implemented  
**Status**: Production-ready

**Deliverables**:

- ✅ Historical loan data storage (Supabase)
- ✅ KPI time series tracking (`kpi_timeseries_daily` table)
- ✅ Data quality monitoring (validation framework)
- ✅ Feature engineering pipeline (transformation phase)

---

### Phase 2: Model Development (3-6 Months)

**Goal**: Build and validate initial ML models for core business problems

#### 2.1 Default Risk Prediction (Month 1-2)

**Objective**: Predict probability of loan default at origination

**Model Approach**:

```python
# Target variable
y = (loan['days_past_due'] > 90).astype(int)  # NPL definition

# Features
features = [
    'principal_amount',
    'duration_months',
    'apr',
    'customer_age',
    'customer_income',
    'customer_credit_score',
    'invoice_count',
    'industry_sector',
    'previous_defaults',
    'debt_to_income_ratio',
]

# Model candidates
models = [
    'LogisticRegression',  # Baseline, interpretable
    'RandomForest',        # Good feature importance
    'XGBoost',             # Best performance usually
    'LightGBM',            # Fast training
]
```

**Evaluation Metrics**:

- AUC-ROC (target: >0.75)
- Precision at 80% recall (minimize false positives)
- Calibration curve (well-calibrated probabilities)
- Feature importance analysis

**Deliverables**:

- [ ] Training notebook: `notebooks/models/default_risk_v1.ipynb`
- [ ] Production model: `models/risk/default_predictor.pkl`
- [ ] API endpoint: `POST /predict/default`
- [ ] Monitoring dashboard: Grafana panel for prediction distribution

#### 2.2 Customer Churn Prediction (Month 2-3)

**Objective**: Identify customers at risk of leaving

**Target Definition**:

- No new loans in 90 days after previous loan payoff
- Active customer → Inactive status

**Features**:

```python
features = [
    'total_lifetime_value',
    'number_of_loans',
    'avg_loan_size',
    'days_since_last_loan',
    'average_repayment_delay',
    'customer_lifetime_months',
    'net_promoter_score',  # If available
    'support_ticket_count',
]
```

**Use Cases**:

- Proactive retention campaigns
- Targeted discount offers
- Priority customer support

**Deliverables**:

- [ ] Churn model: `models/retention/churn_predictor.pkl`
- [ ] API endpoint: `POST /predict/churn`
- [ ] Retention agent integration (trigger alerts)

#### 2.3 Dynamic Pricing Optimization (Month 3-4)

**Objective**: Recommend optimal APR for new loan applications

**Model Type**: Multi-output regression or reinforcement learning

**Inputs**:

```python
context = {
    'customer_risk_score': 0.12,  # From default model
    'requested_amount': 50000,
    'requested_duration': 12,
    'market_rate': 0.35,
    'competitive_rates': [0.32, 0.34, 0.36],
    'customer_ltv': 250000,
}
```

**Outputs**:

```python
recommendation = {
    'suggested_apr': 0.34,
    'expected_profit': 8500,
    'default_probability': 0.12,
    'acceptance_probability': 0.85,
}
```

**Constraints**:

- APR within regulatory limits (18%-40%)
- Risk-adjusted minimum return (RORAC > 15%)
- Competitive positioning

**Deliverables**:

- [ ] Pricing model: `models/pricing/apr_optimizer.pkl`
- [ ] API endpoint: `POST /predict/optimal_price`
- [ ] Pricing agent integration

#### 2.4 Fraud Detection Scoring (Month 4-6)

**Objective**: Real-time anomaly detection for suspicious loan applications

**Approach**: Unsupervised learning + supervised fine-tuning

**Anomaly Types**:

1. **Identity Fraud**: Inconsistent customer information
2. **Application Fraud**: Suspicious patterns (velocity, amount)
3. **First-Party Fraud**: Intentional non-payment
4. **Synthetic Identity**: Fake customer profiles

**Models**:

```python
# Unsupervised baseline
models = [
    'IsolationForest',     # Anomaly detection
    'Autoencoder',         # Deep learning approach
    'LocalOutlierFactor',  # Density-based
]

# Supervised (if labeled fraud data exists)
models = [
    'XGBoost',  # With SMOTE for class imbalance
    'LightGBM',
]
```

**Features**:

```python
features = [
    'application_velocity',  # Applications per day
    'device_fingerprint',
    'ip_address_country',
    'phone_number_age',
    'email_domain_reputation',
    'address_verification_status',
    'behavioral_biometrics',  # Typing speed, mouse patterns
]
```

**Deliverables**:

- [ ] Fraud scoring model: `models/fraud/fraud_detector.pkl`
- [ ] Real-time API: `POST /predict/fraud_score`
- [ ] Alert system integration (Email/PagerDuty)

---

### Phase 3: Continuous Learning Infrastructure (6-9 Months)

**Goal**: Automate model lifecycle management

#### 3.1 Model Training Pipeline

**Components**:

1. **Data Preparation Service**

   ```python
   # Scheduled job (daily at 2 AM)
   class ModelDataPreparation:
       def run(self):
           # 1. Extract latest data from Supabase
           # 2. Feature engineering
           # 3. Train/test split (time-based)
           # 4. Save to staging area
           pass
   ```

2. **Training Orchestrator**

   ```python
   # Triggered when new data available
   class ModelTrainer:
       def run(self, model_name: str):
           # 1. Load training data
           # 2. Cross-validation
           # 3. Hyperparameter tuning
           # 4. Train final model
           # 5. Validate performance
           # 6. Save to model registry
           pass
   ```

3. **Model Registry** (MLflow)

   ```python
   import mlflow

   mlflow.log_model(
       model,
       "default-risk-predictor",
       registered_model_name="default_risk",
   )
   mlflow.log_metrics({
       "auc_roc": 0.82,
       "precision_at_80_recall": 0.65,
   })
   ```

**Deliverables**:

- [ ] Training pipeline: `python/ml/training_pipeline.py`
- [ ] MLflow server setup: `docker-compose.mlflow.yml`
- [ ] Scheduled retraining: `.github/workflows/retrain_models.yml`

#### 3.2 Model Performance Monitoring

**Metrics to Track**:

1. **Prediction Quality**
   - AUC-ROC over time
   - Calibration drift
   - Precision/Recall trends

2. **Data Drift**
   - Feature distribution changes
   - Concept drift detection
   - Covariate shift

3. **Business Impact**
   - Model-driven decision outcomes
   - Revenue impact
   - Risk-adjusted returns

**Tools**:

```yaml
# Monitoring stack
tools:
  - evidently: Data drift detection
  - whylogs: Data profiling
  - prometheus: Metrics collection
  - grafana: Visualization
```

**Deliverables**:

- [ ] Monitoring dashboard: `grafana/dashboards/ml_monitoring.json`
- [ ] Drift detection service: `python/ml/drift_detector.py`
- [ ] Alert rules: `config/rules/ml_alerts.yml`

#### 3.3 A/B Testing Framework

**Architecture**:

```python
class ExperimentManager:
    def create_experiment(
        self,
        name: str,
        variants: list[str],
        traffic_split: dict[str, float],
    ):
        """
        Example:
        create_experiment(
            name="default_model_v2_vs_v1",
            variants=["model_v1", "model_v2"],
            traffic_split={"model_v1": 0.8, "model_v2": 0.2},
        )
        """
        pass

    def get_variant(self, customer_id: str, experiment_name: str) -> str:
        """Consistent assignment using hash."""
        pass

    def log_outcome(
        self,
        experiment_name: str,
        variant: str,
        outcome: dict,
    ):
        """Record experiment results."""
        pass

    def analyze_results(self, experiment_name: str) -> dict:
        """Statistical significance testing."""
        pass
```

**Integration Example**:

```python
# In prediction API
experiment = experiments.get_variant(customer_id, "churn_model_v2")

if experiment == "model_v2":
    prediction = churn_model_v2.predict(features)
else:
    prediction = churn_model_v1.predict(features)

experiments.log_outcome(
    "churn_model_v2",
    experiment,
    {"prediction": prediction, "actual_churn": None}  # Actual filled later
)
```

**Deliverables**:

- [ ] Experiment framework: `python/ml/experiments.py`
- [ ] Analysis notebook: `notebooks/experiment_analysis.ipynb`
- [ ] Monitoring dashboard: Grafana panel for experiment results

---

### Phase 4: Advanced ML (9-12 Months)

**Goal**: State-of-the-art techniques for competitive advantage

#### 4.1 Deep Learning Models

**Use Cases**:

- Time series forecasting (cash flow predictions)
- NLP for loan application text analysis
- Computer vision for document verification

**Models to Explore**:

- LSTM/GRU for sequential data
- Transformers for text (BERT, GPT)
- CNNs for document images

#### 4.2 Reinforcement Learning

**Use Cases**:

- Dynamic collections strategies
- Portfolio allocation optimization
- Adaptive pricing policies

#### 4.3 Explainable AI (XAI)

**Regulatory Compliance**:

- SHAP values for model interpretability
- LIME for local explanations
- Counterfactual explanations for loan rejections

**Tools**:

```python
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Generate explanation for decision
explanation = {
    'prediction': 0.85,  # High risk
    'top_factors': [
        {'feature': 'days_past_due_history', 'impact': +0.3},
        {'feature': 'debt_to_income', 'impact': +0.15},
        {'feature': 'customer_age', 'impact': -0.05},
    ]
}
```

---

## 🛠️ Technology Stack

### Model Development

```yaml
Training:
  - scikit-learn: Traditional ML algorithms
  - XGBoost: Gradient boosting
  - LightGBM: Fast gradient boosting
  - TensorFlow/PyTorch: Deep learning (future)

Feature Engineering:
  - pandas: Data manipulation
  - polars: Fast dataframes (large datasets)
  - feature-engine: Automated feature engineering

Experiment Tracking:
  - MLflow: Model registry, experiment tracking
  - Weights & Biases: Advanced experiment management (optional)
```

### Model Deployment

```yaml
Serving:
  - FastAPI: REST API endpoints
  - ONNX Runtime: Fast inference
  - TorchServe: For PyTorch models (future)

Orchestration:
  - Apache Airflow: Workflow scheduling
  - Prefect: Modern orchestration (alternative)
  - GitHub Actions: Lightweight workflows

Monitoring:
  - Evidently AI: Data drift detection
  - Prometheus: Metrics collection
  - Grafana: Visualization
```

### Infrastructure

```yaml
Compute:
  - Azure ML: Cloud training (GPU/TPU)
  - Azure Functions: Serverless inference
  - Azure Kubernetes Service: Scalable serving (future)

Storage:
  - Supabase: Operational database
  - Azure Blob Storage: Model artifacts
  - MLflow: Model registry

CI/CD:
  - GitHub Actions: Automated testing & deployment
  - Azure DevOps: Enterprise workflows (alternative)
```

---

## 📈 Success Metrics

### Technical Metrics

| Metric                  | Target    | Current               |
| ----------------------- | --------- | --------------------- |
| Default Prediction AUC  | >0.75     | N/A (not implemented) |
| Churn Prediction AUC    | >0.70     | N/A                   |
| Model Training Time     | <4 hours  | N/A                   |
| Inference Latency (p95) | <100ms    | N/A                   |
| Data Drift Detection    | <24 hours | N/A                   |

### Business Metrics

| Metric                    | Target         | Impact                  |
| ------------------------- | -------------- | ----------------------- |
| Reduction in Default Rate | -0.5%          | $200K+ savings annually |
| Churn Prevention          | 20% of at-risk | $100K+ retained revenue |
| Pricing Optimization      | +2% margin     | $150K+ revenue increase |
| Fraud Detection           | 90% catch rate | $50K+ loss prevention   |

---

## 🚀 Getting Started Today

While full ML infrastructure is being built, you can:

### 1. Use Multi-Agent AI for Predictions

```bash
# Risk assessment
python -m python.multi_agent.cli run-agent \
  --role RISK_ANALYST \
  --query "Predict default risk for loans with these characteristics: principal=$50K, DPD history=2 instances, debt-to-income=0.45"

# Churn prediction
python -m python.multi_agent.cli run-agent \
  --role RETENTION \
  --query "Which customers are likely to churn based on: 90 days since last loan, 3 total loans, average delay 5 days"

# Pricing recommendation
python -m python.multi_agent.cli run-agent \
  --role PRICING \
  --query "Recommend APR for: $75K loan, 12 months, customer risk score 0.15, market rate 34%"
```

### 2. Analyze Historical Data

```bash
# Run KPI analysis to identify trends
python scripts/data/run_data_pipeline.py --input data/raw/loans.csv

# View results in Streamlit
streamlit run streamlit_app.py
```

### 3. Build Simple Models (Prototype)

```python
# Quick prototype in notebook
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('data/processed/loans.csv')

# Simple default model
X = df[['principal', 'duration', 'apr', 'dpd_history']]
y = (df['status'] == 'defaulted').astype(int)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import roc_auc_score
score = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
print(f"AUC: {score:.3f}")
```

---

## 📚 Resources

### Learning Materials

- **ML for Credit Risk**: [Risk Modeling Handbook](https://www.risk.net/)
- **MLOps Best Practices**: [Google MLOps Guide](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)
- **Model Monitoring**: [Evidently AI Docs](https://docs.evidentlyai.com/)

### Tools Documentation

- [MLflow](https://mlflow.org/docs/latest/index.html)
- [XGBoost](https://xgboost.readthedocs.io/)
- [FastAPI ML Deployment](https://fastapi.tiangolo.com/advanced/custom-response/)

### Internal Docs

- Multi-Agent System: `python/multi_agent/README.md`
- KPI Definitions: `config/kpis/kpi_definitions.yaml`
- Pipeline Architecture: `docs/OPERATIONS.md`

---

## 🤝 Contributing

To contribute to ML development:

1. **Data Scientists**: Create notebooks in `notebooks/models/`
2. **ML Engineers**: Build pipelines in `python/ml/`
3. **DevOps**: Setup infrastructure in `infra/ml/`
4. **QA**: Test models in `tests/ml/`

See: `docs/GOVERNANCE.md`

---

## 📞 Questions?

- **Technical**: Open GitHub issue with `[ML]` tag
- **Business**: Contact Analytics Team Lead
- **Strategy**: Refer to quarterly OKRs

---

**Last Updated**: 2026-02-02  
**Status**: Roadmap Document - Phase 1 Complete, Phase 2 Planning  
**Next Review**: 2026-03-01
