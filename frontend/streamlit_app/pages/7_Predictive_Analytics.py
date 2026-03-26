import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from backend.python.config.theme import ANALYTICS_THEME
from backend.python.models.default_risk_model import DefaultRiskModel
st.set_page_config(page_title='Predictive Analytics', layout='wide')
st.markdown(f"\n    <style>\n    .main {{\n        background-color: {ANALYTICS_THEME['colors']['background']};\n        color: {ANALYTICS_THEME['colors']['white']};\n    }}\n    .metric-container {{\n        background-color: #1e2130;\n        padding: 20px;\n        border-radius: 10px;\n        border: 1px solid #30363d;\n    }}\n    </style>\n    ", unsafe_allow_html=True)
st.title('🔮 Predictive Analytics')
st.subheader('Probability of Default (PD) Model Control Room')
MODEL_DIR = Path('models/risk')
SCORECARD_DIR = Path('models/scorecard')
metrics = {}
metadata_path = MODEL_DIR / 'default_risk_metadata.json'
if metadata_path.exists():
    with open(metadata_path) as f:
        meta = json.load(f)
        metrics = meta.get('metrics', {})
IV_PATH = SCORECARD_DIR / 'iv_table.csv'
if IV_PATH.exists():
    iv_df = pd.read_csv(IV_PATH)
    st.header('1. Predictive Power (Information Value)')
    st.info('The Information Value (IV) reveals which variables from your data actually separate defaults from paid loans.')
    iv_df['Power'] = iv_df['predictive_power'].map({'Strong': 'Fuerte', 'Medium': 'Medio', 'Weak': 'Débil', 'Useless': 'None'})
    col_iv1, col_iv2 = st.columns([2, 1])
    with col_iv1:
        fig_iv = px.bar(iv_df.head(15), x='iv', y='feature', orientation='h', color='Power', color_discrete_map={'Fuerte': '#00cc96', 'Medio': '#636efa', 'Débil': '#ef553b', 'None': '#30363d'}, title='Information Value (IV) Ranking (Top 15)')
        fig_iv.update_layout(template='plotly_dark')
        st.plotly_chart(fig_iv, use_container_width=True)
    with col_iv2:
        st.write('### Top Predictors')
        for idx, row in iv_df.head(3).iterrows():
            st.success(f"**{row['feature']}** (IV: {row['iv']:.3f})")
    st.divider()
st.header('2. Model Health & Validation')
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric('AUC-ROC', f"{metrics.get('auc_roc', 0):.4f}", help='Area Under the Receiver Operating Characteristic Curve')
with col2:
    st.metric('Gini Coefficient', f"{metrics.get('gini_coefficient', 0):.4f}", help='2 * AUC - 1')
with col3:
    st.metric('KS Statistic', f"{metrics.get('ks_statistic', 0):.4f}", help='Kolmogorov-Smirnov separation power')
with col4:
    st.metric('Accuracy', f"{metrics.get('accuracy', 0):.4f}")
st.divider()
st.header('Feature Importance')
importance = metrics.get('feature_importance', {})
if importance:
    importance_df = pd.DataFrame([{'Feature': k, 'Importance': v} for k, v in importance.items()]).sort_values('Importance', ascending=True)
    fig = px.bar(importance_df, y='Feature', x='Importance', orientation='h', title='XGBoost Feature Gain', color='Importance', color_continuous_scale='Viridis')
    fig.update_layout(template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('Feature importance data not available.')
st.divider()
st.header('3. Retraining Pipeline')
with st.expander('Pipeline Configuration'):
    loan_file = st.text_input('Loan Data Path', 'data/samples/loans_sample_data_20260202.csv')
    payment_file = st.text_input('Payment Data Path (Optional)', 'data/raw/real_payment.csv')
    customer_file = st.text_input('Customer Data Path (Optional)', 'data/raw/customer_data.csv')
    threshold = st.slider('Deployment Threshold (AUC)', 0.5, 1.0, 0.7)
    iv_thresh = st.slider('Feature Selection (IV Threshold)', 0.0, 0.5, 0.02, step=0.01)
    if st.button('Manual Retrain'):
        with st.spinner('Executing retraining pipeline (Phase 1 & 2)...'):
            from scripts.ml.retrain_pipeline import run_pipeline
            success = run_pipeline(loan_path=Path(loan_file), payment_path=Path(payment_file), customer_path=Path(customer_file), model_dir=MODEL_DIR, threshold_auc=threshold, iv_threshold=iv_thresh)
            if success:
                st.success('Retraining successful! New XGBoost model deployed with IV-selected features.')
                st.rerun()
            else:
                st.error('Retraining failed or threshold not met.')
st.divider()
st.header('Scoring Simulator')
st.info('Test the model with individual loan parameters.')
sim_col1, sim_col2 = st.columns(2)
with sim_col1:
    principal = st.number_input('Principal Amount', value=50000.0)
    interest = st.number_input('Interest Rate (%)', value=12.5)
    term = st.slider('Term (Months)', 1, 60, 24)
    collateral = st.number_input('Collateral Value', value=100000.0)
    equifax = st.slider('Equifax Score', 300, 850, 650)
with sim_col2:
    outstanding = st.number_input('Outstanding Balance', value=45000.0)
    tpv = st.number_input('TPV (Last 12m)', value=250000.0)
    last_payment = st.number_input('Last Payment Amount', value=2500.0)
    total_scheduled = st.number_input('Total Scheduled Amount', value=3000.0)
    dpd = st.number_input('Days Past Due', value=0)
if st.button('Predict Probability of Default'):
    try:
        model = DefaultRiskModel.load(MODEL_DIR / 'default_risk_xgb.ubj')
        input_data = {'principal_amount': principal, 'interest_rate': interest, 'term_months': term, 'collateral_value': collateral, 'equifax_score': equifax, 'outstanding_balance': outstanding, 'tpv': tpv, 'last_payment_amount': last_payment, 'total_scheduled': total_scheduled, 'days_past_due': dpd, 'origination_fee': 0.0}
        prob = model.predict_proba(input_data)
        st.subheader('Result')
        prob_pct = prob * 100
        if prob_pct < 10:
            color = 'green'
        elif prob_pct < 30:
            color = 'orange'
        else:
            color = 'red'
        st.markdown(f"### Estimated PD: <span style='color:{color}'>{prob_pct:.2f}%</span>", unsafe_allow_html=True)
        if prob_pct < 10:
            st.success('Low Risk')
        elif prob_pct < 30:
            st.warning('Medium Risk')
        else:
            st.error('High Risk')
    except Exception as e:
        st.error(f'Error during prediction: {e}')
