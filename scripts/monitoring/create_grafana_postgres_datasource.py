from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote, unquote, urlparse

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


def _pick(key: str, env_file: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key) or env_file.get(key) or default
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_database_url(database_url: str) -> Dict[str, str]:
    parsed = urlparse(database_url)
    if not parsed.hostname:
        raise RuntimeError("DATABASE_URL/SUPABASE_DATABASE_URL has no hostname")
    if not parsed.path or parsed.path == "/":
        raise RuntimeError("DATABASE_URL/SUPABASE_DATABASE_URL has no database name")

    user = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    host = parsed.hostname
    port = str(parsed.port or 5432)
    database = parsed.path.lstrip("/")

    if not user or not password:
        raise RuntimeError("DATABASE_URL/SUPABASE_DATABASE_URL must include user and password")

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }


def _get_host_from_env(env_file: Dict[str, str]) -> Optional[str]:
    if host := _pick("SUPABASE_DB_HOST", env_file):
        return host

    if not (supabase_url := _pick("SUPABASE_URL", env_file)):
        return None

    parsed = urlparse(supabase_url)
    project_ref = parsed.hostname.split(".")[0] if parsed.hostname else ""
    return f"db.{project_ref}.supabase.co" if project_ref else None


def _validate_db_config(host: Optional[str], user: Optional[str], password: Optional[str], database: Optional[str]) -> list[str]:
    return [
        name
        for name, value in (
            ("host (SUPABASE_DB_HOST or derivable from SUPABASE_URL)", host),
            ("password (SUPABASE_DB_PASSWORD/PGPASSWORD or SUPABASE_DATABASE_URL)", password),
            ("user (SUPABASE_DB_USER or SUPABASE_DATABASE_URL)", user),
            ("database (SUPABASE_DB_NAME or SUPABASE_DATABASE_URL)", database),
        )
        if not value
    ]


def _build_db_config(env_file: Dict[str, str]) -> Dict[str, str]:
    host = _get_host_from_env(env_file)
    port = _pick("SUPABASE_DB_PORT", env_file, "5432")
    database = _pick("SUPABASE_DB_NAME", env_file, "postgres")
    user = _pick("SUPABASE_DB_USER", env_file, "postgres")
    password = _pick("SUPABASE_DB_PASSWORD", env_file) or _pick("PGPASSWORD", env_file)

    # Prefer explicit DB fields when provided (e.g., Supabase pooler host/user)
    # and only fall back to DATABASE_URL parsing when these are not configured.
    explicit_fields_present = bool(
        _pick("SUPABASE_DB_HOST", env_file)
        or _pick("SUPABASE_DB_USER", env_file)
        or _pick("SUPABASE_DB_PASSWORD", env_file)
    )
    if not explicit_fields_present:
        if database_url := _pick("SUPABASE_DATABASE_URL", env_file) or _pick("DATABASE_URL", env_file):
            return _parse_database_url(database_url)

    if missing := _validate_db_config(host, user, password, database):
        raise RuntimeError("Missing PostgreSQL settings: " + ", ".join(missing))

    return {
        "user": user or "",
        "password": password or "",
        "host": host or "",
        "port": port or "5432",
        "database": database or "postgres",
    }


def _request(method: str, url: str, token: str, **kwargs: Any) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return requests.request(method=method, url=url, headers=headers, timeout=30, **kwargs)


def _upsert_datasource(base_url: str, token: str, name: str, db: Dict[str, str]) -> Dict[str, Any]:
    payload = {
        "name": name,
        "type": "grafana-postgresql-datasource",
        "url": f"{db['host']}:{db['port']}",
        "access": "proxy",
        "database": db["database"],
        "user": db["user"],
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {
            "sslmode": "require",
            "postgresVersion": 1500,
            "timescaledb": False,
        },
        "secureJsonData": {
            "password": db["password"],
        },
    }

    existing = _request("GET", f"{base_url}/api/datasources/name/{quote(name, safe='')}", token)
    if existing.status_code == 200:
        ds_id = existing.json().get("id")
        if not ds_id:
            raise RuntimeError("Datasource exists but no id returned by Grafana")
        update = _request("PUT", f"{base_url}/api/datasources/{ds_id}", token, data=json.dumps(payload))
        if update.status_code != 200:
            raise RuntimeError(f"Datasource update failed ({update.status_code}): {update.text}")
        return update.json()

    if existing.status_code != 404:
        raise RuntimeError(f"Datasource lookup failed ({existing.status_code}): {existing.text}")

    create = _request("POST", f"{base_url}/api/datasources", token, data=json.dumps(payload))
    if create.status_code not in (200, 201):
        raise RuntimeError(f"Datasource create failed ({create.status_code}): {create.text}")
    return create.json()


def _health_check(base_url: str, token: str, uid: str) -> Dict[str, Any]:
    health = _request("GET", f"{base_url}/api/datasources/uid/{uid}/health", token)
    if health.status_code != 200:
        raise RuntimeError(f"Datasource health check failed ({health.status_code}): {health.text}")
    return health.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create/update Grafana PostgreSQL datasource for Supabase")
    parser.add_argument("--token", required=True, help="Grafana Service Account token")
    parser.add_argument("--base-url", default=None, help="Grafana base URL")
    parser.add_argument("--name", default=None, help="Datasource name")
    args = parser.parse_args()

    env_file = _parse_env(ROOT / ".env")
    base_url = (args.base_url or _pick("GRAFANA_BASE_URL", env_file, "https://jenineferderas.grafana.net") or "").rstrip("/")
    ds_name = args.name or _pick("GRAFANA_DATASOURCE_NAME", env_file, "Supabase PostgreSQL") or "Supabase PostgreSQL"

    db = _build_db_config(env_file)
    result = _upsert_datasource(base_url, args.token.strip(), ds_name, db)

    uid = result.get("datasource", {}).get("uid") or result.get("uid")
    if not uid:
        check = _request("GET", f"{base_url}/api/datasources/name/{quote(ds_name, safe='')}", args.token.strip())
        if check.status_code != 200:
            raise RuntimeError("Datasource created but UID could not be resolved")
        uid = check.json().get("uid")

    if not uid:
        raise RuntimeError("Datasource UID not found after create/update")

    health = _health_check(base_url, args.token.strip(), uid)

    print(f"DATASOURCE_NAME={ds_name}")
    print(f"DATASOURCE_UID={uid}")
    print(f"HEALTH_STATUS={health.get('status')}")
    print(f"HEALTH_MESSAGE={health.get('message')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
