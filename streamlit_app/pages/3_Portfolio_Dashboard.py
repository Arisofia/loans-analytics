"""
Enhanced Loans Analytics Dashboard - Main Application

Complete dashboard with:
- CSV/Excel upload with validation
- Key metrics display
- Interactive visualizations
- Loan table with drill-down
- Export functionality
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from python.multi_agent.guardrails import Guardrails
from python.multi_agent.orchestrator import MultiAgentOrchestrator
from python.multi_agent.protocol import LLMProvider

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Page configuration
st.set_page_config(
    page_title="Abaco Loans Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .status-current { background-color: #28a745; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .status-delinquent { background-color: #ffc107; color: black; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .status-default { background-color: #dc3545; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .status-paid-off { background-color: #17a2b8; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
</style>
""", unsafe_allow_html=True)

# Required columns for loan data
REQUIRED_COLUMNS = [
    "loan_id",
    "borrower_name",
    "borrower_email",
    "borrower_id_number",
    "principal_amount",
    "interest_rate",
    "term_months",
    "origination_date",
    "current_status",
    "payment_history_json",
    "risk_score",
    "region"
]


def validate_uploaded_data(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate uploaded data has all required columns."""
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return len(missing_columns) == 0, missing_columns


def parse_payment_history(payment_history_json: str) -> list[dict[str, Any]]:
    """Parse payment history from JSON string."""
    try:
        return json.loads(payment_history_json)
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_days_past_due(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate days past due (DPD) for each loan."""
    df = df.copy()

    def get_dpd(row):
        """Calculate DPD from payment history."""
        payment_history = parse_payment_history(row["payment_history_json"])
        if not payment_history:
            return 0

        # Get unpaid/late payments
        overdue_days = [
            p["days_late"]
            for p in payment_history
            if p["status"] in ["missed", "defaulted"]
            or (p["status"] == "late_paid" and p["days_late"] > 30)
        ]

        return max(overdue_days) if overdue_days else 0

    df["days_past_due"] = df.apply(get_dpd, axis=1)
    return df


def calculate_portfolio_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate key portfolio metrics."""
    # Total portfolio value
    total_portfolio = df["principal_amount"].sum()

    # Weighted average rate
    total_principal = df["principal_amount"].sum()
    weighted_rate = (
        (df["principal_amount"] * df["interest_rate"]).sum() / total_principal
        if total_principal > 0
        else 0
    )

    # Calculate DPD
    df = calculate_days_past_due(df)

    # Delinquency rates
    total_loans = len(df)
    dpd_30_plus = len(df[df["days_past_due"] >= 30])
    dpd_60_plus = len(df[df["days_past_due"] >= 60])
    dpd_90_plus = len(df[df["days_past_due"] >= 90])

    delinquency_rate_30 = (dpd_30_plus / total_loans * 100) if total_loans > 0 else 0
    delinquency_rate_60 = (dpd_60_plus / total_loans * 100) if total_loans > 0 else 0
    delinquency_rate_90 = (dpd_90_plus / total_loans * 100) if total_loans > 0 else 0

    # PAR (Portfolio at Risk) > 30
    par_30_amount = df[df["days_past_due"] >= 30]["principal_amount"].sum()
    par_30_rate = (par_30_amount / total_portfolio * 100) if total_portfolio > 0 else 0

    # Expected loss (simplified: average risk score * portfolio)
    expected_loss = (df["risk_score"] * df["principal_amount"]).sum()
    expected_loss_rate = (expected_loss / total_portfolio * 100) if total_portfolio > 0 else 0

    # Status distribution
    status_dist = df["current_status"].value_counts().to_dict()

    return {
        "total_portfolio": total_portfolio,
        "weighted_avg_rate": weighted_rate,
        "delinquency_rate_30": delinquency_rate_30,
        "delinquency_rate_60": delinquency_rate_60,
        "delinquency_rate_90": delinquency_rate_90,
        "par_30_rate": par_30_rate,
        "expected_loss": expected_loss,
        "expected_loss_rate": expected_loss_rate,
        "total_loans": total_loans,
        "status_distribution": status_dist,
        "avg_loan_size": df["principal_amount"].mean(),
        "avg_risk_score": df["risk_score"].mean(),
    }


def render_metrics_cards(metrics: dict[str, Any]):
    """Render key metrics in cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Total Portfolio Value",
            value=f"€{metrics['total_portfolio']:,.0f}",
            delta=f"{metrics['total_loans']} loans"
        )

    with col2:
        st.metric(
            label="📊 Weighted Avg Rate",
            value=f"{metrics['weighted_avg_rate']:.2%}",
            delta=f"Avg: €{metrics['avg_loan_size']:,.0f}",
        )

    with col3:
        st.metric(
            label="⚠️ Delinquency Rate (30+ DPD)",
            value=f"{metrics['delinquency_rate_30']:.1f}%",
            delta=f"60+: {metrics['delinquency_rate_60']:.1f}%",
            delta_color="inverse"
        )

    with col4:
        st.metric(
            label="🎯 PAR > 30",
            value=f"{metrics['par_30_rate']:.2f}%",
            delta=f"Expected Loss: {metrics['expected_loss_rate']:.2f}%",
            delta_color="inverse"
        )


