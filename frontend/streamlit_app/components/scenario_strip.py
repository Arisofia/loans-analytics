"""Scenario comparison strip — side-by-side scenario cards."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st


def render_scenario_strip(scenarios: List[Dict[str, Any]]) -> None:
    """Render scenario results as side-by-side cards."""
    if not scenarios:
        st.info("No scenario results available.")
        return

    cols = st.columns(len(scenarios))
    for col, sc in zip(cols, scenarios):
        with col:
            label = sc.get("scenario", "unknown").replace("_", " ").title()
            st.subheader(label)

            # Triggers
            triggers = sc.get("triggers", [])
            if triggers:
                for tr in triggers:
                    st.markdown(f"⚡ {tr}")

            # Narrative
            narrative = sc.get("narrative", "")
            if narrative:
                st.caption(narrative)

            # Projected metrics (top 5)
            projected = sc.get("projected_metrics", {})
            if projected:
                for k, v in list(projected.items())[:5]:
                    st.metric(label=k, value=f"{v:,.2f}" if isinstance(v, (int, float)) else str(v))
