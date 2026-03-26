"""Alert card components for decision intelligence pages."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

_SEVERITY_COLORS = {
    "critical": "#FF4B4B",
    "warning": "#FFA500",
    "info": "#4B8BFF",
}
_SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "info": "🔵"}


def render_alert_cards(alerts: List[Dict[str, Any]]) -> None:
    """Render a row of alert cards using ``st.columns``."""
    if not alerts:
        st.info("No active alerts.")
        return

    cols = st.columns(min(len(alerts), 4))
    for idx, alert in enumerate(alerts):
        col = cols[idx % len(cols)]
        severity = alert.get("severity", "info")
        emoji = _SEVERITY_EMOJI.get(severity, "⚪")
        color = _SEVERITY_COLORS.get(severity, "#888")
        with col:
            st.markdown(
                f"""
                <div style="border-left: 4px solid {color}; padding: 0.8rem;
                            margin-bottom: 0.5rem; border-radius: 4px;
                            background: var(--background-color);">
                    <strong>{emoji} {alert.get('title', 'Alert')}</strong><br/>
                    <span style="font-size: 0.85rem;">{alert.get('message', '')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_alert_list(alerts: List[str]) -> None:
    """Render a simple list of alert strings."""
    if not alerts:
        return
    for a in alerts:
        severity = "critical" if "critical" in a.lower() else (
            "warning" if "warning" in a.lower() else "info"
        )
        emoji = _SEVERITY_EMOJI.get(severity, "⚪")
        st.markdown(f"{emoji} {a}")
