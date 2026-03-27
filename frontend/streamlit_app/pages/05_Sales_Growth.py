"""05 — Sales & Growth Intelligence.

Surfaces outputs from the Sales, Segmentation, and Pricing decision
agents: win-rate, segment risk, spread adequacy, and associated
alerts / recommendations.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Sales & Growth", page_icon="📈", layout="wide")

from frontend.streamlit_app.decision_loader import load_decision_state

_SALES_AGENTS = {"sales", "segmentation", "pricing"}
_SALES_KEYWORDS = {"win rate", "win_rate", "spread", "pricing", "segment", "dpd"}


def _filter_by_agent(items: list[dict], agents: set[str]) -> list[dict]:
    """Return items whose ``alert_id``, ``action_id``, or ``rec_id`` belongs to an agent."""
    out = []
    for item in items:
        aid = item.get("alert_id") or item.get("action_id") or item.get("rec_id") or ""
        prefix = aid.split(".")[0] if "." in aid else ""
        if prefix in agents:
            out.append(item)
    return out


def _severity_icon(severity: str) -> str:
    return {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")


def main() -> None:
    st.title("📈 Sales & Growth Intelligence")

    state = load_decision_state()
    if state is None:
        st.warning("No decision state found. Run the pipeline first.")
        return

    # ── Agent status strip ──────────────────────────────────────────
    statuses = state.get("agent_statuses", {})
    status_cols = st.columns(len(_SALES_AGENTS))
    for idx, agent_id in enumerate(sorted(_SALES_AGENTS)):
        with status_cols[idx]:
            status = statuses.get(agent_id, "not_run")
            icon = "✅" if status == "ok" else "⚠️" if status == "blocked" else "⛔" if status == "error" else "⏳"
            st.metric(agent_id.replace("_", " ").title(), f"{icon} {status}")

    st.divider()

    # ── Collect agent-specific items ────────────────────────────────
    all_alerts = state.get("critical_alerts", []) + state.get("ranked_alerts", [])
    all_actions = state.get("ranked_actions", [])
    all_opps = state.get("opportunities", [])

    sales_alerts = _filter_by_agent(all_alerts, _SALES_AGENTS)
    sales_actions = _filter_by_agent(all_actions, _SALES_AGENTS)
    sales_recs = _filter_by_agent(all_opps, _SALES_AGENTS)

    # Include keyword-matched alerts without explicit agent prefix
    for item in all_alerts:
        if item not in sales_alerts:
            title = (item.get("title") or "").lower()
            if any(kw in title for kw in _SALES_KEYWORDS):
                sales_alerts.append(item)

    # ── Tabs ────────────────────────────────────────────────────────
    tab_overview, tab_alerts, tab_actions, tab_recs = st.tabs(
        ["Overview", "Alerts", "Actions", "Recommendations"],
    )

    with tab_overview:
        st.subheader("Commercial Intelligence Summary")
        cols = st.columns(3)
        for col_idx, aid in enumerate(sorted(_SALES_AGENTS)):
            with cols[col_idx]:
                st.markdown(f"#### {aid.replace('_', ' ').title()} Agent")
                s = statuses.get(aid)
                if s == "ok":
                    st.success("Monitored — within thresholds")
                elif s == "blocked":
                    st.error("Blocked by covenant breach")
                else:
                    st.info("Not yet run")

        if sales_alerts:
            st.warning(f"{len(sales_alerts)} active alert(s) from commercial agents.")
        else:
            st.success("No commercial alerts — all metrics within thresholds.")

    with tab_alerts:
        st.subheader("Sales & Growth Alerts")
        if sales_alerts:
            for alert in sales_alerts:
                sev = alert.get("severity", "info")
                st.markdown(f"{_severity_icon(sev)} **[{sev.upper()}]** {alert.get('title', 'Alert')}")
                if alert.get("description"):
                    st.caption(alert["description"])
                val = alert.get("current_value")
                thr = alert.get("threshold")
                if val and thr:
                    st.caption(f"Current: `{val}` · Threshold: `{thr}`")
        else:
            st.success("No active alerts for Sales / Segmentation / Pricing.")

    with tab_actions:
        st.subheader("Pending Actions")
        if sales_actions:
            for action in sales_actions:
                confidence = action.get("confidence", 0)
                st.markdown(
                    f"**{action.get('title', 'Action')}**  \n"
                    f"Owner: `{action.get('owner', '—')}` · "
                    f"Urgency: `{action.get('urgency', 'medium')}` · "
                    f"Confidence: `{confidence:.0%}`"
                )
                if action.get("details"):
                    st.caption(action["details"])
        else:
            st.info("No pending commercial actions.")

    with tab_recs:
        st.subheader("Recommendations")
        if sales_recs:
            for rec in sales_recs:
                st.markdown(f"💡 **{rec.get('title', '')}**")
                st.caption(rec.get("rationale", ""))
                if rec.get("expected_impact"):
                    st.caption(f"Expected impact: {rec['expected_impact']}")
        else:
            st.info("No recommendations from commercial agents.")


if __name__ == "__main__":
    main()