def create_delinquency_trend(df: pd.DataFrame) -> go.Figure:
    """Create delinquency trend line chart."""
    df = df.copy()
    df["origination_date"] = pd.to_datetime(df["origination_date"])
    df = calculate_days_past_due(df)

    # Group by month
    df["origination_month"] = df["origination_date"].dt.to_period("M").astype(str)

    # Calculate delinquency rates by cohort
    cohort_data = []
    for month in sorted(df["origination_month"].unique()):
        cohort = df[df["origination_month"] == month]
        total = len(cohort)
        dpd_30 = len(cohort[cohort["days_past_due"] >= 30])
        dpd_60 = len(cohort[cohort["days_past_due"] >= 60])
        dpd_90 = len(cohort[cohort["days_past_due"] >= 90])

        cohort_data.append(
            {
                "month": month,
                "DPD 30+": (dpd_30 / total * 100) if total > 0 else 0,
                "DPD 60+": (dpd_60 / total * 100) if total > 0 else 0,
                "DPD 90+": (dpd_90 / total * 100) if total > 0 else 0,
            }
        )

    cohort_df = pd.DataFrame(cohort_data)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=cohort_df["month"],
            y=cohort_df["DPD 30+"],
            name="30+ Days",
            mode="lines+markers",
            line={"color": "#ffc107", "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=cohort_df["month"],
            y=cohort_df["DPD 60+"],
            name="60+ Days",
            mode="lines+markers",
            line={"color": "#ff9800", "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=cohort_df["month"],
            y=cohort_df["DPD 90+"],
            name="90+ Days",
            mode="lines+markers",
            line={"color": "#dc3545", "width": 2},
        )
    )

    fig.update_layout(
        title="Delinquency Trend by Origination Cohort",
        xaxis_title="Origination Month",
        yaxis_title="Delinquency Rate (%)",
        hovermode="x unified",
        height=400,
    )

    return fig


def create_risk_distribution(df: pd.DataFrame) -> go.Figure:
    """Create risk score distribution histogram."""
    fig = px.histogram(
        df,
        x="risk_score",
        nbins=20,
        title="Risk Score Distribution",
        labels={"risk_score": "Risk Score", "count": "Number of Loans"},
        color_discrete_sequence=["#667eea"],
    )

    fig.update_layout(
        xaxis_title="Risk Score",
        yaxis_title="Number of Loans",
        height=400,
        showlegend=False,
    )

    return fig


