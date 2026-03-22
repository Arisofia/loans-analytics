import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.python.config.theme import ABACO_THEME
from backend.python.models.default_risk_model import DefaultRiskModel

st.set_page_config(page_title="Predictive Analytics - Abaco", layout="wide")

st.markdown(
    f"""
    <style>
    .main {{
        background-color: {ABACO_THEME['colors']['background']};
        color: {ABACO_THEME['colors']['white']};
    }}
    .metric-container {{
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔮 Predictive Analytics")
st.subheader("Probability of Default (PD) Model Control Room")

# ---------------------------------------------------------------------------
# Load Model Metadata
# ---------------------------------------------------------------------------
MODEL_DIR = Path("models/risk")
METADATA_PATH = MODEL_DIR / "default_risk_metadata.json"

if not METADATA_PATH.exists():
    st.warning("No trained model found. Please run the retraining pipeline.")
    if st.button("Run Initial Training"):
        with st.spinner("Training model..."):
            from scripts.ml.retrain_pipeline import run_pipeline
            success = run_pipeline(
                Path("data/samples/abaco_sample_data_20260202.csv"),
                MODEL_DIR
            )
            if success:
                st.success("Model trained successfully!")
                st.rerun()
            else:
                st.error("Training failed. Check logs.")
    st.stop()

with open(METADATA_PATH) as f:
    metadata = json.load(f)

metrics = metadata.get("metrics", {})

# ---------------------------------------------------------------------------
# Section 1: Model Health & Validation
# ---------------------------------------------------------------------------
st.header("Model Health & Validation")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("AUC-ROC", f"{metrics.get('auc_roc', 0):.4f}", help="Area Under the Receiver Operating Characteristic Curve")
with col2:
    st.metric("Gini Coefficient", f"{metrics.get('gini_coefficient', 0):.4f}", help="2 * AUC - 1")
with col3:
    st.metric("KS Statistic", f"{metrics.get('ks_statistic', 0):.4f}", help="Kolmogorov-Smirnov separation power")
with col4:
    st.metric("Accuracy", f"{metrics.get('accuracy', 0):.4f}")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Feature Importance
# ---------------------------------------------------------------------------
st.header("Feature Importance")
importance = metrics.get("feature_importance", {})
if importance:
    importance_df = pd.DataFrame([
        {"Feature": k, "Importance": v} for k, v in importance.items()
    ]).sort_values("Importance", ascending=True)

    fig = px.bar(
        importance_df,
        y="Feature",
        x="Importance",
        orientation="h",
        title="XGBoost Feature Gain",
        color="Importance",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Feature importance data not available.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Retraining Pipeline
# ---------------------------------------------------------------------------
st.header("Retraining Pipeline")
with st.expander("Pipeline Configuration"):
    input_file = st.text_input("Input Data Path", "data/samples/abaco_sample_data_20260202.csv")
    threshold = st.slider("Deployment Threshold (AUC)", 0.5, 1.0, 0.7)

    if st.button("Manual Retrain"):
        with st.spinner("Executing retraining pipeline..."):
            from scripts.ml.retrain_pipeline import run_pipeline
            success = run_pipeline(Path(input_file), MODEL_DIR, threshold_auc=threshold)
            if success:
                st.success("Retraining successful! New model deployed.")
                st.rerun()
            else:
                st.error("Retraining failed or threshold not met.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Scoring Simulator (Interactive)
# ---------------------------------------------------------------------------
st.header("Scoring Simulator")
st.info("Test the model with individual loan parameters.")

sim_col1, sim_col2 = st.columns(2)

with sim_col1:
    principal = st.number_input("Principal Amount", value=50000.0)
    interest = st.number_input("Interest Rate (%)", value=12.5)
    term = st.slider("Term (Months)", 1, 60, 24)
    collateral = st.number_input("Collateral Value", value=100000.0)
    equifax = st.slider("Equifax Score", 300, 850, 650)

with sim_col2:
    outstanding = st.number_input("Outstanding Balance", value=45000.0)
    tpv = st.number_input("TPV (Last 12m)", value=250000.0)
    last_payment = st.number_input("Last Payment Amount", value=2500.0)
    total_scheduled = st.number_input("Total Scheduled Amount", value=3000.0)
    dpd = st.number_input("Days Past Due", value=0)

if st.button("Predict Probability of Default"):
    # Load model
    try:
        model = DefaultRiskModel.load(MODEL_DIR / "default_risk_xgb.ubj")
        input_data = {
            "principal_amount": principal,
            "interest_rate": interest,
            "term_months": term,
            "collateral_value": collateral,
            "equifax_score": equifax,
            "outstanding_balance": outstanding,
            "tpv": tpv,
            "last_payment_amount": last_payment,
            "total_scheduled": total_scheduled,
            "days_past_due": dpd,
            "origination_fee": 0.0 # Placeholder
        }
        
        # Engineering inside the model (or use FeatureStore)
        prob = model.predict_proba(input_data)
        
        st.subheader("Result")
        prob_pct = prob * 100
        
        color = "green" if prob_pct < 10 else "orange" if prob_pct < 30 else "red"
        st.markdown(f"### Estimated PD: <span style='color:{color}'>{prob_pct:.2f}%</span>", unsafe_allow_html=True)
        
        if prob_pct < 10:
            st.success("Low Risk")
        elif prob_pct < 30:
            st.warning("Medium Risk")
        else:
            st.error("High Risk")
            
    except Exception as e:
        st.error(f"Error during prediction: {e}")
