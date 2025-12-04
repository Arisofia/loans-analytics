import hashlib
import os
import re
import unicodedata
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics_metrics import (
    calculate_quality_score,
    portfolio_kpis,
    project_growth,
    standardize_numeric,
)

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
        "warning": "#FB923C",
        "error": "#DC2626",
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

REQUIRED_COLUMNS = [
    "loan_amount",
    "appraised_value",
    "borrower_income",
    "monthly_debt",
    "loan_status",
    "interest_rate",
    "principal_balance",
]


def apply_theme(fig: px.Figure) -> px.Figure:
    fig.update_layout(
        font_family=ABACO_THEME["typography"]["primary_font"],
        font_color=ABACO_THEME["colors"]["white"],
        paper_bgcolor=ABACO_THEME["colors"]["background"],
        plot_bgcolor=ABACO_THEME["colors"]["background"],
        legend=dict(
            font=dict(
                family=ABACO_THEME["typography"]["secondary_font"],
                color=ABACO_THEME["colors"]["light_gray"],
            )
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    fig.update_traces(marker=dict(line=dict(color=ABACO_THEME["colors"]["background"], width=1)))
    return fig


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    clean = (
        df.rename(columns=lambda col: re.sub(r"[^a-z0-9_]", "_", re.sub(r"\s+", "_", col.strip().lower())))
        .pipe(lambda d: d.loc[:, ~d.columns.duplicated()])
    )
    return clean


def safe_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(r"[₡$€,,%]", "", regex=True)
        .str.replace(",", "", regex=False)
        .replace("", np.nan)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def compute_upload_signature(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    current_position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else None
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    file_bytes = uploaded_file.getvalue()
    digest = hashlib.sha256(file_bytes).hexdigest()
    if hasattr(uploaded_file, "seek") and current_position is not None:
        uploaded_file.seek(current_position)
    return f"{uploaded_file.name}:{uploaded_file.size}:{digest}"


def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9]+", " ", stripped.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def select_payer_column(df: pd.DataFrame) -> Optional[str]:
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
        if preferred_name.lower() in column_lookup:
            return column_lookup[preferred_name.lower()]
    for col in df.columns:
        if re.search(r"payer|payor|pagador|offtaker|buyer|debtor", col, re.IGNORECASE):
            return col
    return None


def compute_roll_rates(df: pd.DataFrame) -> pd.DataFrame:
    if "dpd_status" not in df.columns or "loan_status" not in df.columns:
        return pd.DataFrame()
    base = df.loc[df["dpd_status"].notna()]
    transitions = (
        base.groupby(["dpd_status", "loan_status"]).size().reset_index(name="count")
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
    uploaded.seek(0)
    try:
        return pd.read_csv(uploaded)
    except Exception:
        return pd.DataFrame()


st.set_page_config(
    page_title="ABACO Financial Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@100;300;400;700;900&family=Poppins:wght@100;200;300;400;500;600;700&display=swap');
.stApp {{
    background-color: {ABACO_THEME['colors']['background']};
}}
.stSidebar {{
    background: linear-gradient(180deg, rgba(12, 39, 66, 0.95) 0%, rgba(3, 14, 25, 0.98) 100%) !important;
}}
.abaco-card {{
    background: {ABACO_THEME['gradients']['card_primary']};
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
    border: 2px solid rgba(193, 166, 255, 0.4);
}}
.abaco-metric {{
    font-size: {ABACO_THEME['typography']['metric_size']};
    color: {ABACO_THEME['colors']['white']};
    letter-spacing: 0.08em;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.title("ABACO Financial Intelligence Platform")
st.markdown(
    """This canvas operationalizes the analytics vision documented in docs/Analytics-Vision.md. Every section verifies data availability, computes KPIs from real uploaded datasets, and surfaces AI-ready insight summaries."""
)

st.sidebar.header("Streamlit Ingestion")
uploaded = st.sidebar.file_uploader("Upload the core loan dataset (CSV)", type=["csv"], accept_multiple_files=False)
validation_toggle = st.sidebar.checkbox("Validate upload schema", value=True)
st.sidebar.caption("Use this area to trigger ingestion, refresh safely, and capture metadata.")
if validation_toggle and uploaded is not None:
    columns = normalize_columns(parse_uploaded_file(uploaded)).columns
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
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


def should_ingest(signature: Optional[str]) -> bool:
    return signature is not None and signature != st.session_state.get("last_upload_signature")


def ingest(uploaded_file, signature: Optional[str]) -> None:
    raw = parse_uploaded_file(uploaded_file)
    normalized = normalize_columns(raw)
    numeric_payload = normalized.copy()
    for col in normalized.select_dtypes(include=["object"]).columns:
        converted = safe_numeric(numeric_payload[col])
        if converted.notna().sum() > 0:
            numeric_payload[col] = converted
    st.session_state["loan_data"] = numeric_payload
    st.session_state["ingestion_state"] = define_ingestion_state(numeric_payload)
    st.session_state["last_upload_signature"] = signature
    st.session_state["last_ingested_at"] = pd.Timestamp.now()


current_signature = compute_upload_signature(uploaded)
if should_ingest(current_signature):
    ingest(uploaded, current_signature)

if st.sidebar.button("Refresh ingestion", use_container_width=True):
    if uploaded is not None:
        ingest(uploaded, compute_upload_signature(uploaded))
        st.sidebar.success("Ingestion refreshed.")
    else:
        st.sidebar.warning("Upload a new file before refreshing.")

st.markdown("## Ingestion & Proofing section")
if st.session_state["loan_data"].empty:
    st.warning("Upload the core loan dataset first; downstream sections will wait until the base table exists.")
    st.stop()

loan_df = st.session_state["loan_data"]
ing_state = st.session_state["ingestion_state"]
st.markdown(f"- Rows: {ing_state['rows']}, Columns: {ing_state['columns']}")
st.markdown(f"- Loan base validated: {ing_state['has_loan_base']}")
if st.session_state["last_ingested_at"] is not None:
    st.markdown(f"- Last ingested at: {st.session_state['last_ingested_at'].strftime('%Y-%m-%d %H:%M:%S')}")

missing_required_columns = [col for col in REQUIRED_COLUMNS if col not in loan_df.columns]
if missing_required_columns:
    st.error(
        "Cannot compute KPIs until the dataset includes the following columns: "
        + ", ".join(sorted(missing_required_columns))
    )
    st.stop()

st.markdown("## Data Quality Audit")
quality_score = calculate_quality_score(loan_df)
st.progress(quality_score / 100)
st.markdown("Critical tables scored, missing columns handled, and zeros penalized before KPI synthesis.")

st.markdown("## Payer Coverage Scan")
payer_column = select_payer_column(loan_df)
if payer_column:
    st.success(f"Detected payer column: {payer_column}")
    normalized_col = f"{payer_column}_normalized"
    loan_df[normalized_col] = loan_df[payer_column].apply(normalize_text)
    target_aliases = {
        "Vicepresidencia de la Republica": [r"vice\s*presidencia", r"vicepresidencia de la republica"],
        "Bimbo": [r"bimbo", r"grupo\s*bimbo", r"marinela"],
        "EPA": [r"\bepa\b", r"almacenes\s*epa", r"ferreteria\s*epa"],
        "Walmart": [r"walmart", r"walmart de mexico y centroamerica", r"walmart centroamerica"],
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
        st.info(f"No matches detected for: {', '.join(missing)}. Use normalized payer names to confirm coverage gaps.")
else:
    st.info("Add a payer/payor/pagador/offtaker/buyer/debtor column to assess coverage.")

st.markdown("## KPI Calculations")
metrics, enriched_df = portfolio_kpis(loan_df)
enriched_df["delinquency_rate"] = metrics["delinquency_rate"]
loan_df = enriched_df
st.markdown(f"- **Delinquency rate:** {metrics['delinquency_rate']:.2f}%")
st.markdown(f"- **Portfolio yield:** {metrics['portfolio_yield']:.2f}%")
st.markdown(f"- **Average LTV:** {metrics['average_ltv']:.1f}%")
st.markdown(f"- **Average DTI:** {metrics['average_dti']:.1f}%")
alerts = enriched_df[enriched_df["ltv_ratio"] > 90].assign(
    alert_type="High LTV",
    probability=lambda d: np.clip((d["ltv_ratio"] - 90) / 20, 0, 1),
)
st.dataframe(alerts[["alert_type", "ltv_ratio", "probability"]], hide_index=True)

st.markdown("## Growth & Marketing Analysis")
targets = {
    "target_monthly_yield": st.number_input("Target monthly yield (%)", value=1.5),
    "target_active_loans": st.number_input("Target active loans", value=150),
}
current_metrics = {
    "current_yield": metrics["portfolio_yield"],
    "active_loans": len(enriched_df),
}
gap_yield = targets["target_monthly_yield"] - current_metrics["current_yield"]
gap_loans = targets["target_active_loans"] - current_metrics["active_loans"]
st.metric("Yield gap", f"{gap_yield:.2f}%")
st.metric("Loan gap", f"{gap_loans:.0f}")
monthly_projection = project_growth(
    current_yield=current_metrics["current_yield"],
    target_yield=targets["target_monthly_yield"],
    current_loan_volume=current_metrics["active_loans"],
    target_loan_volume=targets["target_active_loans"],
    periods=6,
).assign(month=lambda d: d["date"].dt.strftime("%b %Y"))
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
    "AI integration available; run a prompt to synthesize KPIs." if needs_ai else "Rule-based summary: focus on delinquency, growth, and alert signals to guide stakeholders."
)
st.markdown(summary)

st.markdown("## Export & Figma Preparation")
st.markdown('Prepare flattened fact tables for the Figma storyboard: https://www.figma.com/make/nuVKwuPuLS7VmLFvqzOX1G/Create-Dark-Editable-Slides?node-id=0-1&t=8coqxRUeoQvNvavm-1')
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
    if "delinquency_rate" in loan_df.columns
    else ["loan_amount", "principal_balance", "interest_rate", "loan_status", "ltv_ratio", "dti_ratio"]
].copy()
st.download_button(
    label="Download flattened fact table",
    data=fact_table.to_csv(index=False).encode("utf-8"),
    file_name="abaco_fact_table.csv",
    mime="text/csv",
)
