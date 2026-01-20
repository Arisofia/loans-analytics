"""Streamlit dashboard for Abaco Loans Analytics - Engineering Excellence Edition."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import numpy as np
import streamlit as st

# Add repository root to sys.path to ensure correct module resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- Data Ingestion Simulation ---
@st.cache_data
def load_and_prepare_data():
    # In a real-world scenario, this would load data from a database or data warehouse.
    data = {
        'customer_id': range(100),
        'revenue': np.random.uniform(10000, 150000, 100),
        'balance': np.random.uniform(1000, 50000, 100),
        'limit': np.random.uniform(20000, 100000, 100),
        'dpd': np.random.choice([-1, 0, 15, 45, 75, 100], 100, p=[0.1, 0.6, 0.1, 0.1, 0.05, 0.05]),
    }
    data = {}
    for key, paths in candidates.items():
        path = next((p for p in paths if p.exists()), None)
        if path is None:
            continue
        df = pd.read_csv(path)
        data[key] = normalize_dataframe_complete(df)
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


def generate_kpi_exports(looker_data):
    required = ["loan_data", "customer_data", "historic_payment_data"]
    missing = [key for key in required if key not in looker_data]
    if missing:
        raise ValueError(f"Missing required Looker exports: {', '.join(missing)}")

    exports_dir = EXPORTS_DIR
    exports_dir.mkdir(parents=True, exist_ok=True)

    from src.analytics.kpi_catalog_processor import KPICatalogProcessor

    catalog_proc = KPICatalogProcessor(
        looker_data["loan_data"],
        looker_data["historic_payment_data"],
        looker_data["customer_data"],
        looker_data.get("schedule_data"),
    )

    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "extended_kpis": catalog_proc.get_all_kpis(),
    }

    try:
        figma_df = catalog_proc.get_figma_dashboard_df()
        figma_df.to_csv(exports_dir / "analytics_facts.csv", index=False)

        scorecard_df = catalog_proc.get_quarterly_scorecard()
        scorecard_df.to_csv(exports_dir / "quarterly_scorecard.csv", index=False)
        
        # Export Figma/Copilot payload
        slide_payload = catalog_proc.get_slide_payload()
        with open(exports_dir / "figma_slide_payload.json", "w") as f:
            json.dump(slide_payload, f, indent=2)
            
    except Exception as exc:
        logger.warning("Extended KPI generation failed: %s", exc)

    output_path = exports_dir / "complete_kpi_dashboard.json"
    output_path.write_text(json.dumps(dashboard, indent=2, default=str), encoding="utf-8")

    return output_path


def build_kpi_snapshot(dashboard, facts_df):
    metrics = {}
    latest_month = None

    if not facts_df.empty:
        facts_sorted = facts_df.sort_values("month") if "month" in facts_df.columns else facts_df
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
try:
    from tracing_setup import enable_auto_instrumentation, init_tracing

    init_tracing(service_name="abaco-dashboard")
    enable_auto_instrumentation()
except Exception:
    logger.warning("Tracing not initialized")

# Custom CSS
st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900&family=Poppins:wght@100;200;300;400;500;600;700&display=swap');
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
        ["Looker exports (auto)", "Manual upload"],
        index=0,
    )

    if data_source == "Looker exports (auto)":
        looker_data = load_looker_exports()
        if looker_data:
            st.session_state["data"] = looker_data
            st.session_state["loaded"] = True
            st.caption(f"Loaded Looker exports: {', '.join(looker_data.keys())}")
            if st.button("Generate KPI exports"):
                with st.spinner("Generating KPI exports from Looker data..."):
                    try:
                        output_path = generate_kpi_exports(looker_data)
                        st.cache_data.clear()
                        st.success(f"KPI exports generated: {output_path}")
                    except Exception as exc:
                        st.error(f"Failed to generate KPI exports: {exc}")
        else:
            st.session_state["loaded"] = False
            st.warning("No Looker exports found in data/archives/looker_exports.")
            st.caption("Upload Looker exports or switch to Manual upload.")
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
                # Map uploaded filenames to required internal keys
                mapped_dfs = {}
                for name, df in dfs.items():
                    name_lower = name.lower()
                    if isinstance(df, dict):
                        for sheet, sdf in df.items():
                            dfs[name][sheet] = normalize_dataframe_complete(sdf)
                    else:
                        normalized_df = normalize_dataframe_complete(df)
                        dfs[name] = normalized_df

                        # Apply fuzzy mapping to identify core tables
                        if ("loan" in name_lower and "data" in name_lower) or name_lower.startswith("loans"):
                            mapped_dfs["loan_data"] = normalized_df
                        elif ("customer" in name_lower and "data" in name_lower) or name_lower.startswith("customer"):
                            mapped_dfs["customer_data"] = normalized_df
                        elif ("payment" in name_lower and "historic" in name_lower) or ("real" in name_lower and "payment" in name_lower) or name_lower.startswith("transaction"):
                            mapped_dfs["historic_payment_data"] = normalized_df
                        elif "schedule" in name_lower:
                            mapped_dfs["schedule_data"] = normalized_df

                # Merge mapped data into session state while keeping original filenames for UI
                final_data = {**dfs, **mapped_dfs}
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
                    except Exception as exc:
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

data = st.session_state["data"]

# Core Tables Identification (prioritize internal keys from auto-mapping)
loan_data = data.get("loan_data")
customer_data = data.get("customer_data", pd.DataFrame())

if loan_data is None:
    # Fallback to original filename search if mapping failed
    for name, df in data.items():
        name_lower = name.lower()
        if ("loan" in name_lower and "data" in name_lower) or name_lower.startswith("loans"):
            loan_data = df
        elif ("customer" in name_lower and "data" in name_lower) or name_lower.startswith("customer"):
            if customer_data.empty:
                customer_data = df

if loan_data is None:
    st.error("Core loan data missing in uploads.")
    st.stop()

merged = loan_data.copy()
if not customer_data.empty and "loan_id" in merged.columns and "loan_id" in customer_data.columns:
    merged = merged.merge(customer_data, on="loan_id", how="left", suffixes=("", "_cust"))

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

# 9. Export & Figma Prep
st.header("📤 Export & Figma Prep")
exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    st.subheader("Data Artifacts")
    if not analytics_facts.empty:
        st.success("✅ Flattened fact tables ready.")
        st.download_button(
            "Download Analytics Facts (CSV)",
            analytics_facts.to_csv(index=False).encode("utf-8"),
            "analytics_facts.csv",
            help="Full time-series of dimensions and metrics for BI tools."
        )
    else:
        st.warning("Generate KPI exports to create fact tables.")

    if EXPORTS_DIR.joinpath("quarterly_scorecard.csv").exists():
        scorecard_data = pd.read_csv(EXPORTS_DIR / "quarterly_scorecard.csv")
        st.download_button(
            "Download Quarterly Scorecard",
            scorecard_data.to_csv(index=False).encode("utf-8"),
            "quarterly_scorecard.csv"
        )

with exp_col2:
    st.subheader("Figma Sync")
    st.write("Push calculated metrics to the [Commercial Analytics Figma](https://www.figma.com/make/nuVKwuPuLS7VmLFvqzOX1G/abaco-commercial-analytics)")
    
    if st.button("🚀 Sync to Figma Slides", use_container_width=True):
        payload_path = EXPORTS_DIR / "figma_slide_payload.json"
        if payload_path.exists():
            with open(payload_path, "r") as f:
                payload = json.load(f)
            
            st.json(payload)
            st.info("💡 **Tip:** If you see an 'Unsupported provider' error in Figma, it means Figma AI (Make) is not enabled for your account. You can manually paste the JSON payload above into your Figma design or use the 'Abaco Sync' plugin if installed.")
            st.success("Figma payload prepared and validated.")
        else:
            st.error("Please 'Generate KPI exports' in the sidebar first.")

st.divider()
st.caption(
    f"Abaco Intelligence Platform | System Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
st.markdown('</div>', unsafe_allow_html=True)
