from __future__ import annotations

import json
import os
import re
import argparse
from pathlib import Path
from typing import Any, Dict, Optional

import requests

ROOT = Path(__file__).resolve().parents[2]


def _parse_env(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _is_placeholder(value: Optional[str]) -> bool:
    if not value:
        return True
    lowered = value.lower()
    placeholder_tokens = (
        "xxxxxxxx",
        "your_",
        "tu_token",
        "paste",
        "<token",
        "<<",
        "changeme",
    )
    return any((token in lowered for token in placeholder_tokens))


def _validate_cli_token(cli_token: Optional[str]) -> None:
    if cli_token is None:
        return
    token = cli_token.strip()
    if not token or _is_placeholder(token):
        raise RuntimeError(
            "Invalid --token value. Replace placeholder text with a real Grafana Service Account token."
        )
    if len(token) < 20:
        raise RuntimeError(
            "Provided --token is too short. Use a full Grafana Service Account token from your Grafana stack."
        )


def _pick(key: str, env_file: Dict[str, str], env_local: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    candidates = [os.getenv(key), env_file.get(key), env_local.get(key), default]
    for candidate in candidates:
        if candidate is None:
            continue
        if _is_placeholder(candidate):
            continue
        return candidate
    return None


def _resolve_auth(
    env_file: Dict[str, str], env_local: Dict[str, str], cli_token: Optional[str] = None
) -> tuple[Dict[str, str], Optional[tuple[str, str]], str]:
    if cli_token and not _is_placeholder(cli_token):
        return ({"Authorization": f"Bearer {cli_token}"}, None, "cli_token")

    token_keys = [
        "GRAFANA_SERVICE_ACCOUNT_TOKEN",
        "GRAFANA_API_TOKEN",
        "GRAFANA_TOKEN",
        "GRAFANA_CLOUD_API_KEY",
    ]
    for key in token_keys:
        if token := _pick(key, env_file, env_local):
            return ({"Authorization": f"Bearer {token}"}, None, key)

    user = _pick("GRAFANA_USER", env_file, env_local, "admin")
    password = _pick("GRAFANA_PASSWORD", env_file, env_local) or _pick(
        "GRAFANA_ADMIN_PASSWORD", env_file, env_local
    )
    if user and password:
        return ({}, (user, password), "basic_auth")

    raise RuntimeError(
        "No Grafana auth found. Set one of: GRAFANA_SERVICE_ACCOUNT_TOKEN, "
        "GRAFANA_API_TOKEN, GRAFANA_TOKEN, or GRAFANA_USER+GRAFANA_PASSWORD."
    )


def _request(
    method: str,
    url: str,
    headers: Dict[str, str],
    auth: Optional[tuple[str, str]],
    **kwargs: Any,
) -> requests.Response:
    base_headers = {"Content-Type": "application/json"} | headers
    return requests.request(method=method, url=url, headers=base_headers, auth=auth, timeout=30, **kwargs)


def _find_datasource(base_url: str, headers: Dict[str, str], auth: Optional[tuple[str, str]], preferred_name: str) -> dict[str, Any]:
    response = _request("GET", f"{base_url}/api/datasources", headers, auth)
    if response.status_code != 200:
        if response.status_code == 401 and "api-key.invalid" in response.text:
            raise RuntimeError(
                "Grafana authentication failed: invalid API key. "
                "Use a valid Service Account token from Grafana Cloud (Stack -> Administration -> Service accounts)."
            )
        raise RuntimeError(f"Failed listing datasources ({response.status_code}): {response.text}")

    datasources = response.json() or []
    if not isinstance(datasources, list) or not datasources:
        raise RuntimeError("No datasources available in Grafana instance")

    for ds in datasources:
        if str(ds.get("name", "")).strip().lower() == preferred_name.strip().lower():
            return ds

    # Fallback to first PostgreSQL-like datasource
    for ds in datasources:
        ds_type = str(ds.get("type", "")).lower()
        if "postgres" in ds_type:
            return ds

    available = ", ".join(sorted(f"{str(ds.get('name', 'unknown'))} ({str(ds.get('type', 'unknown'))})" for ds in datasources))
    raise RuntimeError(
        "No PostgreSQL datasource found in Grafana. "
        "Create one (for Supabase) and set GRAFANA_DATASOURCE_NAME to that datasource name. "
        f"Available datasources: {available}"
    )


def _build_dashboard(uid: str, datasource_uid: str, datasource_type: str) -> dict[str, Any]:
    kpi_table_sql = (
        "SELECT kpi_key, value_num, as_of_date "
        "FROM monitoring.kpi_values "
        "WHERE as_of_date = (SELECT MAX(as_of_date) FROM monitoring.kpi_values) "
        "ORDER BY kpi_key"
    )

    def stat_sql(kpi_key: str) -> str:
        if not re.match(r'^[a-z][a-z0-9_]*$', kpi_key):
            raise ValueError(f"Invalid kpi_key: {kpi_key!r}")
        return (
            "SELECT value_num AS value "
            "FROM monitoring.kpi_values "
            "WHERE kpi_key = '" + kpi_key + "' "
            "ORDER BY as_of_date DESC "
            "LIMIT 1"
        )

    ts_sql = (
        "SELECT as_of_date::timestamp AS time, value_num AS value "
        "FROM monitoring.kpi_values "
        "WHERE kpi_key = 'npl_ratio' "
        "ORDER BY 1"
    )

    datasource = {"uid": datasource_uid, "type": datasource_type}

    return {
        "uid": uid,
        "title": "ABACO KPI Overview",
        "timezone": "browser",
        "schemaVersion": 40,
        "version": 1,
        "refresh": "30s",
        "tags": ["abaco", "kpi", "production"],
        "time": {"from": "now-90d", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "NPL Ratio (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("npl_ratio"), "format": "table"}],
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
            },
            {
                "id": 2,
                "title": "PAR 60 (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("par_60"), "format": "table"}],
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
            },
            {
                "id": 3,
                "title": "Default Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("default_rate"), "format": "table"}],
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
            },
            {
                "id": 4,
                "title": "Cure Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("cure_rate"), "format": "table"}],
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
            },
            {
                "id": 5,
                "title": "NPL Ratio Trend",
                "type": "timeseries",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": ts_sql, "format": "time_series"}],
                "gridPos": {"h": 10, "w": 24, "x": 0, "y": 8},
            },
            {
                "id": 6,
                "title": "Latest KPI Snapshot",
                "type": "table",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": kpi_table_sql, "format": "table"}],
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 18},
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision ABACO KPI dashboard in Grafana")
    parser.add_argument("--token", dest="token", default=None, help="Grafana service account token")
    parser.add_argument("--base-url", dest="base_url", default=None, help="Grafana base URL")
    parser.add_argument("--uid", dest="uid", default=None, help="Dashboard UID")
    args = parser.parse_args()
    _validate_cli_token(args.token)

    env_file = _parse_env(ROOT / ".env")
    env_local = _parse_env(ROOT / ".env.local")

    base_url = args.base_url or _pick("GRAFANA_BASE_URL", env_file, env_local, "http://localhost:3001")
    if base_url is None:
        raise RuntimeError("GRAFANA_BASE_URL is required")
    base_url = base_url.rstrip("/")

    uid = args.uid or _pick("GRAFANA_DASHBOARD_UID", env_file, env_local, "abaco-kpi-overview")
    preferred_ds_name = _pick("GRAFANA_DATASOURCE_NAME", env_file, env_local, "Supabase PostgreSQL")

    headers, auth, auth_source = _resolve_auth(env_file, env_local, cli_token=args.token)

    health = _request("GET", f"{base_url}/api/health", headers, auth)
    print(f"HEALTH_STATUS={health.status_code}")
    if health.status_code != 200:
        raise RuntimeError(f"Grafana health check failed ({health.status_code}): {health.text}")

    ds = _find_datasource(base_url, headers, auth, preferred_ds_name or "Supabase PostgreSQL")
    ds_uid = str(ds.get("uid", "")).strip()
    ds_type = str(ds.get("type", "")).strip()
    if not ds_uid or not ds_type:
        raise RuntimeError("Could not resolve datasource uid/type")

    dashboard = _build_dashboard(uid=uid or "abaco-kpi-overview", datasource_uid=ds_uid, datasource_type=ds_type)
    payload = {"dashboard": dashboard, "folderId": 0, "overwrite": True}

    upsert = _request("POST", f"{base_url}/api/dashboards/db", headers, auth, data=json.dumps(payload))
    print(f"UPSERT_STATUS={upsert.status_code}")
    if upsert.status_code not in (200, 201):
        if upsert.status_code == 401 and "api-key.invalid" in upsert.text:
            raise RuntimeError(
                "Grafana authentication failed during dashboard upsert: invalid API key. "
                "Use a valid Service Account token with dashboard write permissions."
            )
        raise RuntimeError(f"Dashboard upsert failed ({upsert.status_code}): {upsert.text}")

    result = upsert.json() if upsert.text else {}
    dashboard_uid = result.get("uid") or (uid or "abaco-kpi-overview")
    dashboard_url = f"{base_url}/d/{dashboard_uid}"

    print(f"AUTH_SOURCE={auth_source}")
    print(f"DATASOURCE_USED={ds.get('name')}|{ds_uid}|{ds_type}")
    print(f"DASHBOARD_UID={dashboard_uid}")
    print(f"DASHBOARD_URL={dashboard_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
