"""Unit tests for KPI WebSocket client wrappers."""

from __future__ import annotations

import pytest

from frontend.streamlit_app.kpi_websocket_client import KPIWebSocketClient


def test_websocket_client_defaults():
    client = KPIWebSocketClient()
    assert client.ws_url.startswith("ws://")
    assert client.connect_timeout > 0
    assert client.receive_timeout > 0


def test_async_get_snapshot_requires_websockets_when_missing(monkeypatch):
    monkeypatch.setattr("frontend.streamlit_app.kpi_websocket_client.websockets", None)
    client = KPIWebSocketClient()

    with pytest.raises(ImportError):
        import asyncio

        asyncio.run(client.async_get_snapshot())
