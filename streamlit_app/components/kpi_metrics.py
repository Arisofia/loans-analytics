import streamlit as st
import pandas as pd
from src.utils.dashboard_utils import format_kpi_value, kpi_label

def render_kpi_snapshot(kpi_snapshot, snapshot_month=None):
    """Render the top KPI snapshot tiles."""
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

def render_executive_summary(merged):
    """Render the executive summary metrics."""
    st.markdown('<div data-testid="dashboard-board">', unsafe_allow_html=True)
    st.header("📊 Executive Summary")
    col1, col2, col3, col4 = st.columns(4)

    total_loans = merged["loan_id"].nunique() if "loan_id" in merged else 0
    total_outstanding = (
        merged["outstanding_loan_value"].sum() if "outstanding_loan_value" in merged else 0
    )
    
    # Calculate weighted average APR
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
    st.markdown('<div data-testid="kpi-total-loans">', unsafe_allow_html=True)
    col2.metric("Total Outstanding", f"${total_outstanding:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)
    col3.metric("Average APR", f"{avg_apr:.2%}")
    col4.metric("Default Rate", f"{default_rate:.2f}%")

    st.markdown('</div>', unsafe_allow_html=True)
    return total_outstanding
