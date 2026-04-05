from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

def _make_mock_kpi():
    kpi = MagicMock()
    kpi.model_dump.return_value = {'id': 'COLLECTION_RATE', 'name': 'Collection Rate', 'value': 95.0, 'unit': '%', 'threshold_status': 'normal', 'thresholds': {'warning': 80.0, 'critical': 70.0}}
    return kpi

def _make_mock_kpi_service():
    svc = AsyncMock()
    svc.get_latest_kpis = AsyncMock(return_value=[_make_mock_kpi()])
    return svc

def test_kpi_stream_websocket_once_returns_snapshot_event():
    # Import both inside the test to avoid holding a stale module reference
    # after sys.modules.pop in test_deployment_readiness.py's
    # _clear_api_main_module fixture, which would cause the dependency
    # override key to mismatch and invoke the real (unmocked) KPI service.
    from backend.loans_analytics.apps.analytics.api.main import app, get_kpi_service  # noqa: PLC0415
    client = TestClient(app)
    app.dependency_overrides[get_kpi_service] = _make_mock_kpi_service
    try:
        with client.websocket_connect('/analytics/kpis/stream?once=true') as websocket:
            payload = websocket.receive_json()
    finally:
        app.dependency_overrides.pop(get_kpi_service, None)
    assert payload['event'] == 'kpi_snapshot'
    assert payload['source'] == 'realtime-stream'
    assert 'timestamp' in payload
    assert isinstance(payload['kpis'], list)

def test_kpi_stream_websocket_supports_kpi_key_filter_param():
    # Same rationale: import inside the test to survive sys.modules eviction
    # by test_deployment_readiness.py's _clear_api_main_module fixture.
    from backend.loans_analytics.apps.analytics.api.main import app, get_kpi_service  # noqa: PLC0415
    client = TestClient(app)
    app.dependency_overrides[get_kpi_service] = _make_mock_kpi_service
    try:
        with client.websocket_connect('/analytics/kpis/stream?once=true&kpi_keys=PAR30') as websocket:
            payload = websocket.receive_json()
    finally:
        app.dependency_overrides.pop(get_kpi_service, None)
    assert payload['event'] == 'kpi_snapshot'
    assert isinstance(payload['kpis'], list)
    if payload['kpis']:
        first = payload['kpis'][0]
        assert 'id' in first
        assert 'value' in first

