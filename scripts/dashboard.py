import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

st.set_page_config(page_title="Abaco Loans Analytics", layout="wide")

def load_latest_metrics():
    # Find all CSV files in the metrics folder
    list_of_files = glob.glob('data/metrics/*.csv')
    if not list_of_files:
        return None, None
    
    # Get the most recent file based on creation time
    latest_file = max(list_of_files, key=os.path.getctime)
    run_id = os.path.basename(latest_file).replace('.csv', '')
    
    df = pd.read_csv(latest_file)
    return df, run_id

st.title("📊 Abaco Portfolio Dashboard")

df, run_id = load_latest_metrics()

if df is None:
    st.warning("No metrics found. Please run the data pipeline first.")
    st.code("python scripts/run_data_pipeline.py")
else:
    st.caption(f"Displaying data from Run ID: `{run_id}`")

    # --- Top Level KPIs ---
    st.header("Key Performance Indicators")
    
    # We expect a single row for portfolio-level KPIs in this specific output format
    # If your pipeline outputs one row per loan, we would aggregate here.
    # Assuming the pipeline output is aggregated or we take the mean for the demo:
    
    col1, col2, col3 = st.columns(3)
    
    # Extract metrics (safely handling if columns exist)
    par_30 = df['par_30'].mean() if 'par_30' in df.columns else 0
    collection_rate = df['collection_rate'].mean() if 'collection_rate' in df.columns else 0
    health_score = df['portfolio_health_score'].mean() if 'portfolio_health_score' in df.columns else 0

    with col1:
        st.metric("PAR 30", f"{par_30:.2f}%", delta_color="inverse")
    with col2:
        st.metric("Collection Rate", f"{collection_rate:.2f}%")
    with col3:
        st.metric("Portfolio Health", f"{health_score:.1f}/10")

    # --- Data Preview ---
    st.divider()
    st.subheader("Pipeline Output Data")
    st.dataframe(df)

    # --- Visualizations ---
    if 'dpd_0_7_usd' in df.columns:
        st.subheader("DPD Distribution (USD)")
        
        # Melt the dataframe to long format for plotting if it's wide
        dpd_cols = [c for c in df.columns if 'dpd_' in c and '_usd' in c]
        if dpd_cols:
            # Summing in case of multiple rows
            dpd_data = df[dpd_cols].sum().reset_index()
            dpd_data.columns = ['Bucket', 'Amount (USD)']
            
            fig = px.bar(dpd_data, x='Bucket', y='Amount (USD)', title="Delinquency Buckets")
            st.plotly_chart(fig, use_container_width=True)