def build_agent_portfolio_context(df: pd.DataFrame) -> dict[str, Any]:
    """Build sanitized portfolio context for multi-agent analysis."""
    metrics = calculate_portfolio_metrics(df)
    status_counts = (
        df["current_status"].value_counts(dropna=False).to_dict()
        if "current_status" in df.columns
        else {}
    )
    region_counts = (
        df["region"].value_counts(dropna=False).head(10).to_dict()
        if "region" in df.columns
        else {}
    )

    def to_native(value: Any) -> Any:
        if isinstance(value, (int, float, str)) or value is None:
            return value
        if hasattr(value, "item"):
            return value.item()
        return float(value) if isinstance(value, (int, float)) else str(value)

    portfolio_data = {
        "total_loans": int(metrics.get("total_loans", 0)),
        "total_portfolio": to_native(metrics.get("total_portfolio", 0)),
        "avg_interest_rate": to_native(metrics.get("avg_interest_rate", 0)),
        "delinquency_rate_30": to_native(metrics.get("delinquency_rate_30", 0)),
        "delinquency_rate_60": to_native(metrics.get("delinquency_rate_60", 0)),
        "delinquency_rate_90": to_native(metrics.get("delinquency_rate_90", 0)),
        "status_distribution": {k: int(v) for k, v in status_counts.items()},
        "top_regions": {k: int(v) for k, v in region_counts.items()},
    }

    return Guardrails.sanitize_context({"portfolio_data": portfolio_data})


