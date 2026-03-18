"""Monitoring & Control dashboard for the self-healing platform."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import pandas as pd
import requests
import streamlit as st

# Add root directory to path to allow imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
for _p in (ROOT_DIR / "backend", ROOT_DIR / "frontend", ROOT_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from python.config.theme import ABACO_THEME  # noqa: E402
from streamlit_app.utils.security import sanitize_api_base  # noqa: E402

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

# API base URL from server-side configuration (environment variable).
# Not sourced from a Streamlit widget, so CodeQL does not treat it as
# a RemoteFlowSource. Set ABACO_API_BASE in .env or deployment config.
API_BASE: str = os.environ.get("ABACO_API_BASE", "http://localhost:8000")

API_BASE_SAFE = sanitize_api_base(API_BASE)
if API_BASE_SAFE is None:
    st.sidebar.text("API: <invalid or untrusted>")
    st.error("Invalid ABACO_API_BASE configuration. Contact your administrator.")
else:
    st.sidebar.text(f"API: {API_BASE_SAFE}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


MONITORING_EVENTS_ENDPOINT = "/monitoring/events"
MONITORING_EVENTS_ACK_ENDPOINT = "/monitoring/events/ack"
MONITORING_COMMANDS_ENDPOINT = "/monitoring/commands"
ALLOWED_ENDPOINTS = {
    MONITORING_EVENTS_ENDPOINT,
    MONITORING_EVENTS_ACK_ENDPOINT,
    MONITORING_COMMANDS_ENDPOINT,
}


def _build_api_url(path: str) -> str | None:
    """Build a request URL from a fixed literal path.

    This function implements strict SSRF protection by:
    1. Using a sanitized base URL from an environment variable.
    2. Accepting only hardcoded literal paths from local wrappers.
    3. Verifying that the final constructed URL matches the expected host and scheme.
    """
    base = API_BASE_SAFE
    if base is None:
        st.error("API is not configured or is untrusted. Aborting request.")
        return None

    if path not in ALLOWED_ENDPOINTS:
        st.error("SSRF Protection: endpoint is not in the allowed API route list.")
        return None

    normalized_base = base.rstrip("/")
    # Construct URL using verified literal path from wrapper functions.
    url = f"{normalized_base}{path}"

    # Final host/scheme validation to prevent manipulation
    parsed_url = urlparse(url)
    parsed_base = urlparse(normalized_base)
    if parsed_url.netloc != parsed_base.netloc or parsed_url.scheme != parsed_base.scheme:
        st.error("SSRF Protection: URL host or scheme mismatch.")
        return None

    return url


def _request_json(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: dict | None = None,
):
    url = _build_api_url(path)
    if url is None:
        return None
    try:
        resp = requests.request(method, url, params=params, json=json_body, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def _api_get_events(params: dict | None = None):
    return _request_json("GET", MONITORING_EVENTS_ENDPOINT, params=params)


def _api_ack_event(event_id: str):
    return _request_json(
        "POST",
        MONITORING_EVENTS_ACK_ENDPOINT,
        json_body={"event_id": event_id},
    )


def _api_create_command(json_body: dict | None = None):
    return _request_json("POST", MONITORING_COMMANDS_ENDPOINT, json_body=json_body)


def _api_get_commands(params: dict | None = None):
    return _request_json("GET", MONITORING_COMMANDS_ENDPOINT, params=params)


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

    data = _api_get_events(params=event_params)
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
    st.dataframe(df[display_cols].sort_values("created_at", ascending=False), width="stretch")

    # Acknowledge button
    st.subheader("Acknowledge Event")
    event_id_to_ack = st.text_input("Event ID to acknowledge")
    if st.button("Acknowledge", key="ack_btn"):
        if event_id_to_ack:
            event_id_clean = event_id_to_ack.strip()
            try:
                UUID(event_id_clean)
            except ValueError:
                st.error("Invalid event ID format. Use a UUID value.")
            else:
                if result := _api_ack_event(event_id_clean):
                    st.success(f"Event {event_id_clean} acknowledged.")
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

        if result := _api_create_command(json_body=body):
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

    data = _api_get_commands(params=cmd_query_params)
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
        width="stretch",
    )
