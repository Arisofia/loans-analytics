import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
from backend.python.models.default_risk_model import DefaultRiskModel
from .visualizations import apply_theme, styled_df
MODEL_PATH = Path(__file__).resolve().parents[3] / 'models' / 'risk' / 'default_risk_xgb.ubj'

def render_predictive_risk(merged_df: pd.DataFrame):
    st.header('🔮 Predictive Intelligence (PD Model)')
    if not MODEL_PATH.exists():
        st.warning('⚠️ Default Risk Model (XGBoost) not found. Please run the training script.')
        if st.button('Run Training Script'):
            with st.spinner('Training model on current data...'):
                st.info('Please run: python scripts/ml/train_default_risk_model.py')
        return
    try:
        model = DefaultRiskModel.load(MODEL_PATH)
    except Exception as e:
        st.error(f'Error loading model: {e}')
        return
    st.subheader('Probability of Default (PD) Scoring')
    try:
        features_df = model.prepare_features(merged_df)
        import xgboost as xgb
        dmatrix = xgb.DMatrix(features_df)
        probs = model.model.predict(dmatrix)
        merged_df['pd_score'] = probs
        merged_df['risk_rating'] = pd.cut(merged_df['pd_score'], bins=[0, 0.05, 0.15, 0.3, 1.0], labels=['Low (0-5%)', 'Medium (5-15%)', 'High (15-30%)', 'Critical (30%+)'])
    except Exception as e:
        st.error(f'Prediction error: {e}')
        return
    col1, col2 = st.columns(2)
    with col1:
        fig_dist = px.histogram(merged_df, x='pd_score', nbins=20, title='Distribution of Default Probabilities', labels={'pd_score': 'Probability of Default'}, color_discrete_sequence=['#636EFA'])
        st.plotly_chart(apply_theme(fig_dist), use_container_width=True)
    with col2:
        risk_counts = merged_df['risk_rating'].value_counts().reset_index()
        risk_counts.columns = ['Rating', 'Count']
        fig_pie = px.pie(risk_counts, values='Count', names='Rating', title='Portfolio Risk Composition', color='Rating', color_discrete_map={'Low (0-5%)': 'green', 'Medium (5-15%)': 'yellow', 'High (15-30%)': 'orange', 'Critical (30%+)': 'red'})
        st.plotly_chart(apply_theme(fig_pie), use_container_width=True)
    st.subheader('Top High-Risk Accounts')
    high_risk = merged_df[merged_df['pd_score'] > 0.15].sort_values('pd_score', ascending=False)
    display_cols = ['loan_id', 'pd_score', 'risk_rating', 'outstanding_loan_value', 'days_in_default']
    available_cols = [c for c in display_cols if c in high_risk.columns]
    if not high_risk.empty:
        st.dataframe(styled_df(high_risk[available_cols]), use_container_width=True)
    else:
        st.success('✅ No high-risk accounts detected in the current portfolio.')
    if 'metrics' in model.metadata and 'feature_importance' in model.metadata['metrics']:
        st.subheader('Model Decision Factors (Transparency)')
        importances = model.metadata['metrics']['feature_importance']
        imp_df = pd.DataFrame(list(importances.items()), columns=['Feature', 'Importance'])
        imp_df = imp_df.sort_values('Importance', ascending=True)
        fig_imp = px.bar(imp_df, x='Importance', y='Feature', orientation='h', title='Top Predictors of Default')
        st.plotly_chart(apply_theme(fig_imp), use_container_width=True)
