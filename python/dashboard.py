"""
Dashboard analytics and visualization module.
"""

try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover - fallback for test environments
    class _StubStreamlit:
        """Lightweight stub so tests can patch .st without importing streamlit."""

        def title(self, *_args, **_kwargs):
            return None

        def metric(self, *_args, **_kwargs):
            return None

    st = _StubStreamlit()


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
    st.metric("Total Loans", kpis.get('total_loans', 0))
    st.metric("Average Loan", kpis.get('avg_loan', 0))
