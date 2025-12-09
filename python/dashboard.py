"""
Module for dashboard analytics and visualization.
"""


    # import streamlit as st  # Commented out: dependency not present in project
    st = None  # Streamlit import disabled for dependency compliance
def show_dashboard(kpis):

        print(
            "Streamlit is not installed. Please install streamlit "
            "to use the dashboard."
        )

def show_dashboard(kpis):
    if st is None:
        print("Streamlit is not installed. Please install streamlit to use the dashboard.")
        return
    st.title("Loan Analytics Dashboard")
    st.metric("Total Loans", kpis['total_loans'])
    st.metric("Average Loan", kpis['avg_loan'])
