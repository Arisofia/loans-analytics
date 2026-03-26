"""10 — AI Decision Center.

Board-grade decision intelligence dashboard that displays the
``DecisionCenterState`` produced by Phase 5 of the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

st.set_page_config(page_title="AI Decision Center", page_icon="🎯", layout="wide")


# ── helpers ──────────────────────────────────────────────────────────────
def _load_latest_decision_state() -> Dict[str, Any] | None:
    """Find the most recent decision_center_state.json in logs/runs/."""
    runs_dir = Path("logs/runs")
    if not runs_dir.exists():
        return None

    candidates: List[Path] = []
    for run_dir in runs_dir.iterdir():
        state_path = run_dir / "decision" / "decision_center_state.json"
        if state_path.exists():
            candidates.append(state_path)

    if not candidates:
        return None

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    with open(latest, encoding="utf-8") as fh:
        return json.load(fh)


def _severity_color(severity: str) -> str:
    return {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")


def _urgency_emoji(urgency: str) -> str:
    return {"critical": "🚨", "high": "🔥", "medium": "⚡", "low": "💡"}.get(urgency, "📌")


# ── main page ────────────────────────────────────────────────────────────
def main() -> None:
    st.title("🎯 AI Decision Center")

    state = _load_latest_decision_state()

    if state is None:
        st.warning(
            "No decision state found. Run the pipeline first "
            "(`python scripts/data/run_data_pipeline.py`)."
        )
        return

    # ── Business state strip ────────────────────────────────────────────
    biz_state = state.get("business_state", "unknown")
    state_colors = {
        "healthy": ("🟢", "Healthy"),
        "attention": ("🟡", "Attention Required"),
        "critical": ("🔴", "Critical"),
        "covenant_watch": ("🟠", "Covenant Watch"),
        "data_blocked": ("⚫", "Data Quality Blocked"),
    }
    emoji, label = state_colors.get(biz_state, ("⚪", biz_state.title()))
    st.header(f"{emoji} Business State: {label}")
    st.caption(f"Generated: {state.get('timestamp', 'N/A')}")

    # ── Summary metrics ─────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Critical Alerts", len(state.get("critical_alerts", [])))
    col2.metric("Ranked Actions", len(state.get("ranked_actions", [])))
    col3.metric("Opportunities", len(state.get("opportunities", [])))
    col4.metric("Agents OK", sum(
        1 for s in state.get("agent_statuses", {}).values() if s == "ok"
    ))

    st.divider()

    # ── Critical Alerts ─────────────────────────────────────────────────
    st.subheader("🔴 Critical Alerts")
    alerts = state.get("critical_alerts", [])
    if not alerts:
        st.success("No critical alerts.")
    else:
        for alert in alerts:
            with st.expander(f"{_severity_color(alert.get('severity', ''))} {alert.get('title', 'Alert')}", expanded=True):
                st.write(alert.get("description", ""))
                if alert.get("metric_id"):
                    st.code(
                        f"Metric: {alert['metric_id']}  |  "
                        f"Current: {alert.get('current_value', 'N/A')}  |  "
                        f"Threshold: {alert.get('threshold', 'N/A')}"
                    )

    st.divider()

    # ── Ranked Actions ──────────────────────────────────────────────────
    st.subheader("📋 Ranked Actions (Priority Order)")
    actions = state.get("ranked_actions", [])
    if not actions:
        st.info("No actions queued.")
    else:
        for i, action in enumerate(actions, 1):
            urg = _urgency_emoji(action.get("urgency", ""))
            with st.expander(f"{i}. {urg} {action.get('title', 'Action')} — Owner: {action.get('owner', 'N/A')}"):
                st.write(f"**Impact:** {action.get('impact', 'N/A')}")
                st.write(f"**Confidence:** {action.get('confidence', 'N/A')}")
                if action.get("details"):
                    st.write(action["details"])

    st.divider()

    # ── Opportunities ───────────────────────────────────────────────────
    st.subheader("💡 Opportunities")
    opps = state.get("opportunities", [])
    if not opps:
        st.info("No opportunities identified.")
    else:
        for opp in opps:
            with st.expander(f"💡 {opp.get('title', 'Opportunity')}"):
                st.write(f"**Rationale:** {opp.get('rationale', '')}")
                st.write(f"**Expected Impact:** {opp.get('expected_impact', '')}")
                st.write(f"**Confidence:** {opp.get('confidence', 'N/A')}")

    st.divider()

    # ── Scenario Summary ────────────────────────────────────────────────
    st.subheader("📊 Scenario Summary")
    scenarios = state.get("scenario_summary", {})
    if scenarios:
        for name, details in scenarios.items():
            triggers = details.get("triggers", [])
            horizon = details.get("horizon")
            with st.expander(f"Scenario: {name.title()} ({horizon}m horizon)"):
                if triggers:
                    for t in triggers:
                        st.write(f"- {t}")
                else:
                    st.write("No triggers under this scenario.")
    else:
        st.info("No scenario data available.")

    st.divider()

    # ── Agent Status Grid ───────────────────────────────────────────────
    st.subheader("🤖 Agent Status")
    statuses = state.get("agent_statuses", {})
    if statuses:
        cols = st.columns(min(len(statuses), 5))
        for i, (agent_id, status) in enumerate(statuses.items()):
            status_emoji = {"ok": "✅", "blocked": "🚫", "skipped": "⏭️", "error": "❌"}.get(status, "❓")
            cols[i % len(cols)].metric(agent_id, f"{status_emoji} {status}")

    # ── Raw JSON (collapsible) ──────────────────────────────────────────
    with st.expander("🔧 Raw Decision State JSON"):
        st.json(state)


main()
