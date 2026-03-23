import json
import time
from typing import Any, cast
from fastapi.testclient import TestClient
from backend.python.apps.analytics.api.main import app
client = TestClient(cast(Any, app))

def test_nsm_endpoint_returns_empty_response_when_no_runs_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.get('/analytics/nsm')
    assert response.status_code == 200
    body = response.json()
    assert body['latest_period'] is None
    assert body['latest'] is None
    assert body['by_period'] == {}

def test_nsm_endpoint_returns_empty_response_when_no_artifact(tmp_path, monkeypatch):
    run_dir = tmp_path / 'logs' / 'runs' / '20260101_abc12345'
    run_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    response = client.get('/analytics/nsm')
    assert response.status_code == 200
    body = response.json()
    assert body['latest_period'] is None
    assert body['latest'] is None
    assert body['by_period'] == {}

def test_nsm_endpoint_happy_path(tmp_path, monkeypatch):
    run_dir = tmp_path / 'logs' / 'runs' / '20260201_def67890'
    run_dir.mkdir(parents=True)
    nsm_payload = {'latest_period': '2026-01', 'latest': {'tpv_total': 10000.0, 'tpv_recurrent': 6000.0, 'tpv_new': 3000.0, 'tpv_recovered': 1000.0, 'active_clients': 20, 'recurrent_clients': 12, 'new_clients': 6, 'recovered_clients': 2}, 'by_period': {'2026-01': {'tpv_total': 10000.0, 'tpv_recurrent': 6000.0, 'tpv_new': 3000.0, 'tpv_recovered': 1000.0, 'active_clients': 20, 'recurrent_clients': 12, 'new_clients': 6, 'recovered_clients': 2}}}
    (run_dir / 'nsm_recurrent_tpv.json').write_text(json.dumps(nsm_payload))
    monkeypatch.chdir(tmp_path)
    response = client.get('/analytics/nsm')
    assert response.status_code == 200
    body = response.json()
    assert body['latest_period'] == '2026-01'
    assert body['latest']['tpv_recurrent'] == 6000.0
    assert body['latest']['tpv_new'] == 3000.0
    assert body['latest']['tpv_recovered'] == 1000.0
    assert body['latest']['active_clients'] == 20
    assert '2026-01' in body['by_period']
    assert body['by_period']['2026-01']['recurrent_clients'] == 12

def test_nsm_endpoint_supports_current_output_filename(tmp_path, monkeypatch):
    run_dir = tmp_path / 'logs' / 'runs' / '20260201_def67890'
    run_dir.mkdir(parents=True)
    nsm_payload = {'latest_period': '2026-01', 'latest': {'tpv_total': 20000.0, 'tpv_recurrent': 15000.0, 'tpv_new': 4000.0, 'tpv_recovered': 1000.0, 'active_clients': 30, 'recurrent_clients': 18, 'new_clients': 9, 'recovered_clients': 3}, 'by_period': {'2026-01': {'tpv_total': 20000.0, 'tpv_recurrent': 15000.0, 'tpv_new': 4000.0, 'tpv_recovered': 1000.0, 'active_clients': 30, 'recurrent_clients': 18, 'new_clients': 9, 'recovered_clients': 3}}}
    (run_dir / 'nsm_recurrent_tpv_output.json').write_text(json.dumps(nsm_payload))
    monkeypatch.chdir(tmp_path)
    response = client.get('/analytics/nsm')
    assert response.status_code == 200
    body = response.json()
    assert body['latest_period'] == '2026-01'
    assert body['latest']['tpv_recurrent'] == 15000.0
    assert body['by_period']['2026-01']['recovered_clients'] == 3

def test_nsm_endpoint_schema_completeness(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.get('/analytics/nsm')
    assert response.status_code == 200
    body = response.json()
    assert 'latest_period' in body
    assert 'latest' in body
    assert 'by_period' in body

def test_nsm_endpoint_selects_most_recently_modified_run(tmp_path, monkeypatch):
    runs_root = tmp_path / 'logs' / 'runs'
    runs_root.mkdir(parents=True)
    old_run = runs_root / '20260101_aaa00000'
    old_run.mkdir()
    (old_run / 'nsm_recurrent_tpv.json').write_text(json.dumps({'latest_period': '2025-12', 'latest': None, 'by_period': {}}))
    time.sleep(0.1)
    new_run = runs_root / '20260201_bbb11111'
    new_run.mkdir()
    (new_run / 'nsm_recurrent_tpv.json').write_text(json.dumps({'latest_period': '2026-01', 'latest': None, 'by_period': {}}))
    monkeypatch.chdir(tmp_path)
    response = client.get('/analytics/nsm')
    assert response.status_code == 200
    assert response.json()['latest_period'] == '2026-01'
