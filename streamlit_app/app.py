"""Streamlit dashboard for Abaco Loans Analytics - Engineering Excellence Edition."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from dashboard_utils import format_kpi_value, kpi_label  # noqa: E402
from data_normalization import normalize_dataframe_complete  # noqa: E402
from kpi_catalog_processor import KPICatalogProcessor  # noqa: E402
from streamlit_app.components.analytics_tabs import render_advanced_intelligence  # noqa: E402
from streamlit_app.components.charts import (  # noqa: E402
    render_cashflow_trends,
    render_category_breakdown,
    render_growth_analysis,
)
from streamlit_app.components.kpi_metrics import (  # noqa: E402
    render_executive_summary,
    render_kpi_snapshot,
)
from streamlit_app.components.sales_risk import (  # noqa: E402
    render_risk_analysis,
    render_sales_performance,
)
from theme import ABACO_THEME  # noqa: E402
from tracing_setup import enable_auto_instrumentation  # noqa: E402
from tracing_setup import init_tracing

LOCAL_EXPORTS_DIR = ROOT_DIR / "local_exports"
EXPORTS_DIR_CANDIDATES = [
    ROOT_DIR / "exports",
    ROOT_DIR / "data" / "archives" / "_exports",
]
SUPPORT_DIR = ROOT_DIR / "data" / "support"
logger = logging.getLogger(__name__)
try:
    init_tracing("streamlit-dashboard")
    enable_auto_instrumentation()
except ImportError:
    logger.warning("Tracing setup not found, proceeding without it.")
except Exception as exc:
    logger.error("Error initializing tracing: %s", exc)


def resolve_exports_dir(create: bool = False) -> Path:
    for candidate in EXPORTS_DIR_CANDIDATES:
        if candidate.exists():
            return candidate
    default_dir = EXPORTS_DIR_CANDIDATES[0]
    if create:
        default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir


def get_table_type_from_filename(filename: str) -> Optional[str]:
    base_name = filename.lower()
    if "loan" in base_name:
        return "loan_data"
    if "customer" in base_name:
        return "customer_data"
    return None


def load_local_exports() -> dict[str, pd.DataFrame]:
    export_data: dict[str, pd.DataFrame] = {}
    if LOCAL_EXPORTS_DIR.exists():
        for file_path in LOCAL_EXPORTS_DIR.iterdir():
            if file_path.suffix.lower() == ".csv":
                key = get_table_type_from_filename(file_path.name)
                if key:
                    try:
                        export_data[key] = pd.read_csv(file_path)
                    except Exception as exc:
                        st.error(f"Error loading local file {file_path.name}: {exc}")
    return export_data


def handle_file_uploads() -> dict[str, pd.DataFrame]:
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV Exports",
        type="csv",
        accept_multiple_files=True,
    )
    upload_data: dict[str, pd.DataFrame] = {}
    if uploaded_files:
        for uploaded_file in uploaded_files:
            key = get_table_type_from_filename(uploaded_file.name)
            if key:
                try:
                    upload_data[key] = pd.read_csv(uploaded_file)
                    st.sidebar.success(f"Mapped '{uploaded_file.name}' to {key}")
                except Exception as exc:
                    st.sidebar.error(f"Error reading {uploaded_file.name}: {exc}")
            else:
                st.sidebar.warning(
                    f"Could not map file '{uploaded_file.name}' to known data types."
                )
    return upload_data


def get_normalized_table_type(filename: str) -> Optional[str]:
    base_name = filename.lower()
    if "loan" in base_name:
        return "loan_data"
    if "customer" in base_name:
        return "customer_data"
    if "payment" in base_name:
        return "historic_payment_data"
    if "schedule" in base_name:
        return "schedule_data"
    return None


def fuzzy_map_core_tables(
    dfs: dict[str, pd.DataFrame | dict[str, pd.DataFrame]],
) -> dict[str, pd.DataFrame]:
    mapped_dfs: dict[str, pd.DataFrame] = {}
    for name, df in dfs.items():
        if isinstance(df, dict):
            for sheet_name, sheet_df in df.items():
                table_key = get_normalized_table_type(sheet_name)
                if table_key and table_key not in mapped_dfs:
                    mapped_dfs[table_key] = sheet_df
        else:
            name_lower = name.lower()
            table_key = get_normalized_table_type(name_lower)
            if table_key and table_key not in mapped_dfs:  # Prioritize first match
                mapped_dfs[table_key] = df
    return mapped_dfs


def load_kpi_dashboard() -> dict:
    export_dirs = EXPORTS_DIR_CANDIDATES
    for export_dir in export_dirs:
        dashboard_path = export_dir / "complete_kpi_dashboard.json"
        if dashboard_path.exists():
            try:
                return json.loads(dashboard_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Failed to parse KPI dashboard export %s: %s",
                    dashboard_path,
                    exc,
                )
    return {}


@st.cache_data(show_spinner=False)
def load_analytics_facts() -> pd.DataFrame:
    for export_dir in EXPORTS_DIR_CANDIDATES:
        facts_path = export_dir / "analytics_facts.csv"
        if facts_path.exists():
            try:
                return pd.read_csv(facts_path)
            except Exception as exc:
                logger.warning("Failed to load analytics facts: %s", exc)
    return pd.DataFrame()


def build_kpi_snapshot(
    dashboard_metrics: dict, analytics_facts: pd.DataFrame
) -> tuple[dict[str, float], Optional[pd.Timestamp]]:
    snapshot: dict[str, float] = {}
    snapshot_month: Optional[pd.Timestamp] = None
    if not analytics_facts.empty:
        for column in ("month", "month_end", "date"):
            if column in analytics_facts.columns:
                parsed = pd.to_datetime(analytics_facts[column], errors="coerce").dropna()
                if not parsed.empty:
                    snapshot_month = parsed.max()
                    break
    extended_kpis = dashboard_metrics.get("extended_kpis", {})
    executive_strip = extended_kpis.get("executive_strip", {})
    for key, value in executive_strip.items():
        if isinstance(value, (int, float)):
            snapshot[key] = float(value)
    root_keys = (
        "total_aum_usd",
        "active_clients",
        "monthly_revenue_usd",
        "revenue_per_active_client_monthly",
        "mom_growth_pct",
        "yoy_growth_pct",
        "par_90_ratio_pct",
        "delinquency_rate_30_pct",
    )
    for key in root_keys:
        value = dashboard_metrics.get(key)
        if isinstance(value, (int, float)):
            snapshot.setdefault(key, float(value))
    return snapshot, snapshot_month


def load_agent_headcount() -> pd.DataFrame:
    headcount_path = SUPPORT_DIR / "headcount.csv"
    if not headcount_path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(headcount_path)
    except Exception as exc:
        logger.warning("Unable to load headcount data: %s", exc)
    return pd.DataFrame()


def generate_kpi_exports(
    data: dict[str, pd.DataFrame],
    *,
    normalize_inputs: bool = True,
) -> Path:
    exports_dir = resolve_exports_dir(create=True)
    mapped_tables = fuzzy_map_core_tables(data)
    loans_df = mapped_tables.get("loan_data", data.get("loan_data", pd.DataFrame()))
    customers_df = mapped_tables.get("customer_data", data.get("customer_data", pd.DataFrame()))
    payments_df = mapped_tables.get(
        "historic_payment_data",
        data.get("historic_payment_data", pd.DataFrame()),
    )
    schedule_df = mapped_tables.get("schedule_data", data.get("schedule_data"))
    if normalize_inputs:
        normalized_loans = (
            normalize_dataframe_complete(loans_df) if not loans_df.empty else pd.DataFrame()
        )
        normalized_customers = (
            normalize_dataframe_complete(customers_df) if not customers_df.empty else pd.DataFrame()
        )
        normalized_payments = (
            normalize_dataframe_complete(payments_df) if not payments_df.empty else pd.DataFrame()
        )
        normalized_schedule = (
            normalize_dataframe_complete(schedule_df)
            if isinstance(schedule_df, pd.DataFrame) and not schedule_df.empty
            else pd.DataFrame()
        )
    else:
        normalized_loans = loans_df if not loans_df.empty else pd.DataFrame()
        normalized_customers = customers_df if not customers_df.empty else pd.DataFrame()
        normalized_payments = payments_df if not payments_df.empty else pd.DataFrame()
        normalized_schedule = (
            schedule_df
            if isinstance(schedule_df, pd.DataFrame) and not schedule_df.empty
            else pd.DataFrame()
        )
    processor = KPICatalogProcessor(
        normalized_loans,
        normalized_payments,
        normalized_customers,
        normalized_schedule,
    )
    extended_kpis = processor.get_all_kpis()
    executive_strip = extended_kpis.get("executive_strip", {})
    dashboard_metrics = {
        "timestamp": datetime.now().isoformat(),
        "extended_kpis": extended_kpis,
        "total_aum_usd": executive_strip.get("total_outstanding_loan_value", 0.0),
        "active_clients": executive_strip.get("total_customers", 0),
        "total_loans": executive_strip.get("total_loans", 0),
        "avg_apr": executive_strip.get("avg_apr", 0.0),
    }
    dashboard_path = exports_dir / "complete_kpi_dashboard.json"
    dashboard_path.write_text(
        json.dumps(dashboard_metrics, indent=2, default=str),
        encoding="utf-8",
    )
    analytics_facts = processor.get_figma_dashboard_df()
    if not analytics_facts.empty:
        facts_path = exports_dir / "analytics_facts.csv"
        analytics_facts.to_csv(facts_path, index=False)
    return dashboard_path


FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900"
    "&family=Poppins:wght@100;200;300;400;500;600;700&display=swap"
)
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
            st.warning("No data artifacts found in local_exports.")
            st.caption("Upload data or switch to Manual upload.")
    else:
        uploaded_files = st.file_uploader(
            "Upload Loan Tape CSVs and Financial XLSX",
            accept_multiple_files=True,
            type=["csv", "xlsx"],
        )
        if st.button("Ingest Data") or uploaded_files:
            dfs: dict[str, pd.DataFrame | dict[str, pd.DataFrame]] = {}
            for file in uploaded_files:
                if file.name.endswith(".csv"):
                    dfs[file.name] = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    dfs[file.name] = pd.read_excel(file, sheet_name=None)
            if dfs:
                for name, df in dfs.items():
                    if isinstance(df, dict):
                        for sheet, sheet_df in df.items():
                            df[sheet] = normalize_dataframe_complete(sheet_df)
                    else:
                        dfs[name] = normalize_dataframe_complete(df)
                mapped_dfs = fuzzy_map_core_tables(dfs)
                final_data = {**dfs, **mapped_dfs}
                st.session_state["data"] = final_data
                st.session_state["loaded"] = True
                st.success("Data ingested successfully.")
                with st.spinner("Generating KPI exports from uploaded data..."):
                    try:
                        output_path = generate_kpi_exports(
                            final_data,
                            normalize_inputs=False,
                        )
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
st.title("💰 ABACO Financial Intelligence")
dashboard_metrics = load_kpi_dashboard()
analytics_facts = load_analytics_facts()
if not dashboard_metrics and analytics_facts.empty:
    st.warning(
        "No KPI exports detected. Generate KPI exports from the sidebar or add "
        "complete_kpi_dashboard.json and analytics_facts.csv to the exports "
        "directory."
    )
kpi_snapshot, snapshot_month = build_kpi_snapshot(dashboard_metrics, analytics_facts)
render_kpi_snapshot(kpi_snapshot, snapshot_month)
render_cashflow_trends(analytics_facts)
if not st.session_state["loaded"]:
    st.info("Upload data files in the sidebar to unlock loan-level diagnostics.")
    st.stop()
session_data = st.session_state["data"]
loan_data = session_data.get("loan_data")
customer_data = session_data.get("customer_data", pd.DataFrame())
if loan_data is None:
    mapped = fuzzy_map_core_tables(session_data)
    loan_data = mapped.get("loan_data")
    if customer_data.empty:
        customer_data = mapped.get("customer_data", pd.DataFrame())
if loan_data is None:
    st.error("Core loan data missing in uploads.")
    st.stop()
merged = loan_data.copy()
if not customer_data.empty and "loan_id" in merged.columns and "loan_id" in customer_data.columns:
    merged = merged.merge(
        customer_data,
        on="loan_id",
        how="left",
        suffixes=("", "_cust"),
    )
total_outstanding = render_executive_summary(merged)
g_col2 = render_growth_analysis(total_outstanding)
render_category_breakdown(merged, g_col2)
render_sales_performance(merged, load_agent_headcount)
render_risk_analysis(merged)
render_advanced_intelligence(dashboard_metrics)
st.header("📋 KPI Catalog")
with st.expander("View all computed KPIs"):
    all_kpis = dashboard_metrics.get("extended_kpis", {})
    if all_kpis:
        flat_kpis = []
        for key, value in all_kpis.items():
            if isinstance(value, (int, float, str)):
                flat_kpis.append({"KPI": kpi_label(key), "Value": format_kpi_value(key, value)})
        if flat_kpis:
            st.table(pd.DataFrame(flat_kpis))
        st.write("**Detailed Data Tables:**")
        table_keys = [key for key, value in all_kpis.items() if isinstance(value, list) and value]
        selected_table = st.selectbox("Select table to view", table_keys)
        if selected_table:
            st.dataframe(pd.DataFrame(all_kpis[selected_table]))
    else:
        st.info("No extended KPIs found.")
st.divider()
st.caption(
    "Abaco Intelligence Platform | System Date: " f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
