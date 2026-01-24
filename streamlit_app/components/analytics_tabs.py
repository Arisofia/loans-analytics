import pandas as pd
import plotly.express as px
import streamlit as st


from .visualizations import apply_theme, styled_df


def render_advanced_intelligence(dashboard_metrics):
    """Render the advanced analytics tabs."""
    st.markdown('<div data-testid="dashboard-analytics">', unsafe_allow_html=True)
    st.header("🔬 Advanced Intelligence")
    adv_tabs = st.tabs(["Segmentation", "Churn & Retention", "Unit Economics"])

    with adv_tabs[0]:
        st.subheader("Client Segment Distribution (2025)")
        seg_data = dashboard_metrics.get("extended_kpis", {}).get("segmentation_summary", [])
        if seg_data:
            df_seg = pd.DataFrame(seg_data)
            df_seg_display = df_seg.rename(
                columns={
                    "client_segment": "Segment",
                    "Clients": "Active Clients",
                    "Portfolio_Value": "Portfolio Value ($)",
                    "Avg_Loan": "Avg Loan Size ($)",
                    "Delinquency_Rate": "Delinquency (%)",
                }
            )

            c1, c2 = st.columns([1, 1])
            with c1:
                fig_seg_aum = px.bar(
                    df_seg_display,
                    x="Segment",
                    y="Portfolio Value ($)",
                    title="AUM by Segment",
                    text_auto=".2s",
                )
                st.plotly_chart(apply_theme(fig_seg_aum), use_container_width=True)
            with c2:
                fig_seg_risk = px.bar(
                    df_seg_display,
                    x="Segment",
                    y="Delinquency (%)",
                    title="Risk by Segment",
                    color="Delinquency (%)",
                    color_continuous_scale="Reds",
                )
                st.plotly_chart(apply_theme(fig_seg_risk), use_container_width=True)

            st.dataframe(styled_df(df_seg_display), use_container_width=True)
        else:
            st.info(
                "Segmentation data not found. Ensure 'Client Segment' column is present in loans data."
            )

    with adv_tabs[1]:
        st.subheader("90-Day Churn Analysis")
        churn_data = dashboard_metrics.get("extended_kpis", {}).get("churn_90d_metrics", [])
        if churn_data:
            df_churn = pd.DataFrame(churn_data)
            if "month" in df_churn.columns:
                df_churn["month"] = pd.to_datetime(df_churn["month"])
                fig_churn = px.line(
                    df_churn,
                    x="month",
                    y=["churn90d_pct"],
                    title="90-Day Churn Rate Trend",
                    markers=True,
                )
                st.plotly_chart(apply_theme(fig_churn), use_container_width=True)

                st.write("**Churn Metrics Summary:**")
                latest_churn = df_churn.sort_values("month").iloc[-1]
                ch_c1, ch_c2, ch_c3 = st.columns(3)
                ch_c1.metric("Active (90d)", f"{latest_churn['active_90d']:,}")
                ch_c2.metric("Inactive (90d)", f"{latest_churn['inactive_90d']:,}")
                ch_c3.metric("Churn Rate", f"{latest_churn['churn90d_pct']:.2%}")
        else:
            st.info("Churn analytics requires historical disbursement data.")

    with adv_tabs[2]:
        st.subheader("LTV / CAC Efficiency")
        ue_data = dashboard_metrics.get("extended_kpis", {}).get("unit_economics", [])
        if ue_data:
            df_ue = pd.DataFrame(ue_data)
            if "month" in df_ue.columns:
                df_ue["month"] = pd.to_datetime(df_ue["month"])
                fig_ue = px.line(
                    df_ue,
                    x="month",
                    y="ltv_cac_ratio",
                    title="LTV/CAC Ratio Trend",
                    markers=True,
                )
                fig_ue.add_hline(
                    y=3.0,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="Target (3.0x)",
                )
                st.plotly_chart(apply_theme(fig_ue), use_container_width=True)
        else:
            st.info(
                "Unit economics requires marketing spend data (data/support/marketing_spend.csv)."
            )
