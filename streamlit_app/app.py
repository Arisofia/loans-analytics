import pandas as pd
import streamlit as st
import altair as alt
from utils.feature_engineering import FeatureEngineer
from utils.kri_calculator import KRICalculator

st.set_page_config(layout="wide", page_title="Abaco Loans Analytics Dashboard")

# --- Data Ingestion Simulation ---
@st.cache_data
def load_and_prepare_data():
    # In a real-world scenario, this would load data from a database or data warehouse.
    data = {
        'customer_id': range(100),
        'revenue': pd.np.random.uniform(10000, 150000, 100),
        'balance': pd.np.random.uniform(1000, 50000, 100),
        'limit': pd.np.random.uniform(20000, 100000, 100),
        'dpd': pd.np.random.choice([-1, 0, 15, 45, 75, 100], 100, p=[0.1, 0.6, 0.1, 0.1, 0.05, 0.05]),
    }
    raw_df = pd.DataFrame(data)

    # Simulate data quality score
    completeness = (raw_df.notna().sum().sum() / (raw_df.shape[0] * raw_df.shape[1])) * 100
    return raw_df, completeness

# --- Main Application ---
st.title("Abaco Loans Analytics Dashboard")

# 1. Ingestion and Enrichment
raw_portfolio_df, data_quality_score = load_and_prepare_data()
enriched_df = FeatureEngineer.enrich_portfolio(raw_portfolio_df)
kri_metrics = KRICalculator.calculate(enriched_df)
kri_mix = KRICalculator.segment_risk_mix(enriched_df)

# 2. Display High-Level Metrics
st.header("Portfolio Health & Quality Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Data Quality Score", f"{data_quality_score:.2f}%", help="Completeness of the source data.")
col2.metric("Benchmark Rotation", "94%", "1.5% vs. Target", delta_color="inverse")
col3.metric("Collection Target", "88%", "-4% vs. Target")
col4.metric("Portfolio Yield", "12.3%", "0.8% vs. Last Q")

# 3. Key Risk Indicators
st.header("Key Risk Indicators (KRIs)")
kri_col1, kri_col2, kri_col3 = st.columns(3)
kri_col1.metric("30+ Delinquency Rate", f"{kri_metrics.delinquency_30_plus_rate:.2%}" if pd.notna(kri_metrics.delinquency_30_plus_rate) else "N/A")
kri_col2.metric("90+ Delinquency Rate", f"{kri_metrics.delinquency_90_plus_rate:.2%}" if pd.notna(kri_metrics.delinquency_90_plus_rate) else "N/A")
kri_col3.metric("Average DPD", f"{kri_metrics.average_dpd:.1f}" if pd.notna(kri_metrics.average_dpd) else "N/A")

kri_col4, kri_col5, _ = st.columns(3)
kri_col4.metric("Avg Utilization", f"{kri_metrics.average_utilization:.2%}" if pd.notna(kri_metrics.average_utilization) else "N/A")
kri_col5.metric("High Utilization Share", f"{kri_metrics.high_utilization_share:.2%}" if pd.notna(kri_metrics.high_utilization_share) else "N/A")

if kri_mix is not None:
    st.subheader("Risk Mix by Segment")
    st.dataframe(kri_mix.style.format("{:.0%}"))

# 4. Display Distribution Charts
st.header("Customer Distributions")
col_dist1, col_dist2 = st.columns(2)

with col_dist1:
    dpd_chart = alt.Chart(enriched_df).mark_bar().encode(
        x=alt.X('dpd_bucket:N', title='DPD Bucket', sort=['Current', '1-30 DPD', '31-60 DPD', '61-90 DPD', '90+ DPD']),
        y=alt.Y('count():Q', title='Number of Customers'),
        tooltip=['dpd_bucket', 'count()']
    ).properties(
        title='DPD Bucket Distribution'
    )
    st.altair_chart(dpd_chart, use_container_width=True)

with col_dist2:
    segment_chart = alt.Chart(enriched_df).mark_bar().encode(
        x=alt.X('segment:N', title='Customer Segment', sort=['Bronze', 'Silver', 'Gold']),
        y=alt.Y('count():Q', title='Number of Customers'),
        tooltip=['segment', 'count()']
    ).properties(
        title='Customer Segment Distribution'
    )
    st.altair_chart(segment_chart, use_container_width=True)

# 5. Display Customer Data Table
st.header("Enriched Customer Portfolio Data")
st.dataframe(enriched_df)
st.caption("Industry GDP Benchmark: +2.1% (YoY)")
