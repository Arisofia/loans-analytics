"""10 — AI Decision Center (First Live Slice)."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="AI Decision Center", page_icon="🎯", layout="wide")


def _severity_color(severity: str) -> str:
    return {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")


def main() -> None:
    st.title("🎯 AI Decision Center")

    from frontend.streamlit_app.decision_loader import (
        load_decision_state,
        load_metrics,
    )

    state = load_decision_state()
    metrics_data = load_metrics()

    if state is None:
        st.info("Run the pipeline to populate this page.")
        st.stop()

    tab_metrics, tab_alerts, tab_actions, tab_opps = st.tabs(
        ["Executive Metrics", "Alerts", "Actions", "Opportunities"]
    )

    # ── Executive Metrics ────────────────────────────────────────────
    with tab_metrics:
        if metrics_data:
            exec_metrics = metrics_data.get("executive_metrics", [])
            if exec_metrics:
                cols = st.columns(min(len(exec_metrics), 4))
                for i, m in enumerate(exec_metrics):
                    with cols[i % len(cols)]:
                        label = m.get("metric_name", m.get("metric_id", ""))
                        val = m.get("value", 0)
                        unit = m.get("unit", "")
                        if unit == "ratio":
                            st.metric(label, f"{val:.2%}")
                        elif unit == "currency":
                            st.metric(label, f"${val:,.0f}")
                        else:
                            st.metric(label, f"{val:,.2f}")
            else:
                st.write("_No executive metrics available._")
        else:
            st.write("_No metrics data — run the pipeline first._")

    # ── Alerts ────────────────────────────────────────────────────────
    with tab_alerts:
        alerts = state.get("ranked_alerts", [])
        if alerts:
            for alert in alerts:
                sev = alert.get("severity", "info")
                icon = _severity_color(sev)
                title = alert.get("title", "Alert")
                desc = alert.get("description", "")
                st.markdown(f"{icon} **[{sev.upper()}]** {title}")
                if desc:
                    st.caption(desc)
        else:
            st.success("No alerts — all metrics within thresholds.")

    # ── Actions ───────────────────────────────────────────────────────
    with tab_actions:
        actions = state.get("ranked_actions", [])
        if actions:
            for action in actions:
                title = action.get("title", "Action")
                owner = action.get("owner", "—")
                urgency = action.get("urgency", "medium")
                confidence = action.get("confidence", 0)
                st.markdown(
                    f"**{title}**  \n"
                    f"Owner: `{owner}` · Urgency: `{urgency}` · "
                    f"Confidence: `{confidence:.0%}`"
                )
        else:
            st.info("No pending actions.")

    # ── Opportunities ────────────────────────────────────────────────
    with tab_opps:
        opps = state.get("opportunities", [])
        if opps:
            for opp in opps:
                title = opp.get("title", "Opportunity")
                rationale = opp.get("rationale", "")
                impact = opp.get("expected_impact", "")
                st.markdown(f"**{title}**")
                if rationale:
                    st.write(rationale)
                if impact:
                    st.caption(f"Expected impact: {impact}")
        else:
            st.info("No opportunities identified in the latest run.")

    # ── Agent statuses ──────────────────────────────────────────────
    statuses = state.get("agent_statuses", {})
    if statuses:
        with st.expander("Agent Run Statuses"):
            for agent_id, status in statuses.items():
                emoji = "✅" if status == "ok" else "⚠️"
                st.write(f"{emoji} **{agent_id}**: {status}")


main()
