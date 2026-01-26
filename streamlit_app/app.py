"""Streamlit dashboard for Abaco Loans Analytics - Engineering Excellence Edition."""

import json
import logging
import os
import sys
from datetime import datetime
import pandas as pd
import streamlit as st
from typing import Optional
from pathlib import Path

# 1. Robust Bootstrap Import
try:
    from streamlit_app.bootstrap import bootstrap_repo_root
    bootstrap_repo_root()
except ImportError:
    pass

# Add repository root to sys.path to ensure correct module resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 2. Local Imports (now safe after bootstrap)
from src.tracing_setup import initialize_tracing  # Example, adjust as needed
from src.analytics.kpi_catalog_processor import KPICatalogProcessor
from src.config.paths import Paths
from src.theme import ABACO_THEME
from src.utils.dashboard_utils import format_kpi_value, kpi_label
from src.utils.data_normalization import normalize_dataframe_complete
from streamlit_app.components.analytics_tabs import render_advanced_intelligence
from streamlit_app.components.charts import (
    render_cashflow_trends,
    render_category_breakdown,
    render_growth_analysis,
)
from streamlit_app.components.kpi_metrics import (
    render_kpi_snapshot,
    render_executive_summary,
)
from streamlit_app.components.sales_risk import (
    render_risk_analysis,
    render_sales_performance,
)
from src.pipeline.ingestion import load_raw_data_exports

LOCAL_EXPORTS_DIR = "local_exports"
EXPORTS_DIR = Paths.exports_dir()
SUPPORT_DIR = Paths.data_dir() / "support"


def get_table_type_from_filename(filename: str) -> Optional[str]:
    base_name = filename.lower()
    if "loan" in base_name:
        return "loan_data"
    elif "customer" in base_name:
        return "customer_data"
    return None

def load_local_exports() -> dict:
    export_data = {}
    if os.path.exists(LOCAL_EXPORTS_DIR):
        for f in os.listdir(LOCAL_EXPORTS_DIR):
            if f.endswith(".csv"):
                key = get_table_type_from_filename(f)
                if key:
                    try:
                        file_path = os.path.join(LOCAL_EXPORTS_DIR, f)
                        df = pd.read_csv(file_path)
                        export_data[key] = df
                    except Exception as e:
                        st.error(f"Error loading local file {f}: {e}")
    return export_data

def handle_file_uploads() -> dict[str, pd.DataFrame]:
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV Exports", 
        type="csv", 
        accept_multiple_files=True
    )

    upload_data = {}
    if uploaded_files:
        for uploaded_file in uploaded_files:
            key = get_table_type_from_filename(uploaded_file.name)
            if key:
                try:
                    upload_data[key] = pd.read_csv(uploaded_file)
                    st.sidebar.success(f"Mapped '{uploaded_file.name}' to {key}")
                except Exception as e:
                    st.sidebar.error(f"Error reading {uploaded_file.name}: {e}")
            else:
                st.sidebar.warning(f"Could not map file '{uploaded_file.name}' to known data types.")
        
    return upload_data

def get_normalized_table_type(filename: str) -> Optional[str]:
    base_name = filename.lower()
    if "loan" in base_name:
        return "loan_data"
    elif "customer" in base_name:
        return "customer_data"
    elif "payment" in base_name:
        return "historic_payment_data"
    elif "schedule" in base_name:
        return "schedule_data"
    return None

def fuzzy_map_core_tables(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    mapped_dfs = {}
    for name, df in dfs.items():
        name_lower = name.lower()
        table_key = get_normalized_table_type(name_lower)
        if table_key and table_key not in mapped_dfs: # Prioritize first match
            mapped_dfs[table_key] = df
    return mapped_dfs


# Initialize tracing
logger = logging.getLogger(__name__)
try:
    from src.tracing_setup import enable_auto_instrumentation, init_tracing
    init_tracing()
    enable_auto_instrumentation()
except ImportError:
    logger.warning("Tracing setup not found, proceeding without it.")
except Exception as e:
    logger.error(f"Error initializing tracing: {e}")

FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900"
    "&family=Poppins:wght@100;200;300;400;500;600;700&display=swap"
)

# Custom CSS
st.markdown(
    f"""
<style>
    @import url("{FONT_IMPORT_URL}");
    .main {{
        background-color: {ABACO_THEME['colors']['background']};
        color: {ABACO_THEME['colors']['white']};
        font-family: '{ABACO_THEME['typography']['primary_font']}', sans-serif;
    }}
    .stMetric {{
        background: {ABACO_THEME['gradients']['card_primary']};
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {ABACO_THEME['colors']['purple_dark']};
    }}
</style>
""",
    unsafe_allow_html=True,
)

# --- Ingestion Section ---
if "loaded" not in st.session_state:
    st.session_state["loaded"] = False

