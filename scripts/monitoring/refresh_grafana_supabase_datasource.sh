#!/usr/bin/env bash

set -euo pipefail

# Refresh Grafana PostgreSQL datasource credentials using Supabase CLI login-role.
# This avoids direct IPv6-only DB hosts and static DB passwords.

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-${GRAFANA_ADMIN_PASSWORD:-admin123}}"
DATASOURCE_NAME="${GRAFANA_SUPABASE_DATASOURCE_NAME:-Supabase PostgreSQL}"
SUPABASE_SCHEMAS="${SUPABASE_LOGIN_ROLE_SCHEMAS:-monitoring,public}"

for cmd in curl jq awk mktemp python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
done

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

load_env_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" == *"="* ]] || continue

    local key="${line%%=*}"
    local value="${line#*=}"
    key="${key//[[:space:]]/}"

    case "$key" in
      SUPABASE_*|GRAFANA_*|DATABASE_URL|SUPABASE_DATABASE_URL) ;;
      *) continue ;;
    esac

    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    if [[ -z "${!key:-}" ]]; then
      export "$key=$value"
    fi
  done < "$file"
}

is_placeholder_value() {
  local value="$1"
  [[ "$value" == *"your_"* || "$value" == *"_here"* || "$value" == *"<"* ]]
}

has_real_value() {
  local value="$1"
  [[ -n "$value" ]] && ! is_placeholder_value "$value"
}

parse_database_url() {
  local db_url="$1"
  python3 - "$db_url" <<'PY'
import sys
from urllib.parse import unquote, urlparse

raw = sys.argv[1]
parsed = urlparse(raw)
if parsed.scheme not in {"postgresql", "postgres"}:
    raise SystemExit(1)

host = parsed.hostname or ""
port = str(parsed.port or "")
user = unquote(parsed.username or "")
password = unquote(parsed.password or "")
database = (parsed.path or "").lstrip("/")

if not all([host, port, user, password, database]):
    raise SystemExit(2)

print(f"{host}|{port}|{user}|{password}|{database}")
PY
}

resolve_credentials_from_env() {
  local host="${SUPABASE_DB_HOST:-}"
  local port="${SUPABASE_DB_PORT:-}"
  local user="${SUPABASE_DB_USER:-}"
  local password="${SUPABASE_DB_PASSWORD:-}"
  local database="${SUPABASE_DB_NAME:-postgres}"

  if has_real_value "$host" && has_real_value "$port" && has_real_value "$user" && has_real_value "$password"; then
    echo "$host|$port|$user|$password|$database"
    return 0
  fi
  return 1
}

resolve_credentials_from_db_url() {
  local candidate
  for candidate in "${SUPABASE_DATABASE_URL:-}" "${DATABASE_URL:-}"; do
    if ! has_real_value "$candidate"; then
      continue
    fi
    if parsed="$(parse_database_url "$candidate" 2>/dev/null)"; then
      local host="${parsed%%|*}"
      local remainder="${parsed#*|}"
      local port="${remainder%%|*}"
      remainder="${remainder#*|}"
      local user="${remainder%%|*}"
      remainder="${remainder#*|}"
      local password="${remainder%%|*}"
      local database="${remainder#*|}"
      if has_real_value "$host" && has_real_value "$port" && has_real_value "$user" && has_real_value "$password" && has_real_value "$database"; then
        echo "$host|$port|$user|$password|$database"
        return 0
      fi
    fi
  done
  return 1
}

