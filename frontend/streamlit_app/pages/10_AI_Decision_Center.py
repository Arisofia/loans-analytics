"""10 — AI Decision Center (First Live Slice)."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="AI Decision Center", page_icon="🎯", layout="wide")


def main() -> None:
    st.title("🎯 AI Decision Center")
    st.info("Run the pipeline to populate this page.")

    tab_metrics, tab_alerts, tab_actions, tab_opps = st.tabs(
        ["Executive Metrics", "Alerts", "Actions", "Opportunities"]
    )

    with tab_metrics:
        st.write("_No metrics yet — run `run_decision_slice` first._")

    with tab_alerts:
        st.write("_No alerts._")

    with tab_actions:
        st.write("_No actions._")

    with tab_opps:
        st.write("_No opportunities._")


main()
