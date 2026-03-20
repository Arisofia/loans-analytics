"""Helpers for loading KPI snapshot data from API for Streamlit dashboards."""

from __future__ import annotations

import logging
import os
from typing import Optional

import pandas as pd

from frontend.streamlit_app.kpi_api_client import KPIResponse, get_client
from frontend.streamlit_app.kpi_websocket_client import get_snapshot_once

logger = logging.getLogger(__name__)


def _to_snapshot_entry(kpi: KPIResponse) -> dict[str, object]:
    return {
        "value": kpi.value,
        "threshold_status": kpi.threshold_status,
        "thresholds": kpi.thresholds,
        "unit": kpi.unit,
        "name": kpi.name,
        "updated_at": kpi.updated_at,
    }


def _kpi_entry_from_dict(kpi: dict[str, object]) -> tuple[str, dict[str, object]]:
    kpi_id = str(kpi.get("id", "")).strip()
    if not kpi_id:
        return "", {}
    return (
        kpi_id,
        {
            "value": kpi.get("value"),
            "threshold_status": kpi.get("threshold_status", "not_configured"),
            "thresholds": kpi.get("thresholds", {}),
            "unit": kpi.get("unit", "unknown"),
            "name": kpi.get("name", ""),
            "updated_at": kpi.get("updated_at"),
        },
    )


def _fetch_api_result(api_url: Optional[str]) -> dict[str, object]:
    use_ws = os.getenv("KPI_USE_WEBSOCKET", "0").strip().lower() in {"1", "true", "yes"}
    if use_ws:
        return get_snapshot_once()
    client = get_client(api_url=api_url)
    return client.get_latest_kpis(use_cache=True)


def _build_snapshot(api_kpis: list[object]) -> dict[str, dict[str, object]]:
    snapshot: dict[str, dict[str, object]] = {}
    for kpi in api_kpis:
        if isinstance(kpi, KPIResponse):
            if kpi.id:
                snapshot[kpi.id] = _to_snapshot_entry(kpi)
            continue
        if isinstance(kpi, dict):
            kpi_id, entry = _kpi_entry_from_dict(kpi)
            if kpi_id:
                snapshot[kpi_id] = entry
    return snapshot


def load_kpi_snapshot_from_api(
    api_url: Optional[str] = None,
) -> tuple[dict[str, dict[str, object]], Optional[pd.Timestamp], bool]:
    """
    Load KPI snapshot from API.

    Returns:
        Tuple of (snapshot, snapshot_month, is_api_source).
    """
    use_api = os.getenv("KPI_USE_API", "1").strip().lower() not in {"0", "false", "no"}
    if not use_api:
        return {}, None, False

    try:
        api_result = _fetch_api_result(api_url)
        api_kpis = api_result.get("kpis", [])
        if not isinstance(api_kpis, list) or not api_kpis:
            return {}, None, False

        snapshot = _build_snapshot(api_kpis)
        if not snapshot:
            return {}, None, False

        timestamp_raw = api_result.get("timestamp")
        snapshot_month = pd.to_datetime(timestamp_raw, errors="coerce")
        if pd.isna(snapshot_month):
            snapshot_month = None

        return snapshot, snapshot_month, True
    except Exception as exc:
        logger.error("KPI API unreachable — cannot load snapshot: %s", exc)
        raise RuntimeError(f"KPI API snapshot unavailable: {exc}") from exc