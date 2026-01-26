import pandas as pd
import plotly.express as px
import streamlit as st

from .visualizations import apply_theme


def render_sales_performance(merged, load_agent_headcount):
    """Render sales performance charts or team capacity."""
    st.header("🎯 Sales Performance")
    if "sales_agent" in merged.columns:
        agg_map = {"loan_id": "count"}
        if "outstanding_loan_value" in merged.columns:
            agg_map["outstanding_loan_value"] = "sum"

        sales_agg = merged.groupby("sales_agent").agg(agg_map).reset_index()

        if "outstanding_loan_value" in merged.columns:
            sales_agg = sales_agg.rename(
                columns={"outstanding_loan_value": "Volume", "loan_id": "Count"}
            )
            fig_sales = px.treemap(
                sales_agg,
                path=["sales_agent"],
                values="Volume",
                color="Count",
                title="Sales Agent Volume Distribution",
            )
        else:
            sales_agg = sales_agg.rename(columns={"loan_id": "Count"})
            fig_sales = px.bar(
                sales_agg, x="sales_agent", y="Count", title="Sales Agent Loan Count"
            )
        st.plotly_chart(apply_theme(fig_sales), use_container_width=True)
    else:
        headcount_df = load_agent_headcount()
        if not headcount_df.empty and {"month", "function", "fte_count"}.issubset(
            headcount_df.columns
        ):
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


def render_risk_analysis(merged):
    """Render risk analysis charts and metrics."""
    st.markdown('<div data-testid="dashboard-risk">', unsafe_allow_html=True)
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
        total_outstanding = (
            merged["outstanding_loan_value"].sum() if "outstanding_loan_value" in merged else 0
        )
        if total_outstanding == 0:
            score -= 40
        if "interest_rate_apr" not in merged.columns:
            score -= 20
        st.metric("Quality Score", f"{score:.1f}%")

    st.markdown("</div>", unsafe_allow_html=True)
