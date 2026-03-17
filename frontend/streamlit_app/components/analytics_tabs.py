import pandas as pd
import plotly.express as px
import streamlit as st

from .visualizations import apply_theme, styled_df


def _render_forecasting_tab(dashboard_metrics):
    """Render revenue forecasting visuals."""
    st.subheader("Revenue Forecasting (6M)")
    forecast_rows = dashboard_metrics.get("extended_kpis", {}).get("revenue_forecast_6m", [])
    if not forecast_rows:
        st.info("Forecast data not available. Generate KPI exports from current datasets.")
        return

    forecast_df = pd.DataFrame(forecast_rows)
    forecast_df["month"] = pd.to_datetime(forecast_df["month"], errors="coerce")
    forecast_df = forecast_df.dropna(subset=["month"])

    fig = px.line(
        forecast_df,
        x="month",
        y="forecast_revenue_usd",
        title="Revenue Forecast - Next 6 Months",
        markers=True,
    )
    if {"lower_bound_usd", "upper_bound_usd"}.issubset(forecast_df.columns):
        fig.add_scatter(
            x=forecast_df["month"],
            y=forecast_df["upper_bound_usd"],
            mode="lines",
            name="Upper Bound",
            line={"dash": "dot"},
        )
        fig.add_scatter(
            x=forecast_df["month"],
            y=forecast_df["lower_bound_usd"],
            mode="lines",
            name="Lower Bound",
            line={"dash": "dot"},
            fill="tonexty",
        )
    st.plotly_chart(apply_theme(fig), width="stretch")
    st.dataframe(styled_df(forecast_df), width="stretch")


def _render_opportunity_tab(dashboard_metrics):
    """Render opportunity prioritization table and bars."""
    st.subheader("Opportunity Prioritization")
    opportunity_rows = dashboard_metrics.get("extended_kpis", {}).get(
        "opportunity_prioritization",
        [],
    )
    if not opportunity_rows:
        st.info("Opportunity data not available.")
        return

    opportunity_df = pd.DataFrame(opportunity_rows)
    if {"client_segment", "priority_score"}.issubset(opportunity_df.columns):
        fig = px.bar(
            opportunity_df,
            x="client_segment",
            y="priority_score",
            color="Delinquency_Rate" if "Delinquency_Rate" in opportunity_df.columns else None,
            title="Priority Score by Segment",
        )
        st.plotly_chart(apply_theme(fig), width="stretch")

    st.dataframe(styled_df(opportunity_df), width="stretch")


def _render_churn_tab(dashboard_metrics):
    """Render churn and retention trends."""
    st.subheader("90-Day Churn Analysis")
    churn_data = dashboard_metrics.get("extended_kpis", {}).get("churn_90d_metrics", [])
    if churn_data:
        churn_df = pd.DataFrame(churn_data)
        if "month" in churn_df.columns:
            churn_df["month"] = pd.to_datetime(churn_df["month"], errors="coerce")
            churn_df = churn_df.dropna(subset=["month"])
            fig_churn = px.line(
                churn_df,
                x="month",
                y=["churn90d_pct"],
                title="90-Day Churn Rate Trend",
                markers=True,
            )
            st.plotly_chart(apply_theme(fig_churn), width="stretch")
            st.write("**Churn Metrics Summary:**")
            latest_churn = churn_df.sort_values("month").iloc[-1]
            ch_c1, ch_c2, ch_c3 = st.columns(3)
            ch_c1.metric("Active (90d)", f"{int(latest_churn['active_90d']):,}")
            ch_c2.metric("Inactive (90d)", f"{int(latest_churn['inactive_90d']):,}")
            ch_c3.metric("Churn Rate", f"{latest_churn['churn90d_pct']:.2%}")
            st.dataframe(styled_df(churn_df), width="stretch")
    else:
        st.info("Churn analytics requires historical disbursement or payment data.")


