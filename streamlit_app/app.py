"""Streamlit dashboard for Abaco Loans Analytics - Engineering Excellence Edition."""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from components.analytics_tabs import render_advanced_intelligence
from components.charts import (
    render_cashflow_trends,
    render_category_breakdown,
    render_growth_analysis,
)
from components.kpi_metrics import render_executive_summary, render_kpi_snapshot
from components.sales_risk import render_risk_analysis, render_sales_performance
from data_normalization import normalize_dataframe_complete
from dashboard_utils import format_kpi_value, kpi_label
from kpi_catalog_processor import KPICatalogProcessor
from theme import ABACO_THEME
from tracing_setup import enable_auto_instrumentation, init_tracing

ROOT_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = ROOT_DIR / "exports"
SUPPORT_DIR = ROOT_DIR / "data" / "support"
LOOKER_DIR = ROOT_DIR / "data" / "raw" / "_exports"


@st.cache_data(show_spinner=False)
def load_raw_data_exports():
    candidates = {
        "loan_data": [
            LOOKER_DIR / "loan_data.csv",
            LOOKER_DIR / "Abaco-Loan-Tape_Loan-Data_Table-6.csv",
            ROOT_DIR / "data" / "abaco" / "loan_data.csv",
        ],
        "customer_data": [
            LOOKER_DIR / "customer_data.csv",
            LOOKER_DIR / "Abaco-Loan-Tape_Customer-Data_Table-6.csv",
            ROOT_DIR / "data" / "abaco" / "customer_data.csv",
        ],
        "historic_payment_data": [
            LOOKER_DIR / "historic_payment_data.csv",
            LOOKER_DIR / "Abaco-Loan-Tape_Historic-Real-Payment_Table-6.csv",
            ROOT_DIR / "data" / "abaco" / "real_payment.csv",
        ],
        "schedule_data": [
            LOOKER_DIR / "schedules.csv",
            LOOKER_DIR / "payment_schedule.csv",
            LOOKER_DIR / "Abaco-Loan-Tape_Payment Schedule_Table-6.csv",
            ROOT_DIR / "data" / "abaco" / "payment_schedule.csv",
        ],
    }
    data = {}
    for key, paths in candidates.items():
        path = next((p for p in paths if p.exists()), None)
        if path is None:
            continue
        data_frame = pd.read_csv(path)
        data[key] = normalize_dataframe_complete(data_frame)
    return data


@st.cache_data(show_spinner=False, ttl=300)
def load_analytics_facts():
    facts_path = EXPORTS_DIR / "analytics_facts.csv"
    if not facts_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(facts_path)
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce")
    return df


@st.cache_data(show_spinner=False, ttl=300)
def load_kpi_dashboard():
    dashboard_path = EXPORTS_DIR / "complete_kpi_dashboard.json"
    if not dashboard_path.exists():
        return {}
    return json.loads(dashboard_path.read_text())


def generate_kpi_exports(raw_data):
    required = ["loan_data", "customer_data", "historic_payment_data"]
    missing = [key for key in required if key not in raw_data]
    if missing:
        raise ValueError(f"Missing required  exports: {', '.join(missing)}")

    exports_dir = EXPORTS_DIR
    exports_dir.mkdir(parents=True, exist_ok=True)

    catalog_proc = KPICatalogProcessor(
        raw_data["loan_data"],
        raw_data["historic_payment_data"],
        raw_data["customer_data"],
        raw_data.get("schedule_data"),
    )

    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "extended_kpis": catalog_proc.get_all_kpis(),
    }

    try:
        scorecard_df = catalog_proc.get_quarterly_scorecard()
        scorecard_df.to_csv(exports_dir / "quarterly_scorecard.csv", index=False)
    except (ValueError, OSError) as exc:
        logger.warning("Extended KPI generation failed: %s", exc)

    dashboard_path = exports_dir / "complete_kpi_dashboard.json"
    dashboard_path.write_text(
        json.dumps(dashboard, indent=2, default=str), encoding="utf-8"
    )

    return dashboard_path


