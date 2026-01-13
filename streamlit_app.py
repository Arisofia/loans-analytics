"""Streamlit dashboard for Abaco Loans Analytics - Engineering Excellence Edition."""

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Theme definition (as per design system)
ABACO_THEME = {
    "colors": {
        "primary_purple": "#C1A6FF",
        "purple_dark": "#5F4896",
        "dark_blue": "#0C2742",
        "light_gray": "#CED4D9",
        "medium_gray": "#9EA9B3",
        "dark_gray": "#6D7D8E",
        "white": "#FFFFFF",
        "background": "#030E19",
        "success": "#10B981",
        "success_dark": "#059669",
        "warning": "#FB923C",
        "warning_dark": "#EA580C",
        "error": "#DC2626",
        "error_dark": "#991B1B",
        "info": "#3B82F6",
        "info_dark": "#1D4ED8",
    },
    "gradients": {
        "title": "linear-gradient(81.74deg, #C1A6FF 5.91%, #5F4896 79.73%)",
        "card_primary": "linear-gradient(135deg, rgba(193, 166, 255, 0.2) 0%, rgba(0, 0, 0, 0.5) 100%)",
        "card_secondary": "linear-gradient(135deg, rgba(34, 18, 72, 0.4) 0%, rgba(0, 0, 0, 0.6) 100%)",
        "card_highlight": "linear-gradient(135deg, rgba(193, 166, 255, 0.25) 0%, rgba(0, 0, 0, 0.8) 100%)",
    },
    "typography": {
        "primary_font": "Lato",
        "secondary_font": "Poppins",
        "title_size": "48px",
        "metric_size": "48px",
        "label_size": "16px",
        "body_size": "14px",
        "description_size": "12px",
    },
}