def _render_unit_economics_tab(dashboard_metrics):
    """Render LTV/CAC and margin analytics."""
    st.subheader("LTV / CAC and Margins")
    unit_rows = dashboard_metrics.get("extended_kpis", {}).get("unit_economics", [])
    if not unit_rows:
        st.info("Unit economics data not available.")
        return

    unit_df = pd.DataFrame(unit_rows)
    if "month" in unit_df.columns:
        unit_df["month"] = pd.to_datetime(unit_df["month"], errors="coerce")
        unit_df = unit_df.dropna(subset=["month"])

        if "ltv_cac_ratio" in unit_df.columns:
            fig_ratio = px.line(
                unit_df,
                x="month",
                y="ltv_cac_ratio",
                title="LTV/CAC Ratio Trend",
                markers=True,
            )
            fig_ratio.add_hline(
                y=3.0,
                line_dash="dash",
                line_color="green",
                annotation_text="Target (3.0x)",
            )
            st.plotly_chart(apply_theme(fig_ratio), width="stretch")

        if "gross_margin_pct" in unit_df.columns:
            fig_margin = px.line(
                unit_df,
                x="month",
                y="gross_margin_pct",
                title="Gross Margin Trend",
                markers=True,
            )
            st.plotly_chart(apply_theme(fig_margin), width="stretch")

    st.dataframe(styled_df(unit_df), width="stretch")


def _render_pricing_governance_tab(dashboard_metrics):
    """Render pricing stack and governance quality."""
    st.subheader("Pricing Analytics & Data Governance")

    pricing = dashboard_metrics.get("extended_kpis", {}).get("pricing_analytics", {})
    current_pricing = pricing.get("current", {}) if isinstance(pricing, dict) else {}

    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("Weighted APR", f"{current_pricing.get('weighted_apr', 0.0):.2%}")
    pc2.metric("Weighted Fee Rate", f"{current_pricing.get('weighted_fee_rate', 0.0):.2%}")
    pc3.metric(
        "Weighted Effective Rate",
        f"{current_pricing.get('weighted_effective_rate', 0.0):.2%}",
    )

    pricing_monthly = pricing.get("monthly", []) if isinstance(pricing, dict) else []
    if pricing_monthly:
        pricing_df = pd.DataFrame(pricing_monthly)
        if "month" in pricing_df.columns:
            pricing_df["month"] = pd.to_datetime(pricing_df["month"], errors="coerce")
            pricing_df = pricing_df.dropna(subset=["month"])
            fig_price = px.line(
                pricing_df,
                x="month",
                y=["weighted_apr", "weighted_effective_rate"],
                title="Pricing Trend",
                markers=True,
            )
            st.plotly_chart(apply_theme(fig_price), width="stretch")

    governance = dashboard_metrics.get("extended_kpis", {}).get("data_governance", {})
    if governance:
        st.markdown("### Data Quality & Governance")
        g1, g2, g3 = st.columns(3)
        g1.metric("Quality Score", f"{governance.get('quality_score', 0.0):.1%}")
        freshness = governance.get("freshness_days")
        g2.metric("Freshness (days)", "N/A" if freshness is None else f"{freshness}")
        g3.metric("Status", str(governance.get("governance_status", "unknown")).upper())

        completeness = governance.get("completeness", {})
        if completeness:
            st.dataframe(
                styled_df(
                    pd.DataFrame(list(completeness.items()), columns=["Field", "Completeness"])
                ),
                width="stretch",
            )


def render_advanced_intelligence(dashboard_metrics):
    """Render the advanced analytics tabs."""
    st.markdown('<div data-testid="dashboard-analytics">', unsafe_allow_html=True)
    st.header("🔬 Advanced Intelligence")

    strategic = dashboard_metrics.get("extended_kpis", {}).get("strategic_confirmations", {})
    if strategic:
        st.markdown("### Strategic Confirmations")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CAC", "✅" if strategic.get("cac_confirmed") else "❌")
        c2.metric("LTV", "✅" if strategic.get("ltv_confirmed") else "❌")
        c3.metric("Margins", "✅" if strategic.get("margin_confirmed") else "❌")
        c4.metric(
            "Revenue Forecast",
            "✅" if strategic.get("revenue_forecast_confirmed") else "❌",
        )

    adv_tabs = st.tabs(
        [
            "Forecasting",
            "Opportunity",
            "Churn & Retention",
            "Unit Economics",
            "Pricing & Governance",
        ]
    )
    with adv_tabs[0]:
        _render_forecasting_tab(dashboard_metrics)
    with adv_tabs[1]:
        _render_opportunity_tab(dashboard_metrics)
    with adv_tabs[2]:
        _render_churn_tab(dashboard_metrics)
    with adv_tabs[3]:
        _render_unit_economics_tab(dashboard_metrics)
    with adv_tabs[4]:
        _render_pricing_governance_tab(dashboard_metrics)