def build_kpi_snapshot(dashboard, facts_df):
    metrics = {}
    latest_month = None

    if not facts_df.empty:
        if "month" in facts_df.columns:
            facts_sorted = facts_df.sort_values("month")
        else:
            facts_sorted = facts_df
        latest = facts_sorted.iloc[-1]
        latest_month = latest.get("month")
        for col in facts_sorted.columns:
            if col == "month":
                continue
            metrics[col] = latest[col]

    if dashboard:
        for key, value in dashboard.items():
            if key == "timestamp":
                continue
            if isinstance(value, (int, float)):
                metrics.setdefault(key, value)

        exec_strip = dashboard.get("extended_kpis", {}).get("executive_strip", {})
        for key, value in exec_strip.items():
            metrics.setdefault(key, value)

    return metrics, latest_month


@st.cache_data(show_spinner=False)
def load_agent_headcount():
    headcount_path = SUPPORT_DIR / "headcount.csv"
    if not headcount_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(headcount_path)
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce")
    return df


# Initialize tracing
logger = logging.getLogger(__name__)
init_tracing(service_name="abaco-dashboard")
enable_auto_instrumentation()

FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900"
    "&family=Poppins:wght@100;200;300;400;500;600;700&display=swap"
)

# Custom CSS
st.markdown(
    f"""
<style>
    @import url('{FONT_IMPORT_URL}');
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
        raw_data = load_raw_data_exports()
        if raw_data:
            st.session_state["data"] = raw_data
            st.session_state["loaded"] = True
            st.caption(f"Loaded artifacts: {', '.join(raw_data.keys())}")
            if st.button("Generate KPI exports"):
                with st.spinner("Generating KPI exports from artifacts..."):
                    try:
                        output_path = generate_kpi_exports(raw_data)
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
            uploaded_data = {}
            for file in uploaded_files:
                if file.name.endswith(".csv"):
                    uploaded_data[file.name] = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    uploaded_data[file.name] = pd.read_excel(file, sheet_name=None)

            if uploaded_data:
                # Map uploaded filenames to required internal keys
                mapped_dfs = {}
                for name, uploaded_frame in uploaded_data.items():
                    name_lower = name.lower()
                    if isinstance(uploaded_frame, dict):
                        for sheet, sheet_frame in uploaded_frame.items():
                            uploaded_data[name][sheet] = normalize_dataframe_complete(
                                sheet_frame
                            )
                    else:
                        normalized_df = normalize_dataframe_complete(uploaded_frame)
                        uploaded_data[name] = normalized_df

                        # Apply fuzzy mapping to identify core tables
                        if (
                            ("loan" in name_lower and "data" in name_lower)
                            or name_lower.startswith("loans")
                        ):
                            mapped_dfs["loan_data"] = normalized_df
                        elif (
                            "customer" in name_lower and "data" in name_lower
                        ) or name_lower.startswith("customer"):
                            mapped_dfs["customer_data"] = normalized_df
                        elif (
                            ("payment" in name_lower and "historic" in name_lower)
                            or ("real" in name_lower and "payment" in name_lower)
                            or name_lower.startswith("transaction")
                        ):
                            mapped_dfs["historic_payment_data"] = normalized_df
                        elif "schedule" in name_lower:
                            mapped_dfs["schedule_data"] = normalized_df

                # Merge mapped data into session state while keeping filenames for UI
                final_data = {**uploaded_data, **mapped_dfs}
                st.session_state["data"] = final_data
                st.session_state["loaded"] = True
                st.success("Data ingested successfully.")

                # Auto-generate KPI exports from mapped data
                with st.spinner("Generating KPI exports from uploaded data..."):
                    try:
                        output_path = generate_kpi_exports(final_data)
                        st.cache_data.clear()
                        st.success("✅ KPI exports generated and UI updated!")
                        st.rerun()
                    except (ValueError, OSError) as exc:
                        st.warning(f"⚠️ KPI auto-generation skipped: {exc}")

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
    # Fallback to original filename search if mapping failed
    for name, data_frame in session_data.items():
        name_lower = name.lower()
        if ("loan" in name_lower and "data" in name_lower) or name_lower.startswith(
            "loans"
        ):
            loan_data = data_frame
        elif (
            ("customer" in name_lower and "data" in name_lower)
            or name_lower.startswith("customer")
        ):
            if customer_data.empty:
                customer_data = data_frame

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
                flat_kpis.append({"KPI": kpi_label(k), "Value": format_kpi_value(k, v)})

        if flat_kpis:
            st.table(pd.DataFrame(flat_kpis))

        st.write("**Detailed Data Tables:**")
        table_keys = [k for k, v in all_kpis.items() if isinstance(v, list) and v]
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
