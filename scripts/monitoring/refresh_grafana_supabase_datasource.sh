#!/usr/bin/env bash

set -euo pipefail

# Refresh Grafana PostgreSQL datasource credentials using Supabase CLI login-role.
# This avoids direct IPv6-only DB hosts and static DB passwords.

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-${GRAFANA_ADMIN_PASSWORD:-admin123}}"
DATASOURCE_NAME="${GRAFANA_SUPABASE_DATASOURCE_NAME:-Supabase PostgreSQL}"
SUPABASE_SCHEMAS="${SUPABASE_LOGIN_ROLE_SCHEMAS:-monitoring,public}"

for cmd in supabase curl jq awk mktemp; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
done

if ! curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/health" >/dev/null; then
  echo "Grafana is not reachable at ${GRAFANA_URL}" >&2
  exit 1
fi

tmpfile="$(mktemp)"
cleanup() {
  rm -f "$tmpfile"
}
trap cleanup EXIT

if ! supabase db dump --linked --schema "${SUPABASE_SCHEMAS}" --dry-run >"$tmpfile" 2>/dev/null; then
  echo "Failed to initialize Supabase login-role credentials. Ensure Supabase CLI is authenticated and project is linked." >&2
  exit 1
fi

extract_var() {
  local var_name="$1"
  awk -F\" -v key="$var_name" '$0 ~ ("export " key "=") { print $2; exit }' "$tmpfile"
}

pg_host="$(extract_var PGHOST)"
pg_port="$(extract_var PGPORT)"
pg_user="$(extract_var PGUSER)"
pg_password="$(extract_var PGPASSWORD)"
pg_database="$(extract_var PGDATABASE)"

if [[ -z "$pg_host" || -z "$pg_port" || -z "$pg_user" || -z "$pg_password" || -z "$pg_database" ]]; then
  echo "Could not extract PostgreSQL login-role credentials from Supabase CLI output." >&2
  exit 1
fi

datasource_uid="$(curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/datasources" \
  | jq -r --arg name "$DATASOURCE_NAME" '.[] | select(.name == $name) | .uid' \
  | head -n 1)"

if [[ -z "$datasource_uid" || "$datasource_uid" == "null" ]]; then
  echo "Grafana datasource not found: ${DATASOURCE_NAME}" >&2
  exit 1
fi

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

curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  -H "Content-Type: application/json" \
  -X PUT "${GRAFANA_URL}/api/datasources/uid/${datasource_uid}" \
  -d "$payload" >/dev/null

health_status="$(curl -fsS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
  "${GRAFANA_URL}/api/datasources/uid/${datasource_uid}/health" | jq -r '.status // "ERROR"')"

if [[ "$health_status" != "OK" ]]; then
  echo "Datasource update completed but health check is not OK." >&2
  exit 1
fi

echo "Datasource '${DATASOURCE_NAME}' refreshed: ${pg_host}:${pg_port} as ${pg_user}"
echo "Note: login-role credentials are temporary; rerun this script if panels return 'No data' again."
