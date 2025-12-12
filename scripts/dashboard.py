import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Abaco Loans Analytics", layout="wide")

LOGS_DIR = Path("logs/runs")
METRICS_DIR = Path("data/metrics")


def _latest_manifest() -> Path | None:
    manifests = list(LOGS_DIR.glob("*_manifest.json"))
    if not manifests:
        return None
    return max(manifests, key=os.path.getctime)


def load_latest_run():
    """Load latest KPI manifest and associated CSV metrics."""
    manifest_path = _latest_manifest()
    if not manifest_path or not manifest_path.exists():
        return None, None, None

    with manifest_path.open() as f:
        manifest = json.load(f)

    run_id = manifest.get("run_id", "unknown")
    metrics_file = manifest.get("csv_file")
    kpis = manifest.get("kpis", {})

    df = None
    if metrics_file and Path(metrics_file).exists():
        df = pd.read_csv(metrics_file)
    elif metrics_file:
        # fallback to locate by filename in metrics dir
        fallback = METRICS_DIR / Path(metrics_file).name
        if fallback.exists():
            df = pd.read_csv(fallback)

    return df, run_id, kpis


st.title("\ud83d\udcca Abaco Portfolio Dashboard")

df, run_id, kpis = load_latest_run()

if df is None:
    st.warning("No metrics found. Please run the data pipeline first.")
    st.code("python scripts/run_data_pipeline.py")
else:
    st.caption(f"Displaying data from Run ID: `{run_id}`")

    # --- Top Level KPIs ---
    st.header("Key Performance Indicators")

    col1, col2, col3 = st.columns(3)

    par_30_val = kpis.get("par_30", {}).get("value", 0) if isinstance(kpis, dict) else 0
    collection_rate_val = kpis.get("collection_rate", {}).get("value", 0) if isinstance(kpis, dict) else 0
    health_score_val = kpis.get("health_score", {}).get("value", 0) if isinstance(kpis, dict) else 0

    with col1:
        st.metric("PAR 30", f"{par_30_val:.2f}%", delta_color="inverse")
    with col2:
        st.metric("Collection Rate", f"{collection_rate_val:.2f}%")
    with col3:
        st.metric("Portfolio Health", f"{health_score_val:.1f}/10")

    # --- Data Preview ---
    st.divider()
    st.subheader("Pipeline Output Data")
    st.dataframe(df)

    # --- Visualizations ---
    if "dpd_0_7_usd" in df.columns:
        st.subheader("DPD Distribution (USD)")
        dpd_cols = [c for c in df.columns if c.startswith("dpd_") and c.endswith("_usd")]
        if dpd_cols:
            dpd_data = df[dpd_cols].sum().reset_index()
            dpd_data.columns = ["Bucket", "Amount (USD)"]
            fig = px.bar(dpd_data, x="Bucket", y="Amount (USD)", title="Delinquency Buckets")
            st.plotly_chart(fig, use_container_width=True)
