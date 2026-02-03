#!/bin/bash
#
# Import Grafana Dashboard
# Automatically imports pre-configured dashboards into Grafana
#

set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-${GRAFANA_ADMIN_PASSWORD:-admin123}}"
DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../grafana/dashboards" && pwd)"

echo "📊 Importing Grafana Dashboards..."
echo "Grafana URL: $GRAFANA_URL"
echo "Dashboard directory: $DASHBOARD_DIR"
echo ""

# Check if Grafana is accessible
if ! curl -sf "$GRAFANA_URL/api/health" >/dev/null 2>&1; then
    echo "❌ Grafana is not accessible at $GRAFANA_URL"
    echo "Run: make monitoring-start"
    exit 1
fi

# Get datasource UID
DATASOURCE_UID=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    "$GRAFANA_URL/api/datasources/name/Prometheus" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['uid'])" 2>/dev/null || echo "")

if [[ -z "$DATASOURCE_UID" ]]; then
    echo "❌ Prometheus datasource not found in Grafana"
    echo "Run: make monitoring-start"
    exit 1
fi

echo "✓ Prometheus datasource UID: $DATASOURCE_UID"
echo ""

# Import all dashboards
IMPORTED=0
FAILED=0

for dashboard_file in "$DASHBOARD_DIR"/*.json; do
    if [[ ! -f "$dashboard_file" ]]; then
        continue
    fi

    DASHBOARD_NAME=$(basename "$dashboard_file" .json)
    echo "Importing: $DASHBOARD_NAME..."

    # Create import payload with Python
    IMPORT_PAYLOAD=$(python3 << EOF
import json

# Read dashboard file
with open('$dashboard_file', 'r') as f:
    dashboard = json.load(f)

# Update datasource references
def update_datasources(obj):
    if isinstance(obj, dict):
        for key, value in list(obj.items()):
            if key == 'datasource' and isinstance(value, str):
                obj[key] = {
                    'type': 'prometheus',
                    'uid': '$DATASOURCE_UID'
                }
            else:
                update_datasources(value)
    elif isinstance(obj, list):
        for item in obj:
            update_datasources(item)

update_datasources(dashboard)

# Wrap for import API
import_payload = {
    'dashboard': dashboard.get('dashboard', dashboard),
    'overwrite': True,
    'inputs': [],
    'folderId': 0
}

print(json.dumps(import_payload))
EOF
)

    # Import dashboard
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        "$GRAFANA_URL/api/dashboards/import" \
        -d "$IMPORT_PAYLOAD" 2>&1)

    if echo "$RESPONSE" | grep -q "imported\|uid"; then
        DASHBOARD_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('importedUrl', ''))" 2>/dev/null || echo "")
        echo "  ✓ Imported successfully"
        if [[ -n "$DASHBOARD_URL" ]]; then
            echo "  📊 URL: $GRAFANA_URL$DASHBOARD_URL"
        fi
        ((IMPORTED++))
    else
        echo "  ❌ Failed to import"
        echo "  Response: $RESPONSE"
        ((FAILED++))
    fi
    echo ""
done

echo "========================================="
echo "Import Summary:"
echo "  ✓ Imported: $IMPORTED"
if [[ $FAILED -gt 0 ]]; then
    echo "  ❌ Failed: $FAILED"
fi
echo "========================================="

if [[ $IMPORTED -gt 0 ]]; then
    echo ""
    echo "🎉 Dashboards are ready!"
    echo "Visit: $GRAFANA_URL/dashboards"
fi

exit 0
