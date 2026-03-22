"""WebSocket client for real-time KPI snapshot retrieval."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Optional

try:
    import websockets
except ImportError:  # pragma: no cover - optional in limited environments
    websockets = None  # type: ignore[assignment]


class KPIWebSocketClient:
    """Minimal client for consuming KPI snapshots from analytics WebSocket endpoint."""

    def __init__(
        self,
        ws_url: Optional[str] = None,
        connect_timeout: float = 5.0,
        receive_timeout: float = 5.0,
    ):
        self.ws_url = ws_url or os.getenv("KPI_WS_URL", "ws://127.0.0.1:8000/analytics/kpis/stream")
        self.connect_timeout = connect_timeout
        self.receive_timeout = receive_timeout

    async def async_get_snapshot(
        self,
        kpi_keys: Optional[list[str]] = None,
        once: bool = True,
        interval_seconds: float = 5.0,
    ) -> dict[str, Any]:
        """Receive one KPI snapshot payload from the stream endpoint."""
        if not websockets:
            raise ImportError("websockets package is required for KPIWebSocketClient")

        query_parts = [
            f"once={'true' if once else 'false'}",
            f"interval_seconds={interval_seconds}",
        ]
        if kpi_keys:
            query_parts.append(f"kpi_keys={','.join(kpi_keys)}")
        stream_url = f"{self.ws_url}?{'&'.join(query_parts)}"

        async with websockets.connect(stream_url, open_timeout=self.connect_timeout) as ws:
            message = await asyncio.wait_for(ws.recv(), timeout=self.receive_timeout)
            payload = json.loads(message)
            if not isinstance(payload, dict):
                raise ValueError("Invalid WebSocket payload format")
            return payload


def get_snapshot_once(
    ws_url: Optional[str] = None,
    kpi_keys: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Synchronous wrapper for one-shot KPI snapshot retrieval."""
    client = KPIWebSocketClient(ws_url=ws_url)
    return asyncio.run(client.async_get_snapshot(kpi_keys=kpi_keys, once=True))
