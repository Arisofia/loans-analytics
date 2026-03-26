"""Decision table component — renders prioritised action items."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st


def render_decision_table(actions: List[Dict[str, Any]]) -> None:
    """Display a sortable table of orchestrator action items."""
    if not actions:
        st.info("No pending actions.")
        return

    rows = sorted(actions, key=lambda a: a.get("priority", 99))
    header = "| Priority | Agent | Action | Routed |"
    sep = "|---|---|---|---|"
    lines = [header, sep]
    for row in rows:
        routed = "✅" if row.get("routed") else "—"
        lines.append(
            f"| {row.get('priority', '-')} "
            f"| {row.get('agent', '?')} "
            f"| {row.get('action', '')} "
            f"| {routed} |"
        )
    st.markdown("\n".join(lines))
