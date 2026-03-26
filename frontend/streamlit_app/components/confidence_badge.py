"""Confidence badge — visual indicator of model/data confidence."""

from __future__ import annotations

import streamlit as st


_BADGES = {
    "high": ("🟢", "High Confidence"),
    "medium": ("🟡", "Medium Confidence"),
    "low": ("🔴", "Low Confidence"),
}


def render_confidence_badge(level: str) -> None:
    """Show an inline confidence badge (high / medium / low)."""
    emoji, label = _BADGES.get(level.lower(), ("⚪", level))
    st.markdown(f"**{emoji} {label}**")
