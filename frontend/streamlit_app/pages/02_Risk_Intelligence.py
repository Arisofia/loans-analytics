"""02 — Risk Intelligence.

Displays structured outputs from the Risk, Cohort/Vintage, and
Concentration decision agents: PAR curves, vintage deterioration,
HHI / top-N exposure, and associated alerts & actions.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Risk Intelligence", page_icon="🛡️", layout="wide")

from frontend.streamlit_app.decision_loader import load_decision_state

_RISK_AGENTS = {"risk", "cohort_vintage", "concentration"}
_RISK_KEYWORDS = {"par30", "par_30", "par 30", "expected loss", "hhi", "concentration", "vintage", "default rate", "covenant"}


def _filter_by_agent(items: list[dict], agents: set[str]) -> list[dict]:
    """Return items whose id prefix matches one of *agents*."""
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
    st.title("🛡️ Risk Intelligence")

    state = load_decision_state()
    if state is None:
        st.warning("No decision state found. Run the pipeline first.")
        return

    # ── Agent status strip ──────────────────────────────────────────
    statuses = state.get("agent_statuses", {})
    status_cols = st.columns(len(_RISK_AGENTS))
    for idx, agent_id in enumerate(sorted(_RISK_AGENTS)):
        with status_cols[idx]:
            status = statuses.get(agent_id, "not_run")
            label = agent_id.replace("_", " ").title()
            icon = "✅" if status == "ok" else "⚠️" if status == "blocked" else "⛔" if status == "error" else "⏳"
            st.metric(label, f"{icon} {status}")

    st.divider()

    # ── Collect items ───────────────────────────────────────────────
    all_alerts = state.get("critical_alerts", []) + state.get("ranked_alerts", [])
    all_actions = state.get("ranked_actions", [])
    all_opps = state.get("opportunities", [])

    risk_alerts = _filter_by_agent(all_alerts, _RISK_AGENTS)
    risk_actions = _filter_by_agent(all_actions, _RISK_AGENTS)
    risk_recs = _filter_by_agent(all_opps, _RISK_AGENTS)

    # Include keyword-matched alerts without explicit agent prefix
    for item in all_alerts:
        if item not in risk_alerts:
            title = (item.get("title") or "").lower()
            if any(kw in title for kw in _RISK_KEYWORDS):
                risk_alerts.append(item)

    # ── Tabs ────────────────────────────────────────────────────────
    tab_overview, tab_alerts, tab_actions, tab_recs = st.tabs(
        ["Risk Overview", "Alerts", "Actions", "Recommendations"],
    )

    # ── Overview ────────────────────────────────────────────────────
    with tab_overview:
        st.subheader("Risk Agent Outputs")

        cols = st.columns(3)
        _agent_labels = {
            "cohort_vintage": ("Cohort / Vintage", "Origination vintage analysis and trend detection"),
            "concentration": ("Concentration", "HHI, top-N exposure, single obligor cap"),
            "risk": ("Risk", "PAR30 monitoring, expected loss"),
        }
        for col_idx, aid in enumerate(sorted(_RISK_AGENTS)):
            with cols[col_idx]:
                label, desc = _agent_labels.get(aid, (aid, ""))
                st.markdown(f"#### {label}")
                st.caption(desc)
                s = statuses.get(aid)
                if s == "ok":
                    st.success("Completed")
                elif s == "blocked":
                    st.error("Blocked by upstream agent")
                elif s == "error":
                    st.error("Agent error")
                elif s == "skipped":
                    st.warning("Skipped — dependencies not met")
                else:
                    st.info("Not yet run")

        critical_count = sum(1 for a in risk_alerts if a.get("severity") == "critical")
        warning_count = sum(1 for a in risk_alerts if a.get("severity") == "warning")
        if critical_count:
            st.error(f"🔴 {critical_count} critical risk alert(s)")
        if warning_count:
            st.warning(f"🟡 {warning_count} warning(s)")
        if not critical_count and not warning_count:
            st.success("No risk alerts — portfolio within thresholds.")

    # ── Alerts ──────────────────────────────────────────────────────
    with tab_alerts:
        st.subheader("Risk Alerts")
        if risk_alerts:
            for alert in risk_alerts:
                sev = alert.get("severity", "info")
                st.markdown(f"{_severity_icon(sev)} **[{sev.upper()}]** {alert.get('title', 'Alert')}")
                if alert.get("description"):
                    st.caption(alert["description"])
                val = alert.get("current_value")
                thr = alert.get("threshold")
                if val and thr:
                    st.caption(f"Current: `{val}` · Threshold: `{thr}`")
        else:
            st.success("No active risk alerts.")

    # ── Actions ─────────────────────────────────────────────────────
    with tab_actions:
        st.subheader("Risk Actions")
        if risk_actions:
            for action in risk_actions:
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
            st.info("No pending risk actions.")

    # ── Recommendations ─────────────────────────────────────────────
    with tab_recs:
        st.subheader("Risk Recommendations")
        if risk_recs:
            for rec in risk_recs:
                st.markdown(f"💡 **{rec.get('title', '')}**")
                st.caption(rec.get("rationale", ""))
                if rec.get("expected_impact"):
                    st.caption(f"Expected impact: {rec['expected_impact']}")
        else:
            st.info("No recommendations from risk agents.")


if __name__ == "__main__":
    main()
