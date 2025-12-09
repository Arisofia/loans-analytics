
"""
Dashboard analytics and visualization module.
"""


def show_dashboard(kpis):
    """
    Display the loan analytics dashboard using Streamlit or fallback to print.
    """
    if st is None:
        print(
            "Streamlit is not installed. Please install streamlit to use the "
            "dashboard."
        )
        return
    st.title("Loan Analytics Dashboard")
    st.metric("Total Loans", kpis['total_loans'])
    st.metric("Average Loan", kpis['avg_loan'])
