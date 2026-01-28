"""No-op tracing helpers for the Streamlit dashboard."""

from __future__ import annotations


def init_tracing(service_name: str) -> None:
    """Initialize tracing for the given service name (no-op in dashboard)."""
    _ = service_name


def enable_auto_instrumentation() -> None:
    """Enable auto instrumentation (no-op in dashboard)."""
    return None
