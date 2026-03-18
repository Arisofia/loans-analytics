"""Usage metrics dashboard for Abaco Loans Analytics."""

from pathlib import Path

import pandas as pd
import streamlit as st

from backend.python.config.theme import ABACO_THEME
from backend.python.utils.usage_tracker import UsageTracker

ROOT_DIR = Path.cwd()

st.set_page_config(page_title="Usage Metrics - Abaco", layout="wide")

st.markdown(
    f"""
    <style>
    .main {{
        background-color: {ABACO_THEME['colors']['background']};
        color: {ABACO_THEME['colors']['white']};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Usage Metrics Tracking")

tracker = UsageTracker()
events = tracker.get_events()

if not events:
    st.info("No usage events recorded yet.")
else:
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame([e.to_dict() for e in events])

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Events", len(df))
    with col2:
        st.metric("Unique Features", df["feature_name"].nunique())
    with col3:
        st.metric("Unique Actions", df["action"].nunique())

    st.subheader("Event Log")
    st.dataframe(df.sort_values(by="timestamp", ascending=False), width="stretch")

    st.subheader("Feature Usage Breakdown")
    feature_counts = df["feature_name"].value_counts().reset_index()
    feature_counts.columns = ["Feature", "Count"]
    st.bar_chart(feature_counts.set_index("Feature"))

    st.subheader("Export Metrics")
    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        if st.button("Export to JSON"):
            output_path = ROOT_DIR / "exports" / "usage_metrics.json"
            tracker.export(output_path, export_format="json")
            st.success(f"Exported to {output_path}")

    with export_col2:
        if st.button("Export to CSV"):
            output_path = ROOT_DIR / "exports" / "usage_metrics.csv"
            tracker.export(output_path, export_format="csv")
            st.success(f"Exported to {output_path}")

    with export_col3:
        if st.button("Export to Parquet"):
            output_path = ROOT_DIR / "exports" / "usage_metrics.parquet"
            tracker.export(output_path, export_format="parquet")
            st.success(f"Exported to {output_path}")

# Track visit to this page
if "tracked_metrics_visit" not in st.session_state:
    tracker.track("usage_metrics_page", "view")
    st.session_state["tracked_metrics_visit"] = True
