"""Tests for KPI WebSocket streaming endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.python.apps.analytics.api.main import app


def test_kpi_stream_websocket_once_returns_snapshot_event():
    client = TestClient(app)

    with client.websocket_connect("/analytics/kpis/stream?once=true") as websocket:
        payload = websocket.receive_json()

    assert payload["event"] == "kpi_snapshot"
    assert payload["source"] == "realtime-stream"
    assert "timestamp" in payload
    assert isinstance(payload["kpis"], list)


def test_kpi_stream_websocket_supports_kpi_key_filter_param():
    client = TestClient(app)

    with client.websocket_connect("/analytics/kpis/stream?once=true&kpi_keys=PAR30") as websocket:
        payload = websocket.receive_json()

    assert payload["event"] == "kpi_snapshot"
    assert isinstance(payload["kpis"], list)
    if payload["kpis"]:
        first = payload["kpis"][0]
        assert "id" in first
        assert "value" in first