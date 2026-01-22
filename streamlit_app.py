
from __future__ import annotations
import hashlib
import os
import re
import json
from pathlib import Path
from datetime import datetime
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import polars as pl
import streamlit as st
from src.analytics.polars_analytics_engine import PolarsAnalyticsEngine

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





def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.rename(
        columns=lambda col: re.sub(r"[^a-z0-9_]", "_", re.sub(r"\s+", "_", col.strip().lower()))
    ).pipe(lambda d: d.loc[:, ~d.columns.duplicated()])
    return clean


def safe_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(r"[₡$€,,%]", "", regex=True)
        .str.replace(",", "", regex=False)
        .replace("", np.nan)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def compute_upload_signature(uploaded_file) -> str | None:
    if uploaded_file is None:
        return None
    content = uploaded_file.getvalue()
    digest = hashlib.md5(content[:1048576]).hexdigest()
    return f"{uploaded_file.name}:{uploaded_file.size}:{digest}"


def normalize_text(value) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = re.sub(r"[^a-z0-9\s]", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def select_payer_column(df: pd.DataFrame) -> str | None:
    preferred = [
        "payer",
        "payer_name",
        "payor",
        "pagador",
        "offtaker",
        "buyer",
        "debtor",
        "customer_name",
    ]
    column_lookup = {col.lower(): col for col in df.columns}
    for preferred_name in preferred:
        lookup_key = preferred_name.lower()
        if lookup_key in column_lookup:
            return column_lookup[lookup_key]
    return next(
        (
            col
            for col in df.columns
            if re.search(
                r"payer|payor|pagador|offtaker|buyer|debtor",
                col,
                re.IGNORECASE,
            )
        ),
        None,
    )


def compute_roll_rates(df: pd.DataFrame) -> pd.DataFrame:
    if "dpd_status" not in df.columns or "loan_status" not in df.columns:
        return pd.DataFrame()
    base = df.loc[df["dpd_status"].notna()]
    transitions = (
        base.groupby(["dpd_status", "loan_status"])
        .size()
        .reset_index(name="count")
        .assign(percent=lambda d: d["count"] / d["count"].sum() * 100)
    )
    return transitions


def define_ingestion_state(df: pd.DataFrame) -> pd.Series:
    return pd.Series(
        {
            "rows": len(df),
            "columns": len(df.columns),
            "has_loan_base": "loan_status" in df.columns
            and "loan_amount" in df.columns
            and "principal_balance" in df.columns,
        }
    )


@st.cache_data(show_spinner=False)
def parse_uploaded_file(uploaded) -> pd.DataFrame:
    if uploaded is None:
        return pd.DataFrame()
    return pd.read_csv(uploaded)


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
                col.astype(str).str.replace(r"[$,€%₡,]", "", regex=True),
                errors="coerce",
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

    percent_hints = (
        "pct",
        "rate",
        "ratio",
        "yield",
        "apr",
        "penetration",
        "recurrence",
    )
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
    count_hints = (
        "clients",
        "customers",
        "loans",
        "count",
        "early",
        "late",
        "on_time",
        "fte",
    )

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

st.sidebar.header("Streamlit Ingestion")
uploaded = st.sidebar.file_uploader(
    "Upload the core loan dataset (CSV)", type=["csv"], accept_multiple_files=False
)
validation_toggle = st.sidebar.checkbox("Validate upload schema", value=True)
st.sidebar.caption("Use this area to trigger ingestion, refresh safely, and capture metadata.")
if validation_toggle and uploaded is not None:
    required = [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "loan_status",
        "interest_rate",
        "principal_balance",
    ]
    columns = normalize_columns(parse_uploaded_file(uploaded)).columns
    missing = [col for col in required if col not in columns]
    if missing:
        st.sidebar.error(f"Missing required columns: {', '.join(sorted(set(missing)))}")

if "loan_data" not in st.session_state:
    st.session_state["loan_data"] = pd.DataFrame()
if "ingestion_state" not in st.session_state:
    st.session_state["ingestion_state"] = {}
if "last_upload_signature" not in st.session_state:
    st.session_state["last_upload_signature"] = None
if "last_ingested_at" not in st.session_state:
    st.session_state["last_ingested_at"] = None


def ingest(uploaded_file, signature: str | None):
    raw = parse_uploaded_file(uploaded_file)
    normalized = normalize_columns(raw)
    numeric_columns = normalized.select_dtypes(include=["object"]).columns
    numeric_payload = normalized.copy()
    for col in numeric_columns:
        numeric_payload[col] = safe_numeric(numeric_payload[col])
    st.session_state["loan_data"] = numeric_payload
    st.session_state["ingestion_state"] = define_ingestion_state(numeric_payload)
    st.session_state["last_upload_signature"] = signature
    st.session_state["last_ingested_at"] = pd.Timestamp.now()


if uploaded is not None and (current_signature := compute_upload_signature(uploaded)):
    if current_signature != st.session_state.get("last_upload_signature"):
        ingest(uploaded, current_signature)
    else:
        st.sidebar.info("Upload unchanged since last ingestion; skipping reload.")

if st.sidebar.button("Refresh ingestion", use_container_width=True):
    if uploaded is not None and (signature := compute_upload_signature(uploaded)):
        ingest(uploaded, signature)
        st.sidebar.success("Ingestion refreshed.")
    else:
        st.sidebar.warning("Upload a new file before refreshing.")

st.markdown("## Ingestion & Proofing section")
if st.session_state["loan_data"].empty:
    st.warning(
        "Upload the core loan dataset first; downstream sections will wait until the base table exists."
    )
    st.stop()

loan_df = st.session_state["loan_data"]
total_loans = len(loan_df)
ing_state = st.session_state["ingestion_state"]
st.markdown(f"- Rows: {ing_state['rows']}, Columns: {ing_state['columns']}")
st.markdown(f"- Loan base validated: {ing_state['has_loan_base']}")
if st.session_state["last_ingested_at"] is not None:
    st.markdown(
        f"- Last ingested at: {st.session_state['last_ingested_at'].strftime('%Y-%m-%d %H:%M:%S')}"
    )

st.markdown("## Data Quality Audit")
quality_score = 100
if ing_state["rows"] == 0 or ing_state["columns"] == 0:
    quality_score = 0
else:
    quality_score -= loan_df.isna().mean().mean() * 100
quality_score = max(0, min(100, quality_score))
st.progress(quality_score / 100)
st.markdown(
    "Critical tables scored, missing columns handled, and zeros penalized before KPI synthesis."
)

st.markdown("## Payer Coverage Scan")
payer_column = select_payer_column(loan_df)
if payer_column:
    st.success(f"Detected payer column: {payer_column}")
    normalized_col = f"{payer_column}_normalized"
    loan_df[normalized_col] = loan_df[payer_column].apply(normalize_text)
    target_aliases = {
        "Vicepresidencia de la Republica": [
            r"vice\s*presidencia",
            r"vicepresidencia de la republica",
        ],
        "Bimbo": [r"bimbo", r"grupo\s*bimbo", r"marinela"],
        "EPA": [r"\bepa\b", r"almacenes\s*epa", r"ferreteria\s*epa"],
        "Walmart": [
            r"walmart",
            r"walmart de mexico y centroamerica",
            r"walmart centroamerica",
        ],
        "Pricesmart": [r"prices?mart"],
        "Nestle": [r"nestl[eé]", r"nestle el salvador"],
        "Coca Cola": [r"coca\s*cola", r"femsa"],
    }
    coverage_rows = []
    for target, patterns in target_aliases.items():
        pattern = "|".join(patterns)
        mask = loan_df[normalized_col].str.contains(pattern, regex=True, na=False)
        exposure = (
            loan_df.loc[mask, "principal_balance"].sum()
            if "principal_balance" in loan_df.columns
            else np.nan
        )
        coverage_rows.append(
            {
                "Target": target,
                "Matches": int(mask.sum()),
                "Outstanding Exposure": exposure,
            }
        )
    coverage_df = pd.DataFrame(coverage_rows)
    st.dataframe(coverage_df, hide_index=True)
    missing = coverage_df.loc[coverage_df["Matches"] == 0, "Target"].tolist()
    if missing:
        st.info(
            f"No matches detected for: {', '.join(missing)}. Use normalized payer names to confirm coverage gaps."
        )
else:
    st.info("Add a payer/payor/pagador/offtaker/buyer/debtor column to assess coverage.")

st.markdown("## KPI Calculations")

# Use PolarsAnalyticsEngine for core calculations
engine = PolarsAnalyticsEngine(pl.from_pandas(loan_df))
kpis = engine.compute_kpis()

# Update loan_df with ratios for downstream sections
ratios_df = engine.compute_ratios().collect().to_pandas()
loan_df["ltv_ratio"] = ratios_df["ltv_ratio"]
loan_df["dti_ratio"] = ratios_df["dti_ratio"]

delinquency_rate = kpis["delinquency_rate"]
portfolio_yield = kpis["portfolio_yield"]
avg_ltv = kpis["avg_ltv"]
avg_dti = kpis["avg_dti"]

st.markdown(f"- **Delinquency rate:** {delinquency_rate:.2f}%")
st.markdown(f"- **Portfolio yield:** {portfolio_yield:.2f}%")
st.markdown(f"- **Average LTV:** {avg_ltv:.1f}%")
st.markdown(f"- **Average DTI:** {avg_dti:.1f}%")

# Risk Alerts via Polars
risk_alerts_df = engine.get_risk_alerts()
if not risk_alerts_df.is_empty():
    alerts = risk_alerts_df.to_pandas().assign(
        alert_type="High Risk",
        probability=lambda d: np.clip((d["ltv_ratio"] - 90) / 20, 0, 1),
    )
    st.dataframe(alerts[["alert_type", "ltv_ratio", "probability"]], hide_index=True)
else:
    st.info("No high-risk loans detected.")

st.markdown("## Growth & Marketing Analysis")
targets = {
    "target_monthly_yield": st.number_input("Target monthly yield (%)", value=1.5),
    "target_active_loans": st.number_input("Target active loans", value=150),
}
current_metrics = {
    "current_yield": portfolio_yield,
    "active_loans": total_loans,
}
gap_yield = targets["target_monthly_yield"] - current_metrics["current_yield"]
gap_loans = targets["target_active_loans"] - current_metrics["active_loans"]
st.metric("Yield gap", f"{gap_yield:.2f}%")
st.metric("Loan gap", f"{gap_loans:.0f}")
monthly_projection = pd.DataFrame(
    {
        "month": pd.date_range(start=pd.Timestamp.now(), periods=6, freq="MS"),
        "yield": np.linspace(current_metrics["current_yield"], targets["target_monthly_yield"], 6),
        "loan_volume": np.linspace(
            current_metrics["active_loans"], targets["target_active_loans"], 6
        ),
    }
).assign(month=lambda d: d["month"].dt.strftime("%b %Y"))
fig_growth = px.line(
    monthly_projection,
    x="month",
    y=["yield", "loan_volume"],
    markers=True,
    title="Projected Growth Path",
)
apply_theme(fig_growth)
st.plotly_chart(fig_growth, use_container_width=True)
treemap_source = loan_df.sample(min(1000, len(loan_df)))
fig_treemap = px.treemap(
    treemap_source,
    path=["loan_status"],
    values="principal_balance",
    title="Marketing & Sales Treemap",
)
apply_theme(fig_treemap)
st.plotly_chart(fig_treemap, use_container_width=True)

st.markdown("## Roll Rate / Cascade")
roll_rates = compute_roll_rates(loan_df)
if roll_rates.empty:
    st.info("Roll rate data requires dpd_status and loan_status columns to compute transitions.")
else:
    st.dataframe(roll_rates, hide_index=True)

st.markdown("## AI Integration & Narrative")
needs_ai = all(key in os.environ for key in ("OPENAI_API_KEY", "GOOGLE_API_KEY"))
summary = (
    "AI integration available; run a prompt to synthesize KPIs."
    if needs_ai
    else "Rule-based summary: focus on delinquency, growth, and alert signals to guide stakeholders."
)
st.markdown(summary)

st.markdown("## Export & Figma Preparation")
st.markdown(
    "Prepare flattened fact tables for the Figma storyboard: https://www.figma.com/make/nuVKwuPuLS7VmLFvqzOX1G/Create-Dark-Editable-Slides?node-id=0-1&t=8coqxRUeoQvNvavm-1"
)
cash_cols = [
    "recv_revenue_for_month",
    "recv_interest_for_month",
    "recv_fee_for_month",
    "sched_revenue",
]
analytics_facts = load_analytics_facts()
fact_table = loan_df[
    [
        "loan_amount",
        "principal_balance",
        "interest_rate",
        "loan_status",
        "ltv_ratio",
        "dti_ratio",
        "delinquency_rate",
    ]
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
        "Download CSV",
        export_df.to_csv(index=False).encode("utf-8"),
        "abaco_export.csv",
    )

st.divider()
st.caption(
    f"Abaco Intelligence Platform | System Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
