from __future__ import annotations
from unittest.mock import Mock, patch
import pandas as pd
import pytest
from frontend.streamlit_app.kpi_api_client import KPIResponse
from frontend.streamlit_app.kpi_snapshot_loader import load_kpi_snapshot_from_api

def test_load_kpi_snapshot_from_api_success_with_dataclass(monkeypatch):
    monkeypatch.setenv('KPI_USE_API', '1')
    mock_client = Mock()
    mock_client.get_latest_kpis.return_value = {'kpis': [KPIResponse(id='avg_apr', name='Average APR', value=12.5, unit='%', threshold_status='normal', thresholds={'warning': 14.0, 'critical': 16.0}, updated_at='2026-03-20T10:00:00Z')], 'timestamp': '2026-03-20T10:00:00Z'}
    with patch('frontend.streamlit_app.kpi_snapshot_loader.get_client', return_value=mock_client):
        snapshot, snapshot_month, is_api_source = load_kpi_snapshot_from_api()
    assert is_api_source is True
    assert 'avg_apr' in snapshot
    assert snapshot['avg_apr']['value'] == pytest.approx(12.5)
    assert snapshot['avg_apr']['threshold_status'] == 'normal'
    assert isinstance(snapshot_month, pd.Timestamp)

def test_load_kpi_snapshot_from_api_success_with_dict(monkeypatch):
    monkeypatch.setenv('KPI_USE_API', '1')
    mock_client = Mock()
    mock_client.get_latest_kpis.return_value = {'kpis': [{'id': 'par_30', 'name': 'PAR 30', 'value': 8.2, 'unit': '%', 'threshold_status': 'critical', 'thresholds': {'warning': 5.0, 'critical': 7.0}, 'updated_at': '2026-03-20T10:00:00Z'}], 'timestamp': '2026-03-20T10:00:00Z'}
    with patch('frontend.streamlit_app.kpi_snapshot_loader.get_client', return_value=mock_client):
        snapshot, snapshot_month, is_api_source = load_kpi_snapshot_from_api()
    assert is_api_source is True
    assert snapshot['par_30']['threshold_status'] == 'critical'
    assert snapshot['par_30']['unit'] == '%'
    assert isinstance(snapshot_month, pd.Timestamp)

def test_load_kpi_snapshot_from_api_disabled(monkeypatch):
    monkeypatch.setenv('KPI_USE_API', '0')
    snapshot, snapshot_month, is_api_source = load_kpi_snapshot_from_api()
    assert snapshot == {}
    assert snapshot_month is None
    assert is_api_source is False

def test_load_kpi_snapshot_from_api_empty_payload(monkeypatch):
    monkeypatch.setenv('KPI_USE_API', '1')
    mock_client = Mock()
    mock_client.get_latest_kpis.return_value = {'kpis': [], 'timestamp': '2026-03-20T10:00:00Z'}
    with patch('frontend.streamlit_app.kpi_snapshot_loader.get_client', return_value=mock_client):
        snapshot, snapshot_month, is_api_source = load_kpi_snapshot_from_api()
    assert snapshot == {}
    assert snapshot_month is None
    assert is_api_source is False

def test_load_kpi_snapshot_from_api_fallback_on_error(monkeypatch):
    monkeypatch.setenv('KPI_USE_API', '1')
    with patch('frontend.streamlit_app.kpi_snapshot_loader.get_client', side_effect=ConnectionError('API down')):
        with pytest.raises(RuntimeError, match='KPI API snapshot unavailable'):
            load_kpi_snapshot_from_api()

def test_load_kpi_snapshot_from_api_prefers_websocket_when_enabled(monkeypatch):
    monkeypatch.setenv('KPI_USE_API', '1')
    monkeypatch.setenv('KPI_USE_WEBSOCKET', '1')
    ws_payload = {'event': 'kpi_snapshot', 'timestamp': '2026-03-20T10:00:00Z', 'kpis': [{'id': 'avg_apr', 'name': 'Average APR', 'value': 11.2, 'unit': '%', 'threshold_status': 'normal', 'thresholds': {'warning': 14.0, 'critical': 16.0}}]}
    with patch('frontend.streamlit_app.kpi_snapshot_loader.get_snapshot_once', return_value=ws_payload) as ws_mock:
        snapshot, snapshot_month, is_api_source = load_kpi_snapshot_from_api()
    ws_mock.assert_called_once()
    assert is_api_source is True
    assert snapshot['avg_apr']['value'] == pytest.approx(11.2)
    assert isinstance(snapshot_month, pd.Timestamp)
