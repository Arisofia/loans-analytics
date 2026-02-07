"""Monitoring & Control dashboard for the self-healing platform."""

import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# Add root directory to path to allow imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from python.config.theme import ABACO_THEME  # noqa: E402

st.set_page_config(page_title="Monitoring & Control - Abaco", layout="wide")

st.markdown(
    f"""
    <style>
    .main {{
        background-color: {ABACO_THEME['colors']['background']};
        color: {ABACO_THEME['colors']['white']};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Monitoring & Control")

API_BASE = st.sidebar.text_input("API Base URL", value="http://localhost:8000", key="api_base")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api_get(path: str, params: dict | None = None):
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def _api_post(path: str, json_body: dict | None = None):
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json_body, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def _api_patch(path: str, json_body: dict | None = None):
    try:
        resp = requests.patch(f"{API_BASE}{path}", json=json_body, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ---------------------------------------------------------------------------
# Section 1: Live Event Feed
# ---------------------------------------------------------------------------
st.header("Live Event Feed")

col_sev, col_src, col_limit = st.columns(3)
with col_sev:
    severity_filter = st.selectbox("Severity", ["all", "info", "warning", "critical"], index=0)
with col_src:
    source_filter = st.text_input("Source filter", value="")
with col_limit:
    event_limit = st.number_input("Limit", min_value=1, max_value=500, value=50)

if st.button("Refresh Events", key="refresh_events"):
    event_params: dict = {"limit": event_limit}
    if severity_filter != "all":
        event_params["severity"] = severity_filter
    if source_filter:
        event_params["source"] = source_filter

    data = _api_get("/monitoring/events", params=event_params)
    if data and data.get("events"):
        st.session_state["events_data"] = data["events"]
    elif data:
        st.info("No events found.")

if "events_data" in st.session_state and st.session_state["events_data"]:
    events = st.session_state["events_data"]
    df = pd.DataFrame(events)
    display_cols = [
        c
        for c in ["created_at", "severity", "event_type", "source", "id", "acknowledged_at"]
        if c in df.columns
    ]
    st.dataframe(
        df[display_cols].sort_values("created_at", ascending=False), use_container_width=True
    )

    # Acknowledge button
    st.subheader("Acknowledge Event")
    event_id_to_ack = st.text_input("Event ID to acknowledge")
    if st.button("Acknowledge", key="ack_btn"):
        if event_id_to_ack:
            result = _api_post(f"/monitoring/events/{event_id_to_ack}/ack")
            if result:
                st.success(f"Event {event_id_to_ack} acknowledged.")
        else:
            st.warning("Enter an event ID first.")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Command Panel
# ---------------------------------------------------------------------------
st.header("Command Panel")

cmd_col1, cmd_col2 = st.columns(2)
with cmd_col1:
    cmd_type = st.selectbox(
        "Command Type",
        ["rerun_pipeline", "notify_team", "scale_up", "acknowledge_alert"],
    )
with cmd_col2:
    cmd_requester = st.selectbox("Requested By", ["operator", "n8n", "auto_rule"])

cmd_event_id = st.text_input("Related Event ID (optional)", value="")
cmd_params_raw = st.text_area("Parameters (JSON)", value="{}", height=80)

if st.button("Create Command", key="create_cmd"):
    import json

    try:
        params_dict = json.loads(cmd_params_raw)
    except json.JSONDecodeError:
        st.error("Invalid JSON in parameters field.")
        params_dict = None

    if params_dict is not None:
        body = {
            "command_type": cmd_type,
            "requested_by": cmd_requester,
            "parameters": params_dict,
        }
        if cmd_event_id:
            body["event_id"] = cmd_event_id

        result = _api_post("/monitoring/commands", json_body=body)
        if result:
            st.success(f"Command created: {result}")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Command Status
# ---------------------------------------------------------------------------
st.header("Command Status")

status_filter = st.selectbox(
    "Status filter", ["all", "pending", "running", "completed", "failed"], index=0
)

if st.button("Refresh Commands", key="refresh_cmds"):
    cmd_query_params = {"limit": 50}
    if status_filter != "all":
        cmd_query_params["status"] = status_filter

    data = _api_get("/monitoring/commands", params=cmd_query_params)
    if data and data.get("commands"):
        st.session_state["commands_data"] = data["commands"]
    elif data:
        st.info("No commands found.")

if "commands_data" in st.session_state and st.session_state["commands_data"]:
    cmds = st.session_state["commands_data"]
    df_cmds = pd.DataFrame(cmds)
    display_cols = [
        c
        for c in ["created_at", "command_type", "status", "requested_by", "id", "completed_at"]
        if c in df_cmds.columns
    ]
    st.dataframe(
        df_cmds[display_cols].sort_values("created_at", ascending=False),
        use_container_width=True,
    )
