import io
import re
from typing import Optional

import numpy as np
import pandas as pd
try:
    import plotly.express as px
except ImportError as e:
    raise ImportError(
        "plotly.express could not be imported. Ensure 'plotly' is installed in your environment."
    ) from e
import streamlit as st

from src.analytics_metrics import calculate_quality_score, portfolio_kpis, project_growth, standardize_numeric

REQUIRED_COLUMNS = [
    "loan_amount",
    "appraised_value",
    "borrower_income",
    "monthly_debt",
    "loan_status",
    "interest_rate",
    "principal_balance",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and snake-case incoming column names."""

    clean = df.rename(columns=lambda col: re.sub(r"[^a-z0-9_]+", "_", col.strip().lower()))
    return clean.loc[:, ~clean.columns.duplicated()]


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


def ensure_required_columns(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return None
    return df


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    for col in ["loan_amount", "appraised_value", "borrower_income", "monthly_debt", "interest_rate", "principal_balance"]:
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
    fig = px.line(projection, x="date", y=["yield", "loan_volume"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Enriched sample")
    st.dataframe(enriched.head())


def main() -> None:
    st.set_page_config(page_title="ABACO Analytics", layout="wide")
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
