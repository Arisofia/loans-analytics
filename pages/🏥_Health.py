import json
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Health Check", page_icon="🏥", layout="centered")


def check_system_health():
    """Perform basic system health checks."""
    checks = {}

    root_dir = Path(__file__).resolve().parent.parent
    checks["root_directory"] = root_dir.exists()

    exports_dir = root_dir / "exports"
    checks["exports_directory"] = exports_dir.exists()

    try:
        dashboard_path = exports_dir / "complete_kpi_dashboard.json"
        if dashboard_path.exists():
            with dashboard_path.open("r") as f:
                data = json.load(f)
                checks["kpi_dashboard"] = isinstance(data, dict) and len(data) > 0
        else:
            checks["kpi_dashboard"] = False
    except Exception as e:
        logger.error("Failed to check KPI dashboard: %s", e)
        checks["kpi_dashboard"] = False

    try:
        analytics_path = exports_dir / "analytics_facts.csv"
        checks["analytics_facts"] = analytics_path.exists()
    except Exception as e:
        logger.error("Failed to check analytics facts: %s", e)
        checks["analytics_facts"] = False

    return checks


st.title("🏥 Health Check")

st.markdown("---")

checks = check_system_health()
status = "ok" if all(checks.values()) else "partial"

col1, col2 = st.columns(2)
with col1:
    st.metric("Status", status.upper(), "✅" if status == "ok" else "⚠️")

with col2:
    st.metric("Timestamp", datetime.now().isoformat())

st.markdown("---")

st.subheader("System Components")
for check_name, check_result in checks.items():
    icon = "✅" if check_result else "❌"
    st.write(
        f"{icon} **{check_name.replace('_', ' ').title()}**: {'OK' if check_result else 'FAILED'}"
    )

st.markdown("---")

if status == "ok":
    st.success("✅ All systems operational", icon="✅")
else:
    st.warning(
        "⚠️ Some components are not ready. This is expected if analytics have not run yet.",
        icon="⚠️",
    )
    st.info(
        "Run the complete analytics pipeline to populate exports and resolve missing components.",
        icon="ℹ️",
    )