def create_regional_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create regional concentration heatmap for Spanish regions."""
    # Calculate metrics by region
    regional_data = (
        df.groupby("region")
        .agg({"principal_amount": ["sum", "count"], "risk_score": "mean"})
        .reset_index()
    )

    regional_data.columns = ["region", "total_amount", "loan_count", "avg_risk"]
    regional_data["concentration"] = (
        regional_data["total_amount"] / regional_data["total_amount"].sum() * 100
    )

    # Sort by concentration
    regional_data = regional_data.sort_values("concentration", ascending=False)

    fig = px.bar(
        regional_data.head(10),
        x="region",
        y="concentration",
        color="avg_risk",
        title="Top 10 Regions by Portfolio Concentration",
        labels={"concentration": "Portfolio %", "avg_risk": "Avg Risk", "region": "Region"},
        color_continuous_scale="RdYlGn_r",
        text="concentration",
    )

    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(height=400, xaxis_tickangle=-45)

    return fig


def create_vintage_analysis(df: pd.DataFrame) -> go.Figure:
    """Create vintage analysis visualization."""
    df = df.copy()
    df["origination_date"] = pd.to_datetime(df["origination_date"])
    df["origination_quarter"] = df["origination_date"].dt.to_period("Q").astype(str)

    vintage_data = (
        df.groupby(["origination_quarter", "current_status"]).size().unstack(fill_value=0)
    )
    vintage_pct = vintage_data.div(vintage_data.sum(axis=1), axis=0) * 100

    fig = go.Figure()

    status_colors = {
        "current": "#28a745",
        "paid-off": "#17a2b8",
        "delinquent": "#ffc107",
        "default": "#dc3545",
    }

    for status in vintage_pct.columns:
        fig.add_trace(
            go.Bar(
                name=status.title(),
                x=vintage_pct.index,
                y=vintage_pct[status],
                marker_color=status_colors.get(status, "#6c757d"),
            )
        )

    fig.update_layout(
        title="Vintage Analysis - Loan Status by Origination Quarter",
        xaxis_title="Origination Quarter",
        yaxis_title="Percentage (%)",
        barmode="stack",
        height=400,
        hovermode="x unified",
    )

    return fig


def render_loan_table(df: pd.DataFrame):
    """Render interactive loan table with filters."""
    st.subheader("📋 Loan Portfolio - Detailed View")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.multiselect(
            "Status",
            options=df["current_status"].unique().tolist(),
            default=df["current_status"].unique().tolist(),
        )

    with col2:
        regions = sorted(df["region"].unique().tolist())
        region_filter = st.multiselect(
            "Region",
            options=regions,
            default=[],
        )

    with col3:
        min_amount = float(df["principal_amount"].min())
        max_amount = float(df["principal_amount"].max())
        amount_range = st.slider(
            "Principal Amount (€)",
            min_value=min_amount,
            max_value=max_amount,
            value=(min_amount, max_amount),
            format="€%.0f",
        )

    with col4:
        search_term = st.text_input("🔍 Search (Loan ID or Borrower)", "")

    # Apply filters
    filtered_df = df[df["current_status"].isin(status_filter)]

    if region_filter:
        filtered_df = filtered_df[filtered_df["region"].isin(region_filter)]

    filtered_df = filtered_df[
        (filtered_df["principal_amount"] >= amount_range[0])
        & (filtered_df["principal_amount"] <= amount_range[1])
    ]

    if search_term:
        filtered_df = filtered_df[
            filtered_df["loan_id"].str.contains(search_term, case=False)
            | filtered_df["borrower_name"].str.contains(search_term, case=False)
        ]

    # Display count
    st.info(f"Showing {len(filtered_df)} of {len(df)} loans")

    # Prepare display dataframe
    display_df = filtered_df[
        [
            "loan_id",
            "borrower_name",
            "region",
            "principal_amount",
            "interest_rate",
            "term_months",
            "origination_date",
            "current_status",
            "risk_score",
        ]
    ].copy()

    display_df["principal_amount"] = display_df["principal_amount"].apply(
        lambda x: f"€{x:,.2f}"
    )
    display_df["interest_rate"] = display_df["interest_rate"].apply(lambda x: f"{x:.2%}")
    display_df["risk_score"] = display_df["risk_score"].apply(lambda x: f"{x:.4f}")

    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "loan_id": st.column_config.TextColumn("Loan ID", width="small"),
            "borrower_name": st.column_config.TextColumn("Borrower", width="medium"),
            "region": st.column_config.TextColumn("Region", width="medium"),
            "principal_amount": st.column_config.TextColumn("Principal", width="small"),
            "interest_rate": st.column_config.TextColumn("Rate", width="small"),
            "term_months": st.column_config.NumberColumn("Term (mo)", width="small"),
            "origination_date": st.column_config.DateColumn("Orig. Date", width="small"),
            "current_status": st.column_config.TextColumn("Status", width="small"),
            "risk_score": st.column_config.TextColumn("Risk", width="small"),
        }
    )

    # Export buttons
    col1, col2 = st.columns([1, 5])
    with col1:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export CSV",
            data=csv,
            file_name=f"loan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


# Main app
def main():
    st.markdown('<p class="main-header">📊 Abaco Loans Analytics Dashboard</p>', unsafe_allow_html=True)

    # Sidebar - File upload
    with st.sidebar:
        st.header("📤 Upload Loan Data")

        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="Upload a CSV file with loan data. Required columns: "
            + ", ".join(REQUIRED_COLUMNS[:6])
            + "...",
        )

        # Quick load sample data
        if st.button("📂 Load Sample Data (Spanish Loans)"):
            sample_file = ROOT_DIR / "data" / "raw" / "spanish_loans_seed.csv"
            if sample_file.exists():
                st.session_state["data_loaded"] = True
                st.session_state["loan_data"] = pd.read_csv(sample_file)
                st.success("✅ Sample data loaded!")
                st.rerun()
            else:
                st.error("Sample file not found. Run: `python scripts/seed_spanish_loans.py`")

        st.markdown("---")

        # Agent Analysis
        st.header("🤖 AI Analysis")
        if st.button("🔍 Run Agent Analysis"):
            if not st.session_state.get("data_loaded"):
                st.warning("Please upload data before running agent analysis.")
            elif not os.getenv("OPENAI_API_KEY"):
                st.warning("OPENAI_API_KEY is not set. Please configure it to run agents.")
            else:
                with st.spinner("Running multi-agent analysis..."):
                    try:
                        df = st.session_state.get("loan_data")
                        context = build_agent_portfolio_context(df)
                        orchestrator = MultiAgentOrchestrator(
                            provider=LLMProvider.OPENAI,
                            enable_tracing=False,
                        )
                        results = orchestrator.run_scenario(
                            "loan_risk_review",
                            context,
                        )
                        st.session_state["agent_results"] = results
                        st.success("✅ Agent analysis completed")
                    except Exception as exc:  # pylint: disable=broad-except
                        st.error(f"❌ Agent analysis failed: {exc}")

        st.markdown("---")
        st.caption("💡 Upload your own CSV or load sample Spanish loan data")
    
    # Handle file upload
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            valid, missing_cols = validate_uploaded_data(df)

            if valid:
                st.session_state["data_loaded"] = True
                st.session_state["loan_data"] = df
                st.success("✅ Data uploaded and validated successfully!")
            else:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                st.info(f"Required columns: {', '.join(REQUIRED_COLUMNS)}")
                return
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            return

    # Check if data is loaded
    if (
        "data_loaded" not in st.session_state
        or not st.session_state["data_loaded"]
    ):
        st.info(
            "👆 Please upload a CSV file or load sample data from the sidebar to begin analysis"
        )

        st.markdown("### 📋 Required Data Format")
        st.markdown("Your CSV file must include these columns:")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Borrower Information:**")
            st.markdown("- `loan_id`")
            st.markdown("- `borrower_name`")
            st.markdown("- `borrower_email`")
            st.markdown("- `borrower_id_number`")
            st.markdown("- `region`")

        with col2:
            st.markdown("**Loan Details:**")
            st.markdown("- `principal_amount`")
            st.markdown("- `interest_rate`")
            st.markdown("- `term_months`")
            st.markdown("- `origination_date`")
            st.markdown("- `current_status`")
            st.markdown("- `payment_history_json`")
            st.markdown("- `risk_score`")

        return

    # Load data
    df = st.session_state["loan_data"]

    # Calculate metrics
    metrics = calculate_portfolio_metrics(df)

    # Display metrics
    st.markdown("### 📊 Key Portfolio Metrics")
    render_metrics_cards(metrics)

    if "agent_results" in st.session_state:
        st.markdown("### 🤖 AI Analysis Results")
        results = st.session_state.get("agent_results", {})
        with st.expander("View multi-agent outputs", expanded=True):
            if results.get("risk_analysis"):
                st.markdown("**Risk Analysis**")
                st.write(results["risk_analysis"])
            if results.get("compliance_review"):
                st.markdown("**Compliance Review**")
                st.write(results["compliance_review"])
            if results.get("ops_recommendations"):
                st.markdown("**Ops Recommendations**")
                st.write(results["ops_recommendations"])
            metadata = results.get("_metadata")
            if metadata:
                st.caption(f"Trace ID: {metadata.get('trace_id', 'n/a')}")

    st.markdown("---")

    # Visualizations
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📈 Delinquency Trends",
            "📊 Risk Distribution",
            "🗺️ Regional Analysis",
            "📅 Vintage Analysis",
            "📋 Loan Table",
        ]
    )
    
    with tab1:
        st.plotly_chart(create_delinquency_trend(df), use_container_width=True)

        # Additional delinquency metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("DPD 30+", f"{metrics['delinquency_rate_30']:.1f}%")
        with col2:
            st.metric("DPD 60+", f"{metrics['delinquency_rate_60']:.1f}%")
        with col3:
            st.metric("DPD 90+", f"{metrics['delinquency_rate_90']:.1f}%")

    with tab2:
        st.plotly_chart(create_risk_distribution(df), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Risk Score", f"{metrics['avg_risk_score']:.4f}")
        with col2:
            st.metric("Expected Loss", f"€{metrics['expected_loss']:,.0f}")

    with tab3:
        st.plotly_chart(create_regional_heatmap(df), use_container_width=True)

        st.markdown("#### Regional Distribution")
        regional_summary = df.groupby("region").agg(
            {
                "principal_amount": "sum",
                "loan_id": "count",
                "risk_score": "mean",
            }
        ).round(2)
        regional_summary.columns = ["Total Amount (€)", "Loan Count", "Avg Risk"]
        regional_summary = regional_summary.sort_values(
            "Total Amount (€)", ascending=False
        )
        st.dataframe(regional_summary, use_container_width=True)

    with tab4:
        st.plotly_chart(create_vintage_analysis(df), use_container_width=True)

        st.markdown("#### Status Distribution")
        status_counts = df["current_status"].value_counts()
        status_pct = (status_counts / len(df) * 100).round(1)

        col1, col2, col3, col4 = st.columns(4)
        for i, (status, count) in enumerate(status_counts.items()):
            col = [col1, col2, col3, col4][i % 4]
            with col:
                st.metric(
                    status.title(),
                    f"{count} ({status_pct[status]:.1f}%)",
                )

    with tab5:
        render_loan_table(df)


if __name__ == "__main__":
    main()
