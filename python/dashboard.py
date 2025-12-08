import streamlit as st

def show_dashboard(kpis):
    st.title("Loan Analytics Dashboard")
    st.metric("Total Loans", kpis['total_loans'])
    st.metric("Average Loan", kpis['avg_loan'])
