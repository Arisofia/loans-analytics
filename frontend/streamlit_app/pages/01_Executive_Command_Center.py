"""01 — Executive Command Center.

Top-level dashboard combining business state, key metrics,
alerts, and action items from the Decision Intelligence pipeline.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Executive Command Center", page_icon="📊", layout="wide")

from frontend.streamlit_app.decision_loader import load_decision_state
from frontend.streamlit_app.components.alert_cards import render_alert_list
from frontend.streamlit_app.components.decision_table import render_decision_table
from frontend.streamlit_app.components.confidence_badge import render_confidence_badge


def main() -> None:
    st.title("📊 Executive Command Center")

    state = load_decision_state()
    if state is None:
        st.warning("No decision state found. Run the pipeline first.")
        return

    # Business state banner
    biz_state = state.get("business_state", "unknown")
    state_colors = {
        "healthy": "🟢", "attention": "🟡", "critical": "🔴", "data_blocked": "⛔",
        "covenant_watch": "🟠",
    }
    st.header(f"{state_colors.get(biz_state, '⚪')} Business State: {biz_state.replace('_', ' ').title()}")

    # ── Covenant status strip ───────────────────────────────────────
    all_alerts = state.get("critical_alerts", []) + state.get("ranked_alerts", [])
    covenant_alerts = [
        a for a in all_alerts
        if (a.get("alert_id") or "").startswith("covenant.")
    ]
    if covenant_alerts:
        breach_count = len(covenant_alerts)
        st.error(f"⚠️ **Covenant Monitor:** {breach_count} breach(es) detected")
        for ca in covenant_alerts:
            st.caption(f"🔴 {ca.get('title', '')} — {ca.get('description', '')}")
    else:
        st.success("✅ **Covenant Monitor:** All covenants within thresholds")

    # Confidence
    render_confidence_badge(state.get("confidence", "medium"))

    # Key metrics strip
    metrics = state.get("metrics", {})
    if metrics:
        cols = st.columns(min(len(metrics), 6))
        for idx, (k, v) in enumerate(list(metrics.items())[:6]):
            with cols[idx % len(cols)]:
                st.metric(k, f"{v:,.2f}" if isinstance(v, (int, float)) else str(v))

    # Alerts
    st.subheader("Alerts")
    render_alert_list(state.get("alerts", []))

    # Actions
    st.subheader("Prioritised Actions")
    render_decision_table(state.get("actions", []))

    # Recommendations
    recs = state.get("recommendations", [])
    if recs:
        st.subheader("Recommendations")
        for r in recs:
            st.markdown(f"💡 {r}")


main()