st.set_page_config(
    page_title="ABACO Financial Intelligence Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT_DIR = Path(__file__).resolve().parent
LOOKER_DIR = ROOT_DIR / "data" / "raw" / "looker_exports"
EXPORTS_DIR = ROOT_DIR / "exports"
SUPPORT_DIR = ROOT_DIR / "data" / "support"


# Utility functions
def apply_theme(fig):
    fig.update_layout(
        plot_bgcolor=ABACO_THEME["colors"]["background"],
        paper_bgcolor=ABACO_THEME["colors"]["background"],
        font_color=ABACO_THEME["colors"]["light_gray"],
        title_font_color=ABACO_THEME["colors"]["primary_purple"],
        colorway=["#C1A6FF", "#5F4896", "#10B981", "#FB923C"],
    )
    return fig


def styled_df(df):
    return df.style.set_table_styles(
        [
            {
                "selector": "tr:hover",
                "props": [("background-color", ABACO_THEME["colors"]["medium_gray"])],
            }
        ]
    )


def clean_numeric(col):
    if col.dtype == "object":
        sample = col.dropna().astype(str).head(50)
        cleaned = sample.str.replace(r"[$,€%₡,]", "", regex=True)
        numeric_ratio = pd.to_numeric(cleaned, errors="coerce").notna().mean()
        if numeric_ratio >= 0.6:
            col = pd.to_numeric(
                col.astype(str).str.replace(r"[$,€%₡,]", "", regex=True), errors="coerce"
            )
    return col


def normalize_dataframe(df):
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    for col in df.columns:
        df[col] = clean_numeric(df[col])
    return df


def format_percent(value):
    if abs(value) <= 1:
        return f"{value:.2%}"
    return f"{value:.2f}%"


def format_kpi_value(name, value):
    if value is None or pd.isna(value):
        return "—"
    if isinstance(value, str):
        return value

    name_lower = name.lower()
    if name_lower in {"ltv_cac_ratio", "rotation"}:
        return f"{value:.2f}x"

    percent_hints = ("pct", "rate", "ratio", "yield", "apr", "penetration", "recurrence")
    currency_hints = (
        "usd",
        "revenue",
        "outstanding",
        "disbursement",
        "fee",
        "interest",
        "aum",
        "capital",
        "payment",
        "received",
        "sched",
    )
    count_hints = ("clients", "customers", "loans", "count", "early", "late", "on_time", "fte")

    if any(hint in name_lower for hint in percent_hints):
        return format_percent(float(value))
    if any(hint in name_lower for hint in currency_hints):
        return f"${float(value):,.2f}"
    if any(hint in name_lower for hint in count_hints):
        return f"{float(value):,.0f}"

    return f"{float(value):,.2f}"


KPI_LABEL_OVERRIDES = {
    "total_aum_usd": "Total AUM (USD)",
    "ltv_cac_ratio": "LTV / CAC",
    "par_90_ratio_pct": "PAR 90 Ratio",
    "mom_growth_pct": "MoM Growth",
    "yoy_growth_pct": "YoY Growth",
}


def kpi_label(name):
    return KPI_LABEL_OVERRIDES.get(name, name.replace("_", " ").title())


@st.cache_data(show_spinner=False)
def load_looker_exports():
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
        df = pd.read_csv(path)
        data[key] = normalize_dataframe(df)
    return data


@st.cache_data(show_spinner=False)
def load_analytics_facts():
    facts_path = EXPORTS_DIR / "analytics_facts.csv"
    if not facts_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(facts_path)
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
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

    from src.analytics.kpi_calculator_complete import ABACOKPICalculator

    calc = ABACOKPICalculator(
        looker_data["loan_data"],
        looker_data["historic_payment_data"],
        looker_data["customer_data"],
    )
    dashboard = calc.get_complete_kpi_dashboard(cac_usd=350)
    dashboard["timestamp"] = datetime.now().isoformat()

    try:
        from src.analytics.kpi_catalog_processor import KPICatalogProcessor

        catalog_proc = KPICatalogProcessor(
            looker_data["loan_data"],
            looker_data["historic_payment_data"],
            looker_data["customer_data"],
            looker_data.get("schedule_data"),
        )
        dashboard["extended_kpis"] = catalog_proc.get_all_kpis()

        figma_df = catalog_proc.get_figma_dashboard_df()
        figma_df.to_csv(exports_dir / "analytics_facts.csv", index=False)

        scorecard_df = catalog_proc.get_quarterly_scorecard()
        scorecard_df.to_csv(exports_dir / "quarterly_scorecard.csv", index=False)
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
                for name, df in dfs.items():
                    if isinstance(df, dict):
                        for sheet, sdf in df.items():
                            dfs[name][sheet] = normalize_dataframe(sdf)
                    else:
                        dfs[name] = normalize_dataframe(df)

                st.session_state["data"] = dfs
                st.session_state["loaded"] = True
                st.success("Data ingested successfully.")

                # Auto-generate KPI exports from uploaded data
                with st.spinner("Generating KPI exports from uploaded data..."):
                    try:
                        output_path = generate_kpi_exports(dfs)
                        st.cache_data.clear()
                        st.info(f"✅ KPI exports generated: {output_path}")
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

if kpi_snapshot:
    st.header("📌 KPI Snapshot")
    if snapshot_month is not None and not pd.isna(snapshot_month):
        st.caption(f"Snapshot month: {snapshot_month.strftime('%Y-%m')}")
    st.caption(f"KPI count: {len(kpi_snapshot)}")

    kpi_items = sorted(kpi_snapshot.items(), key=lambda item: item[0])
    kpi_cols = st.columns(4)
    for idx, (name, value) in enumerate(kpi_items):
        kpi_cols[idx % 4].metric(kpi_label(name), format_kpi_value(name, value))
else:
    st.info("KPI snapshot not available. Export analytics to populate KPI tiles.")

if not analytics_facts.empty:
    st.header("💸 Cashflow")
    cash_cols = [
        "recv_revenue_for_month",
        "recv_interest_for_month",
        "recv_fee_for_month",
        "sched_revenue",
    ]
    available_cols = [col for col in cash_cols if col in analytics_facts.columns]
    if available_cols:
        cash_df = analytics_facts[["month"] + available_cols].copy()
        cash_df = cash_df.dropna(subset=["month"])
        fig_cash = px.line(
            cash_df,
            x="month",
            y=available_cols,
            title="Cashflow Trends",
            markers=True,
        )
        st.plotly_chart(apply_theme(fig_cash), use_container_width=True)

        latest_cash = cash_df.sort_values("month").iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        if "recv_revenue_for_month" in latest_cash:
            c1.metric(
                "Revenue (Received)",
                format_kpi_value("recv_revenue_for_month", latest_cash["recv_revenue_for_month"]),
            )
        if "recv_interest_for_month" in latest_cash:
            c2.metric(
                "Interest (Received)",
                format_kpi_value("recv_interest_for_month", latest_cash["recv_interest_for_month"]),
            )
        if "recv_fee_for_month" in latest_cash:
            c3.metric(
                "Fees (Received)",
                format_kpi_value("recv_fee_for_month", latest_cash["recv_fee_for_month"]),
            )
        if "sched_revenue" in latest_cash:
            c4.metric(
                "Revenue (Scheduled)",
                format_kpi_value("sched_revenue", latest_cash["sched_revenue"]),
            )

if not st.session_state["loaded"]:
    st.info("Upload data files in the sidebar to unlock loan-level diagnostics.")
    st.stop()

data = st.session_state["data"]

# Core Tables Identification
loan_data = None
customer_data = pd.DataFrame()

for name, df in data.items():
    if "loan" in name.lower() and "data" in name.lower():
        loan_data = df
    elif "customer" in name.lower():
        customer_data = df

if loan_data is None:
    st.error("Core loan data missing in uploads.")
    st.stop()

merged = loan_data.copy()
if not customer_data.empty and "loan_id" in merged.columns and "loan_id" in customer_data.columns:
    merged = merged.merge(customer_data, on="loan_id", how="left", suffixes=("", "_cust"))

# --- 1. Portfolio Overview ---
st.header("📊 Executive Summary")
col1, col2, col3, col4 = st.columns(4)

total_loans = merged["loan_id"].nunique() if "loan_id" in merged else 0
total_outstanding = (
    merged["outstanding_loan_value"].sum() if "outstanding_loan_value" in merged else 0
)
# Calculate weighted average APR (weighted by outstanding loan value)
if "interest_rate_apr" in merged.columns and "outstanding_loan_value" in merged.columns:
    total_balance = merged["outstanding_loan_value"].sum()
    if total_balance > 0:
        avg_apr = (
            merged["interest_rate_apr"] * merged["outstanding_loan_value"]
        ).sum() / total_balance
    else:
        avg_apr = 0
else:
    avg_apr = 0
default_rate = (merged["loan_status"] == "Default").mean() * 100 if "loan_status" in merged else 0

col1.metric("Total Loans", f"{total_loans:,}")
col2.metric("Total Outstanding", f"${total_outstanding:,.2f}")
col3.metric("Average APR", f"{avg_apr:.2%}")
col4.metric("Default Rate", f"{default_rate:.2f}%")

# --- 2. Growth Analysis ---
st.header("📈 Growth & Projections")
g_col1, g_col2 = st.columns(2)

current_outstanding = total_outstanding
target_o = st.session_state.get("target_outstanding", 8360500.0)
gap_o = target_o - current_outstanding

with g_col1:
    st.write(f"**Target Gap:** ${gap_o:,.2f}")
    months = np.arange(13)
    proj_values = np.linspace(current_outstanding, target_o, 13)
    df_proj = pd.DataFrame({"Month": months, "Projected": proj_values})
    fig_growth = px.line(
        df_proj, x="Month", y="Projected", title="12-Month Portfolio Growth Projection"
    )
    st.plotly_chart(apply_theme(fig_growth), use_container_width=True)

with g_col2:
    if "categoria" in merged.columns:
        cat_agg = merged.groupby("categoria")["outstanding_loan_value"].sum().reset_index()
        fig_cat = px.pie(
            cat_agg,
            values="outstanding_loan_value",
            names="categoria",
            title="Portfolio by Category",
        )
        st.plotly_chart(apply_theme(fig_cat), use_container_width=True)

# --- 3. Marketing & Sales ---
st.header("🎯 Sales Performance")
if "sales_agent" in merged.columns:
    sales_agg = (
        merged.groupby("sales_agent")
        .agg({"outstanding_loan_value": "sum", "loan_id": "count"})
        .reset_index()
        .rename(columns={"outstanding_loan_value": "Volume", "loan_id": "Count"})
    )
    fig_sales = px.treemap(
        sales_agg,
        path=["sales_agent"],
        values="Volume",
        color="Count",
        title="Sales Agent Volume Distribution",
    )
    st.plotly_chart(apply_theme(fig_sales), use_container_width=True)
else:
    headcount_df = load_agent_headcount()
    if not headcount_df.empty and {"month", "function", "fte_count"}.issubset(headcount_df.columns):
        st.subheader("Team Capacity")
        latest_month = headcount_df["month"].max()
        latest_headcount = headcount_df[headcount_df["month"] == latest_month]
        fig_headcount = px.bar(
            latest_headcount,
            x="function",
            y="fte_count",
            color="team" if "team" in latest_headcount.columns else None,
            title="Headcount by Function",
        )
        st.plotly_chart(apply_theme(fig_headcount), use_container_width=True)
    else:
        st.info(
            "Sales agent data not found. Provide agent performance data to populate this section."
        )

# --- 4. Risk Analysis ---
st.header("⚠️ Risk Analysis")
r_col1, r_col2 = st.columns(2)

with r_col1:
    if "days_in_default" in merged.columns:
        merged["dpd_bucket"] = pd.cut(
            merged["days_in_default"],
            bins=[-1, 0, 30, 60, 90, float("inf")],
            labels=["Current", "1-30", "31-60", "61-90", "90+"],
        )
        dpd_dist = (
            merged["dpd_bucket"]
            .value_counts()
            .reindex(["Current", "1-30", "31-60", "61-90", "90+"])
            .reset_index()
        )
        dpd_dist.columns = ["Bucket", "Count"]
        fig_dpd = px.bar(dpd_dist, x="Bucket", y="Count", title="DPD Bucket Distribution")
        st.plotly_chart(apply_theme(fig_dpd), use_container_width=True)

with r_col2:
    st.subheader("Data Quality Audit")
    score = 100.0
    if total_outstanding == 0:
        score -= 40
    if "interest_rate_apr" not in merged.columns:
        score -= 20
    st.metric("Quality Score", f"{score:.1f}%")

# --- 5. Export ---
st.header("📤 Export")
if st.button("Prepare Export"):
    export_df = merged.head(100)
    st.dataframe(styled_df(export_df))
    st.download_button(
        "Download CSV", export_df.to_csv(index=False).encode("utf-8"), "abaco_export.csv"
    )

st.divider()
st.caption(
    f"Abaco Intelligence Platform | System Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