with st.sidebar:
    st.title("Data Ingestion")
    data_source = st.radio(
        "Data Source",
        ["Local artifacts (auto)", "Manual upload"],
        index=0,
    )

    if data_source == "Local artifacts (auto)":
        _data = load_local_exports()
        if _data:
            st.session_state["data"] = _data
            st.session_state["loaded"] = True
            st.caption(f"Loaded artifacts: {', '.join(_data.keys())}")
            if st.button("Generate KPI exports"):
                with st.spinner("Generating KPI exports from artifacts..."):
                    try:
                        output_path = generate_kpi_exports(_data)
                        st.cache_data.clear()
                        st.success(f"KPI exports generated: {output_path}")
                    except (ValueError, OSError) as exc:
                        st.error(f"Failed to generate KPI exports: {exc}")
        else:
            st.session_state["loaded"] = False
            st.warning("No data artifacts found in data/raw.")
            st.caption("Upload data or switch to Manual upload.")
    else:
        uploaded_files = st.file_uploader(
            "Upload Loan Tape CSVs and Financial XLSX",
            accept_multiple_files=True,
            type=["csv", "xlsx"],
        )

        if st.button("Ingest Data") or uploaded_files:
            dfs = {}
            for file in uploaded_files:
                if file.name.endswith(".csv"):
                    dfs[file.name] = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    dfs[file.name] = pd.read_excel(file, sheet_name=None)

            if dfs:
                # Normalize all dataframes
                for name, df in dfs.items():
                    if isinstance(df, dict):
                        for sheet, sdf in df.items():
                            dfs[name][sheet] = normalize_dataframe_complete(sdf)
                    else:
                        dfs[name] = normalize_dataframe_complete(df)

                # Use shared fuzzy mapping helper
                mapped_dfs = fuzzy_map_core_tables(dfs)
                final_data = {**dfs, **mapped_dfs}
                st.session_state["data"] = final_data
                st.session_state["loaded"] = True
                st.success("Data ingested successfully.")

                # Auto-generate KPI exports from mapped data
                with st.spinner("Generating KPI exports from uploaded data..."):
                    try:
                        output_path = generate_kpi_exports(final_data)
                        st.cache_data.clear()
                        st.success("\u2705 KPI exports generated and UI updated!")
                        st.rerun()
                    except Exception as exc:
                        st.warning(f"\u26a0\ufe0f KPI auto-generation skipped: {exc}")

    if st.button("Clear Data"):
        st.session_state["loaded"] = False
        st.session_state.pop("data", None)
        st.rerun()

    st.divider()
    target_outstanding = st.number_input("Target Outstanding", value=8360500.0)
    target_loans = st.number_input("Target Loans", value=1000)
    st.session_state["target_outstanding"] = target_outstanding
    st.session_state["target_loans"] = target_loans

# --- Main Dashboard ---
st.title("💰 ABACO Financial Intelligence")

@st.cache_data(show_spinner=False)
def load_analytics_facts():
    # Placeholder for actual analytics facts loading
    return pd.DataFrame()

dashboard_metrics = load_kpi_dashboard()
analytics_facts = load_analytics_facts()
kpi_snapshot, snapshot_month = build_kpi_snapshot(dashboard_metrics, analytics_facts)

# 1. KPI Snapshot
render_kpi_snapshot(kpi_snapshot, snapshot_month)

# 2. Cashflow Trends
render_cashflow_trends(analytics_facts)

if not st.session_state["loaded"]:
    st.info("Upload data files in the sidebar to unlock loan-level diagnostics.")
    st.stop()

session_data = st.session_state["data"]


# Core Tables Identification (prioritize internal keys from auto-mapping)
loan_data = session_data.get("loan_data")
customer_data = session_data.get("customer_data", pd.DataFrame())

if loan_data is None:
    # Fallback: use fuzzy mapping helper on all data
    mapped = fuzzy_map_core_tables(session_data) # Use session_data here
    loan_data = mapped.get("loan_data")
    if customer_data.empty:
        customer_data = mapped.get("customer_data", pd.DataFrame())

if loan_data is None:
    st.error("Core loan data missing in uploads.")
    st.stop()

merged = loan_data.copy()
if (
    not customer_data.empty
    and "loan_id" in merged.columns
    and "loan_id" in customer_data.columns
):
    merged = merged.merge(
        customer_data,
        on="loan_id",
        how="left",
        suffixes=("", "_cust"),
    )

# 3. Executive Summary
total_outstanding = render_executive_summary(merged)

# 4. Growth Analysis & Category Breakdown
g_col2 = render_growth_analysis(total_outstanding)
render_category_breakdown(merged, g_col2)

# 5. Sales Performance
render_sales_performance(merged, load_agent_headcount)

# 6. Risk Analysis
render_risk_analysis(merged)

# 7. Advanced Intelligence
render_advanced_intelligence(dashboard_metrics)

# 8. KPI Catalog
st.header("📋 KPI Catalog")
with st.expander("View all computed KPIs"):
    all_kpis = dashboard_metrics.get("extended_kpis", {})
    if all_kpis:
        # Flatten simple key-value pairs
        flat_kpis = []
        for k, v in all_kpis.items():
            if isinstance(v, (int, float, str)):
                flat_kpis.append(
                    {"KPI": kpi_label(k), "Value": format_kpi_value(k, v)}
                )

        if flat_kpis:
            st.table(pd.DataFrame(flat_kpis))

        st.write("**Detailed Data Tables:**")
        table_keys = [
            k for k, v in all_kpis.items() if isinstance(v, list) and v
        ]
        selected_table = st.selectbox("Select table to view", table_keys)
        if selected_table:
            st.dataframe(pd.DataFrame(all_kpis[selected_table]))
    else:
        st.info("No extended KPIs found.")

st.divider()
st.caption(
    "Abaco Intelligence Platform | System Date: "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
st.markdown("</div>", unsafe_allow_html=True)