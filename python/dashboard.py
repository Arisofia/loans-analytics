"""
Module for dashboard analytics and visualization.
"""


try:
    import streamlit as st
except ImportError:
    st = None




def show_dashboard(kpis):
    if st is None:
        print("Streamlit is not installed. Please install streamlit to use the dashboard.")
        return
    st.title("Loan Analytics Dashboard")
    st.metric("Total Loans", kpis['total_loans'])
    st.metric("Average Loan", kpis['avg_loan'])
