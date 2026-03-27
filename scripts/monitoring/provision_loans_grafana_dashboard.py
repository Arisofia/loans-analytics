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
            f"SELECT value_num AS value "
            f"FROM monitoring.kpi_values "
            f"WHERE kpi_key = '{kpi_key}' "  # nosec B608
            f"ORDER BY as_of_date DESC "
            f"LIMIT 1"
        )

    ts_sql = (
        "SELECT as_of_date::timestamp AS time, value_num AS value "
        "FROM monitoring.kpi_values "
        "WHERE kpi_key = 'npl_ratio' "
        "ORDER BY 1"
    )

    par_trend_sql = (
        "SELECT as_of_date::timestamp AS time, "
        "MAX(CASE WHEN kpi_key = 'par_30' THEN value_num END) AS par_30, "
        "MAX(CASE WHEN kpi_key = 'par_60' THEN value_num END) AS par_60, "
        "MAX(CASE WHEN kpi_key = 'par_90' THEN value_num END) AS par_90 "
        "FROM monitoring.kpi_values "
        "WHERE kpi_key IN ('par_30', 'par_60', 'par_90') "
        "GROUP BY as_of_date "
        "ORDER BY 1"
    )

    mom_yoy_sql = (
        "SELECT as_of_date::timestamp AS time, "
        "MAX(CASE WHEN kpi_key = 'mom_growth_pct' THEN value_num END) AS mom_growth, "
        "MAX(CASE WHEN kpi_key = 'yoy_growth_pct' THEN value_num END) AS yoy_growth "
        "FROM monitoring.kpi_values "
        "WHERE kpi_key IN ('mom_growth_pct', 'yoy_growth_pct') "
        "GROUP BY as_of_date "
        "ORDER BY 1"
    )

    monthly_volume_sql = (
        "SELECT date_trunc('month', disbursement_date)::timestamp AS time, "
        "COUNT(*) AS loan_count, "
        "SUM(disbursement_amount) AS total_disbursed "
        "FROM public.loan_data "
        "WHERE disbursement_date IS NOT NULL "
        "GROUP BY 1 ORDER BY 1"
    )

    datasource = {"uid": datasource_uid, "type": datasource_type}

    return {
        "uid": uid,
        "title": "LOANS KPI Overview",
        "timezone": "browser",
        "schemaVersion": 40,
        "version": 1,
        "refresh": "30s",
        "tags": ["loans", "kpi", "production"],
        "time": {"from": "now-90d", "to": "now"},
        "panels": [
            # Row 1: Asset Quality stats (y=0)
            {
                "id": 1,
                "title": "NPL Ratio (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("npl_ratio"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 0, "y": 0},
            },
            {
                "id": 2,
                "title": "PAR 30 (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("par_30"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 4, "y": 0},
            },
            {
                "id": 3,
                "title": "PAR 60 (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("par_60"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 8, "y": 0},
            },
            {
                "id": 4,
                "title": "PAR 90 (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("par_90"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 12, "y": 0},
            },
            {
                "id": 5,
                "title": "Default Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("default_rate"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 16, "y": 0},
            },
            {
                "id": 6,
                "title": "Cure Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("cure_rate"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 20, "y": 0},
            },
            # Row 2: Portfolio & Cash Flow stats (y=6)
            {
                "id": 7,
                "title": "Total AUM",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("total_outstanding_balance"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 0, "y": 6},
            },
            {
                "id": 8,
                "title": "Recovery Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("recovery_rate"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 4, "y": 6},
            },
            {
                "id": 9,
                "title": "Collections Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("collections_rate"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 8, "y": 6},
            },
            {
                "id": 10,
                "title": "Portfolio Yield (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("portfolio_yield"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 12, "y": 6},
            },
            {
                "id": 11,
                "title": "Repeat Borrower Rate (%)",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("repeat_borrower_rate"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 16, "y": 6},
            },
            {
                "id": 12,
                "title": "New Loans MTD",
                "type": "stat",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": stat_sql("new_loans_count_mtd"), "format": "table"}],
                "gridPos": {"h": 6, "w": 4, "x": 20, "y": 6},
            },
            # Row 3: Trend charts (y=12)
            {
                "id": 13,
                "title": "NPL Ratio Trend",
                "type": "timeseries",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": ts_sql, "format": "time_series"}],
                "gridPos": {"h": 10, "w": 12, "x": 0, "y": 12},
            },
            {
                "id": 14,
                "title": "PAR Trend (30/60/90)",
                "type": "timeseries",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": par_trend_sql, "format": "time_series"}],
                "gridPos": {"h": 10, "w": 12, "x": 12, "y": 12},
            },
            # Row 4: Full snapshot table (y=22)
            {
                "id": 15,
                "title": "Latest KPI Snapshot",
                "type": "table",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": kpi_table_sql, "format": "table"}],
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 22},
            },
            # Row 5: MoM/YoY Growth & Monthly Volume (y=34)
            {
                "id": 16,
                "title": "MoM / YoY Growth (%)",
                "type": "timeseries",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": mom_yoy_sql, "format": "time_series"}],
                "gridPos": {"h": 10, "w": 12, "x": 0, "y": 34},
            },
            {
                "id": 17,
                "title": "Monthly Disbursement Volume",
                "type": "timeseries",
                "datasource": datasource,
                "targets": [{"refId": "A", "rawSql": monthly_volume_sql, "format": "time_series"}],
                "gridPos": {"h": 10, "w": 12, "x": 12, "y": 34},
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision LOANS KPI dashboard in Grafana")
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

    uid = args.uid or _pick("GRAFANA_DASHBOARD_UID", env_file, env_local, "loans-kpi-overview")
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

    dashboard = _build_dashboard(uid=uid or "loans-kpi-overview", datasource_uid=ds_uid, datasource_type=ds_type)
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
    dashboard_uid = result.get("uid") or (uid or "loans-kpi-overview")
    dashboard_url = f"{base_url}/d/{dashboard_uid}"

    print(f"AUTH_SOURCE={'basic_auth' if auth_source == 'basic_auth' else 'token'}")
    print(f"DATASOURCE_USED={ds.get('name')}|{ds_uid}|{ds_type}")
    print(f"DASHBOARD_UID={dashboard_uid}")
    print(f"DASHBOARD_URL={dashboard_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
