"""Streamlit portal for ABACO loan analytics."""
import io
import re
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
        "metric_size": "32px",
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


@st.cache_data(show_spinner=False)
def parse_uploaded_file(uploaded) -> pd.DataFrame:
    if uploaded is None:
        return pd.DataFrame()

    name = uploaded.name.lower()
    content = uploaded.read()
    buffer = io.BytesIO(content)

    try:
        if name.endswith(".csv"):
            df = pd.read_csv(buffer)
        elif name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(buffer)
        else:
            st.warning("Unsupported file type. Please upload CSV or Excel.")
            return pd.DataFrame()
    except Exception as exc:  # pragma: no cover - streamlit UI message
        st.error(f"Unable to read file: {exc}")
        return pd.DataFrame()

    return normalize_columns(df)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.rename(columns=lambda col: re.sub(r"[^a-z0-9_]+", "_", col.strip().lower()))
    return clean.loc[:, ~clean.columns.duplicated()]


def ensure_required_columns(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return None
    return df


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    for col in [
        "loan_amount",
        "appraised_value",
        "borrower_income",
        "monthly_debt",
        "interest_rate",
        "principal_balance",
    ]:
        work[col] = standardize_numeric(work[col])
    return work


def render_metrics(df: pd.DataFrame) -> None:
    metrics, enriched = portfolio_kpis(df)
    quality = calculate_quality_score(df)

    st.subheader("Portfolio KPIs")
    cols = st.columns(4)
    cols[0].metric("Delinquency rate", f"{metrics['delinquency_rate']:.2f}%")
    cols[1].metric("Portfolio yield", f"{metrics['portfolio_yield']:.2f}%")
    cols[2].metric("Average LTV", f"{metrics['average_ltv']:.2f}%")
    cols[3].metric("Average DTI", f"{metrics['average_dti']:.2f}")

    st.metric("Data quality score", f"{quality:.0f}/100")

    st.subheader("Projection")
    projection = project_growth(
        current_yield=float(metrics["portfolio_yield"]),
        target_yield=float(metrics["portfolio_yield"] * 1.1),
        current_loan_volume=float(df["principal_balance"].sum()),
        target_loan_volume=float(df["principal_balance"].sum() * 1.2),
    )
    fig = px.line(projection, x="month", y=["yield", "loan_volume"], markers=True)
    apply_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Enriched sample")
    st.dataframe(enriched.head())


def main() -> None:
    st.set_page_config(page_title="ABACO Analytics", layout="wide")
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {ABACO_THEME['colors']['background']}; }}
        .stToolbar {{ border-color: rgba(255, 255, 255, 0.1); }}
        .stMetricLabel {{ color: {ABACO_THEME['colors']['light_gray']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("ABACO Loan Analytics")
    st.write("Upload a portfolio extract to compute governed KPIs and quality signals.")

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xls", "xlsx"])
    df = parse_uploaded_file(uploaded)
    if df.empty:
        st.info("Awaiting data upload.")
        return

    df = ensure_required_columns(df)
    if df is None:
        return

    df = coerce_numeric(df)
    render_metrics(df)


if __name__ == "__main__":
    main()