resolve_credentials_from_supabase_cli() {
  if ! command -v supabase >/dev/null 2>&1; then
    return 1
  fi

  local tmpfile
  tmpfile="$(mktemp)"
  if ! supabase db dump --linked --schema "${SUPABASE_SCHEMAS}" --dry-run >"$tmpfile" 2>/dev/null; then
    rm -f "$tmpfile"
    return 1
  fi

  extract_var() {
    local var_name="$1"
    awk -F\" -v key="$var_name" '$0 ~ ("export " key "=") { print $2; exit }' "$tmpfile"
  }

  local host port user password database
  host="$(extract_var PGHOST)"
  port="$(extract_var PGPORT)"
  user="$(extract_var PGUSER)"
  password="$(extract_var PGPASSWORD)"
  database="$(extract_var PGDATABASE)"
  rm -f "$tmpfile"

  if has_real_value "$host" && has_real_value "$port" && has_real_value "$user" && has_real_value "$password" && has_real_value "$database"; then
    echo "$host|$port|$user|$password|$database"
    return 0
  fi
  return 1
}

load_env_file "${project_root}/.env.monitoring"
load_env_file "${project_root}/.env.local"
load_env_file "${project_root}/.env"

if ! curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/health" >/dev/null; then
  echo "Grafana is not reachable at ${GRAFANA_URL}" >&2
  exit 1
fi

credentials=""
if credentials="$(resolve_credentials_from_env)"; then
  source_hint="SUPABASE_DB_* env vars"
elif credentials="$(resolve_credentials_from_db_url)"; then
  source_hint="DATABASE_URL/SUPABASE_DATABASE_URL"
elif credentials="$(resolve_credentials_from_supabase_cli)"; then
  source_hint="supabase CLI login-role"
else
  echo "Could not resolve PostgreSQL credentials." >&2
  echo "Provide SUPABASE_DB_HOST/SUPABASE_DB_USER/SUPABASE_DB_PASSWORD or DATABASE_URL, or link/login Supabase CLI." >&2
  exit 1
fi

pg_host="${credentials%%|*}"
rest="${credentials#*|}"
pg_port="${rest%%|*}"
rest="${rest#*|}"
pg_user="${rest%%|*}"
rest="${rest#*|}"
pg_password="${rest%%|*}"
pg_database="${rest#*|}"

datasource_json="$(curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/datasources" \
  | jq -c --arg name "$DATASOURCE_NAME" '.[] | select(.name == $name)' \
  | head -n 1)"

if [[ -z "$datasource_json" || "$datasource_json" == "null" ]]; then
  echo "Grafana datasource not found: ${DATASOURCE_NAME}" >&2
  exit 1
fi

datasource_uid="$(jq -r '.uid' <<<"$datasource_json")"

payload="$(jq -n \
  --arg name "$DATASOURCE_NAME" \
  --arg host "$pg_host" \
  --arg port "$pg_port" \
  --arg database "$pg_database" \
  --arg user "$pg_user" \
  --arg password "$pg_password" \
  '{
    name: $name,
    type: "grafana-postgresql-datasource",
    access: "proxy",
    isDefault: true,
    editable: true,
    url: ($host + ":" + $port),
    database: $database,
    user: $user,
    jsonData: {
      sslmode: "require",
      postgresVersion: 1400,
      timescaledb: false,
      maxOpenConns: 20,
      maxIdleConns: 2,
      connMaxLifetime: 14400,
      database: $database
    },
    secureJsonData: {
      password: $password
    }
  }'
)"

response_body="$(mktemp)"
http_code="$(
  curl -sS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -o "$response_body" \
  -w "%{http_code}" \
  -X PUT "${GRAFANA_URL}/api/datasources/uid/${datasource_uid}" \
  -d "$payload"
)"
if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
  echo "Datasource update failed (HTTP ${http_code})." >&2
  cat "$response_body" >&2
  rm -f "$response_body"
  exit 1
fi
rm -f "$response_body"

health_status="$(curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  "${GRAFANA_URL}/api/datasources/uid/${datasource_uid}/health" | jq -r '.status // "ERROR"')"

if [[ "$health_status" != "OK" ]]; then
  echo "Datasource update completed but health check is not OK." >&2
  exit 1
fi

echo "Datasource '${DATASOURCE_NAME}' refreshed: ${pg_host}:${pg_port} as ${pg_user}"
echo "Credential source: ${source_hint}"
echo "Note: login-role credentials are temporary; rerun this script if panels return 'No data' again."
