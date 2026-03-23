from __future__ import annotations
import os
from urllib.parse import quote
import pytest
import requests
RUN_E2E = os.getenv('RUN_E2E', '0') == '1'
RUN_GRAFANA_E2E = os.getenv('RUN_GRAFANA_E2E', '0') == '1'
GRAFANA_BASE_URL = os.getenv('GRAFANA_BASE_URL', 'http://localhost:3001').rstrip('/')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', 'admin123')
GRAFANA_DATASOURCE_NAME = os.getenv('GRAFANA_DATASOURCE_NAME', 'Supabase PostgreSQL')
GRAFANA_DASHBOARD_UID = os.getenv('GRAFANA_DASHBOARD_UID', 'abaco-kpi-overview')
EXPECT_GRAFANA_DATA = os.getenv('EXPECT_GRAFANA_DATA', '1') == '1'
AUTH = (GRAFANA_USER, GRAFANA_PASSWORD)
pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not RUN_E2E, reason='Set RUN_E2E=1 to run E2E tests'), pytest.mark.skipif(not RUN_GRAFANA_E2E, reason='Set RUN_GRAFANA_E2E=1 to include Grafana E2E checks')]

def _grafana_up() -> bool:
    try:
        resp = requests.get(f'{GRAFANA_BASE_URL}/api/health', auth=AUTH, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False

def _iter_panels(panel_list: list[dict]) -> list[dict]:
    panels: list[dict] = []
    for panel in panel_list or []:
        panels.append(panel)
        nested = panel.get('panels')
        if isinstance(nested, list) and nested:
            panels.extend(_iter_panels(nested))
    return panels

def _rows_in_result(result: dict) -> int:
    total = 0
    for frame in result.get('frames', []) or []:
        values = (frame.get('data') or {}).get('values') or []
        if isinstance(values, list) and values and isinstance(values[0], list):
            total += len(values[0])
    return total

@pytest.fixture(scope='module')
def datasource_uid() -> str:
    health = requests.get(f'{GRAFANA_BASE_URL}/api/health', auth=AUTH, timeout=5)
    assert health.status_code == 200, f'Grafana health endpoint failed: {health.text}'
    assert health.json().get('database') == 'ok', f'Grafana DB not ready: {health.text}'
    ds_name = quote(GRAFANA_DATASOURCE_NAME, safe='')
    ds_resp = requests.get(f'{GRAFANA_BASE_URL}/api/datasources/name/{ds_name}', auth=AUTH, timeout=10)
    assert ds_resp.status_code == 200, f"Datasource '{GRAFANA_DATASOURCE_NAME}' not found: {ds_resp.text}"
    ds_uid = ds_resp.json().get('uid')
    assert ds_uid, 'Datasource UID is missing'
    ds_health = requests.get(f'{GRAFANA_BASE_URL}/api/datasources/uid/{ds_uid}/health', auth=AUTH, timeout=15)
    assert ds_health.status_code == 200, f'Datasource health endpoint failed: {ds_health.text}'
    assert ds_health.json().get('status') == 'OK', f'Datasource unhealthy: {ds_health.text}. Common causes: missing/expired DB credentials or password decryption issues.'
    return ds_uid

@pytest.mark.skipif(not _grafana_up(), reason='Grafana is not reachable')
def test_abaco_kpi_overview_queries(datasource_uid: str):
    dash_resp = requests.get(f'{GRAFANA_BASE_URL}/api/dashboards/uid/{GRAFANA_DASHBOARD_UID}', auth=AUTH, timeout=15)
    assert dash_resp.status_code == 200, f"Dashboard UID '{GRAFANA_DASHBOARD_UID}' not found: {dash_resp.text}"
    dashboard = dash_resp.json().get('dashboard') or {}
    panels = _iter_panels(dashboard.get('panels') or [])
    sql_targets: list[tuple[int, str, str]] = []
    for panel in panels:
        panel_id = int(panel.get('id', -1))
        title = str(panel.get('title', f'panel-{panel_id}'))
        for target in panel.get('targets') or []:
            raw_sql = target.get('rawSql')
            if isinstance(raw_sql, str) and raw_sql.strip():
                sql_targets.append((panel_id, title, raw_sql.strip()))
    assert sql_targets, 'No SQL targets found in ABACO KPI Overview dashboard'
    failures: list[str] = []
    total_rows = 0
    for idx, (panel_id, title, raw_sql) in enumerate(sql_targets, start=1):
        ref_id = f'P{panel_id}_{idx}'
        query_payload = {'queries': [{'refId': ref_id, 'datasource': {'uid': datasource_uid, 'type': 'grafana-postgresql-datasource'}, 'rawSql': raw_sql, 'format': 'table'}], 'from': 'now-90d', 'to': 'now'}
        query_resp = requests.post(f'{GRAFANA_BASE_URL}/api/ds/query', json=query_payload, auth=AUTH, timeout=40)
        assert query_resp.status_code == 200, f'/api/ds/query failed for panel {panel_id} ({title}): {query_resp.text}'
        result = (query_resp.json().get('results') or {}).get(ref_id) or {}
        if result.get('error'):
            failures.append(f"panel {panel_id} ({title}) -> {result.get('errorSource')}: {result.get('error')}")
            continue
        total_rows += _rows_in_result(result)
    assert not failures, 'Grafana panel queries failed:\n' + '\n'.join(failures)
    if EXPECT_GRAFANA_DATA:
        assert total_rows > 0, "ABACO KPI Overview returned zero rows across all panel queries. This indicates global 'No data' (empty tables, wrong schema, or stale ingestion)."
