"""Streamlit dashboard for Abaco Loans Analytics - Engineering Excellence Edition."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from backend.python.config.theme import ABACO_THEME
from backend.python.config.tracing_setup import enable_auto_instrumentation, init_tracing
from backend.python.kpis.catalog_processor import KPICatalogProcessor
from backend.python.kpis.strategic_reporting import (
    build_strategic_summary,
    write_strategic_report,
)
from backend.python.utils.dashboard import format_kpi_value, kpi_label
from backend.python.utils.normalization import normalize_dataframe_complete
from backend.python.utils.usage_tracker import UsageTracker
from frontend.streamlit_app.components.analytics_tabs import render_advanced_intelligence
from frontend.streamlit_app.components.charts import (
    render_cashflow_trends,
    render_category_breakdown,
    render_growth_analysis,
)
from frontend.streamlit_app.components.kpi_metrics import (
    render_executive_summary,
    render_kpi_snapshot,
)
from frontend.streamlit_app.components.sales_risk import (
    render_risk_analysis,
    render_sales_performance,
)

# Use absolute paths relative to this file for robustness
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOCAL_EXPORTS_DIR = ROOT_DIR / "local_exports"
EXPORTS_DIR_CANDIDATES = [
    ROOT_DIR / "exports",
    ROOT_DIR / "data" / "archives" / "_exports",
]
SUPPORT_DIR = ROOT_DIR / "data" / "support"
logger = logging.getLogger(__name__)
init_tracing("streamlit-dashboard")
enable_auto_instrumentation()


# Initialize usage tracker
usage_tracker = UsageTracker()

# Track dashboard visit
if "tracked_visit" not in st.session_state:
    usage_tracker.track("dashboard", "visit")
    st.session_state["tracked_visit"] = True


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
        for local_exports_file_item in LOCAL_EXPORTS_DIR.iterdir():
            if local_exports_file_item.suffix.lower() == ".csv":
                export_file_map_key = get_table_type_from_filename(local_exports_file_item.name)
                if export_file_map_key:
                    try:
                        export_data[export_file_map_key] = pd.read_csv(local_exports_file_item)
                    except Exception as exc:
                        st.error(f"Error loading local file {local_exports_file_item.name}: {exc}")
    return export_data


def handle_file_uploads() -> dict[str, pd.DataFrame]:
    sidebar_uploaded_files_widget = st.sidebar.file_uploader(
        "Upload CSV Exports",
        type="csv",
        accept_multiple_files=True,
    )
    upload_data: dict[str, pd.DataFrame] = {}
    if sidebar_uploaded_files_widget:
        for uploaded_file_widget_item in sidebar_uploaded_files_widget:
            upload_widget_key = get_table_type_from_filename(uploaded_file_widget_item.name)
            if upload_widget_key:
                try:
                    upload_data[upload_widget_key] = pd.read_csv(uploaded_file_widget_item)
                    st.sidebar.success(
                        f"Mapped '{uploaded_file_widget_item.name}' to {upload_widget_key}"
                    )
                except Exception as exc:
                    st.sidebar.error(f"Error reading {uploaded_file_widget_item.name}: {exc}")
            else:
                st.sidebar.warning(
                    f"Could not map file '{uploaded_file_widget_item.name}' to known data types."
                )
    return upload_data


def get_normalized_table_type(filename: str) -> Optional[str]:
    normalized_file_name = filename.lower()
    if "loan" in normalized_file_name:
        return "loan_data"
    if "customer" in normalized_file_name:
        return "customer_data"
    if "payment" in normalized_file_name:
        return "historic_payment_data"
    if "schedule" in normalized_file_name:
        return "schedule_data"
    return None


def fuzzy_map_core_tables(
    input_dfs: dict[str, pd.DataFrame | dict[str, pd.DataFrame]],
) -> dict[str, pd.DataFrame]:
    mapped_core_tables_dict: dict[str, pd.DataFrame] = {}
    for core_table_map_name, core_table_map_val in input_dfs.items():
        if isinstance(core_table_map_val, dict):
            for core_sheet_map_name, core_sheet_map_df in core_table_map_val.items():
                core_table_map_key = get_normalized_table_type(core_sheet_map_name)
                if core_table_map_key and core_table_map_key not in mapped_core_tables_dict:
                    mapped_core_tables_dict[core_table_map_key] = core_sheet_map_df
        else:
            core_name_map_lower = core_table_map_name.lower()
            core_table_map_key = get_normalized_table_type(core_name_map_lower)
            if core_table_map_key and core_table_map_key not in mapped_core_tables_dict:
                mapped_core_tables_dict[core_table_map_key] = core_table_map_val
    return mapped_core_tables_dict


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
                st.warning(
                    f"⚠️ KPI dashboard file is corrupted or incomplete and could not be loaded "
                    f"({dashboard_path.name}). Re-run the pipeline to regenerate it."
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
    input_dashboard_metrics: dict, input_analytics_facts: pd.DataFrame
) -> tuple[dict[str, float], Optional[pd.Timestamp]]:
    kpi_snapshot: dict[str, float] = {}
    kpi_snapshot_month: Optional[pd.Timestamp] = None
    if not input_analytics_facts.empty:
        for kpi_col_name in ("month", "month_end", "date"):
            if kpi_col_name in input_analytics_facts.columns:
                kpi_parsed = pd.to_datetime(
                    input_analytics_facts[kpi_col_name], errors="coerce"
                ).dropna()
                if not kpi_parsed.empty:
                    kpi_snapshot_month = kpi_parsed.max()
                    break
    kpi_extended_kpis = input_dashboard_metrics.get("extended_kpis", {})
    kpi_executive_strip = kpi_extended_kpis.get("executive_strip", {})
    for unique_key_var, kpi_exec_value_item in kpi_executive_strip.items():
        if isinstance(kpi_exec_value_item, (int, float)):
            kpi_snapshot[unique_key_var] = float(kpi_exec_value_item)
    kpi_root_keys = (
        "total_aum_usd",
        "active_clients",
        "monthly_revenue_usd",
        "revenue_per_active_client_monthly",
        "mom_growth_pct",
        "yoy_growth_pct",
        "par_90_ratio_pct",
        "delinquency_rate_30_pct",
    )
    for unique_root_key_var in kpi_root_keys:
        kpi_root_value_item = input_dashboard_metrics.get(unique_root_key_var)
        if isinstance(kpi_root_value_item, (int, float)):
            kpi_snapshot.setdefault(unique_root_key_var, float(kpi_root_value_item))
    return kpi_snapshot, kpi_snapshot_month


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
    analytics_facts = processor.get_monthly_revenue_df()
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
        main_uploaded_files = st.file_uploader(
            "Upload Loan Tape CSVs and Financial XLSX",
            accept_multiple_files=True,
            type=["csv", "xlsx"],
        )
        if st.button("Ingest Data") or main_uploaded_files:
            main_dfs: dict[str, pd.DataFrame | dict[str, pd.DataFrame]] = {}
            for main_file in main_uploaded_files:
                if main_file.name.endswith(".csv"):
                    main_dfs[main_file.name] = pd.read_csv(main_file)
                elif main_file.name.endswith(".xlsx"):
                    main_dfs[main_file.name] = pd.read_excel(main_file, sheet_name=None)
            if main_dfs:
                for main_name, main_df in main_dfs.items():
                    if isinstance(main_df, dict):
                        for main_sheet, main_sheet_df in main_df.items():
                            main_df[main_sheet] = normalize_dataframe_complete(main_sheet_df)
                    else:
                        main_dfs[main_name] = normalize_dataframe_complete(main_df)
                main_mapped_dfs = fuzzy_map_core_tables(main_dfs)
                final_data = {**main_dfs, **main_mapped_dfs}
                st.session_state["data"] = final_data
                st.session_state["loaded"] = True
                st.success("Data ingested successfully.")
                usage_tracker.track(
                    "data_ingestion",
                    "manual_upload",
                    file_count=len(main_uploaded_files),
                )
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
global_dashboard_metrics_var = load_kpi_dashboard()
global_analytics_facts_var = load_analytics_facts()

with st.expander("🔗 Dashboard Links & Strategic Reporting", expanded=True):
    deployed_dashboard_url = os.getenv(
        "DASHBOARD_PUBLIC_URL",
        "https://abaco-dashboard-app.kindocean-8ac70092.spaincentral.azurecontainerapps.io",
    )
    st.markdown("- **Streamlit (Local):** http://localhost:8501")
    st.markdown("- **Grafana (Local):** http://localhost:3001/dashboards")
    st.markdown(f"- **Streamlit (Deployed):** {deployed_dashboard_url}")
    st.markdown("- **Dashboard docs:** docs/analytics/dashboards.md")
    if st.button("Generate Strategic Report"):
        if global_dashboard_metrics_var:
            strategic_summary = build_strategic_summary(global_dashboard_metrics_var)
            strategic_links = {
                "streamlit_local": "http://localhost:8501",
                "grafana_local": "http://localhost:3001/dashboards",
                "streamlit_prod": deployed_dashboard_url,
                "dashboard_docs": "docs/analytics/dashboards.md",
            }
            strategic_json_path, strategic_md_path = write_strategic_report(
                summary=strategic_summary,
                links=strategic_links,
                output_dir=ROOT_DIR / "reports" / "strategic",
            )
            st.success(f"Strategic report generated: {strategic_md_path}")
            st.caption(f"JSON artifact: {strategic_json_path}")
        else:
            st.warning("Generate KPI exports first to create strategic report artifacts.")

if not global_dashboard_metrics_var and global_analytics_facts_var.empty:
    st.warning(
        "No KPI exports detected. Generate KPI exports from the sidebar or add "
        "complete_kpi_dashboard.json and analytics_facts.csv to the exports "
        "directory."
    )
global_kpi_snapshot, global_snapshot_month_var = build_kpi_snapshot(
    global_dashboard_metrics_var, global_analytics_facts_var
)
render_kpi_snapshot(global_kpi_snapshot, global_snapshot_month_var)
render_cashflow_trends(global_analytics_facts_var)
if not st.session_state["loaded"]:
    st.info("Upload data files in the sidebar to unlock loan-level diagnostics.")
    st.stop()
session_data = st.session_state["data"]
loan_data_df = session_data.get("loan_data")
customer_data_df = session_data.get("customer_data", pd.DataFrame())
if loan_data_df is None:
    global_mapped_dfs_var = fuzzy_map_core_tables(session_data)
    loan_data_df = global_mapped_dfs_var.get("loan_data")
    if customer_data_df.empty:
        customer_data_df = global_mapped_dfs_var.get("customer_data", pd.DataFrame())
if loan_data_df is None:
    st.error("Core loan data missing in uploads.")
    st.stop()
merged_df = loan_data_df.copy()
if (
    not customer_data_df.empty
    and "loan_id" in merged_df.columns
    and "loan_id" in customer_data_df.columns
):
    merged_df = merged_df.merge(
        customer_data_df,
        on="loan_id",
        how="left",
        suffixes=("", "_cust"),
    )
total_outstanding = render_executive_summary(merged_df)
g_col2 = render_growth_analysis(total_outstanding)
render_category_breakdown(merged_df, g_col2)
render_sales_performance(merged_df, load_agent_headcount)
render_risk_analysis(merged_df)
render_advanced_intelligence(global_dashboard_metrics_var)
st.header("📋 KPI Catalog")
with st.expander("View all computed KPIs"):
    all_kpis_expanded = global_dashboard_metrics_var.get("extended_kpis", {})
    if all_kpis_expanded:
        flat_kpis_expanded = []
        for unique_kpi_key_exp, kpi_value_exp in all_kpis_expanded.items():
            if isinstance(kpi_value_exp, (int, float, str)):
                flat_kpis_expanded.append(
                    {
                        "KPI": kpi_label(unique_kpi_key_exp),
                        "Value": format_kpi_value(unique_kpi_key_exp, kpi_value_exp),
                    }
                )
        if flat_kpis_expanded:
            st.table(pd.DataFrame(flat_kpis_expanded))
        st.write("**Detailed Data Tables:**")
        table_keys_expanded = [
            unique_table_key_exp
            for unique_table_key_exp, v_exp in all_kpis_expanded.items()
            if isinstance(v_exp, list) and v_exp
        ]
        selected_table_expanded = st.selectbox("Select table to view", table_keys_expanded)
        if selected_table_expanded:
            st.dataframe(pd.DataFrame(all_kpis_expanded[selected_table_expanded]))
    else:
        st.info("No extended KPIs found.")
st.divider()
st.caption(
    "Abaco Intelligence Platform | System Date: " f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
