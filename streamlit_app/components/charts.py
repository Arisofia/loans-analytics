import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from python.utils.dashboard import compute_cat_agg, format_kpi_value  # noqa: E402

from .visualizations import apply_theme  # noqa: E402


def render_cashflow_trends(analytics_facts):
    """Render cashflow trend charts and metrics."""
    if not analytics_facts.empty:
        st.markdown('<div data-testid="dashboard-cfo">', unsafe_allow_html=True)
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
            st.markdown('<div data-testid="chart-revenue">', unsafe_allow_html=True)
            st.plotly_chart(apply_theme(fig_cash), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            latest_cash = cash_df.sort_values("month").iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            if "recv_revenue_for_month" in latest_cash:
                c1.metric(
                    "Revenue (Received)",
                    format_kpi_value(
                        "recv_revenue_for_month", latest_cash["recv_revenue_for_month"]
                    ),
                )
            if "recv_interest_for_month" in latest_cash:
                c2.metric(
                    "Interest (Received)",
                    format_kpi_value(
                        "recv_interest_for_month",
                        latest_cash["recv_interest_for_month"],
                    ),
                )
            if "recv_fee_for_month" in latest_cash:
                c3.metric(
                    "Fees (Received)",
                    format_kpi_value(
                        "recv_fee_for_month",
                        latest_cash["recv_fee_for_month"],
                    ),
                )
            if "sched_revenue" in latest_cash:
                c4.metric(
                    "Revenue (Scheduled)",
                    format_kpi_value("sched_revenue", latest_cash["sched_revenue"]),
                )
            st.markdown("</div>", unsafe_allow_html=True)


def render_growth_analysis(total_outstanding):
    """Render growth projections and category breakdown."""
    st.markdown('<div data-testid="dashboard-growth">', unsafe_allow_html=True)
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
            df_proj,
            x="Month",
            y="Projected",
            title="12-Month Portfolio Growth Projection",
        )
        st.plotly_chart(apply_theme(fig_growth), use_container_width=True)
    return g_col2


def render_category_breakdown(merged, col):
    """Render the category breakdown pie chart."""
    with col:
        try:
            cat_agg = compute_cat_agg(merged)
            if not cat_agg.empty and cat_agg["outstanding_loan_value"].sum() > 0:
                fig_cat = px.pie(
                    cat_agg,
                    values="outstanding_loan_value",
                    names="categoria",
                    title="Portfolio by Category",
                )
                st.plotly_chart(apply_theme(fig_cat), use_container_width=True)
            else:
                if "categoria" in merged.columns and "outstanding_loan_value" not in merged.columns:
                    st.info(
                        "Outstanding loan value column missing. Category breakdown unavailable."
                    )
                else:
                    st.info("No outstanding balance data found for category breakdown.")
        except (ValueError, KeyError) as exc:
            st.warning(f"Could not generate category breakdown: {exc}")
