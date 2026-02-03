#!/bin/bash

# restore_dashboards.sh - Import dashboards from backup to Grafana
# Usage: ./scripts/restore_dashboards.sh [backup-directory]
# Default: grafana/dashboards/backups/latest/

set -euo pipefail

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
BACKUP_DIR="${1:-grafana/dashboards/backups/latest}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "♻️  Grafana Dashboard Restore"
echo "================================"
echo "Grafana URL: ${GRAFANA_URL}"
echo "Backup directory: ${BACKUP_DIR}"
echo ""

# Check if backup directory exists
if [ ! -d "${BACKUP_DIR}" ]; then
    echo -e "${RED}❌ ERROR: Backup directory does not exist: ${BACKUP_DIR}${NC}"
    echo "Available backups:"
    ls -1 grafana/dashboards/backups/ 2>/dev/null || echo "  (none)"
    exit 1
fi

# Check if Grafana is accessible
if ! curl -s -f -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Cannot connect to Grafana at ${GRAFANA_URL}${NC}"
    echo "Ensure Grafana is running: make monitoring-start"
    exit 1
fi

# Get Prometheus datasource UID
echo "🔍 Looking up Prometheus datasource..."
DATASOURCE_UID=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    "${GRAFANA_URL}/api/datasources" | \
    python3 -c "
import sys, json
datasources = json.load(sys.stdin)
for ds in datasources:
    if ds.get('type') == 'prometheus':
        print(ds['uid'])
        break
" || echo "")

if [ -z "${DATASOURCE_UID}" ]; then
    echo -e "${RED}❌ ERROR: No Prometheus datasource found${NC}"
    echo "Configure datasource first: scripts/auto_start_monitoring.sh"
    exit 1
fi

echo -e "${GREEN}✓ Prometheus datasource UID: ${DATASOURCE_UID}${NC}"
echo ""

# Find all dashboard JSON files
DASHBOARD_FILES=$(find "${BACKUP_DIR}" -name "*.json" ! -name "manifest.json" 2>/dev/null || echo "")

if [ -z "${DASHBOARD_FILES}" ]; then
    echo -e "${YELLOW}⚠️  No dashboard files found in ${BACKUP_DIR}${NC}"
    exit 0
fi

TOTAL_COUNT=$(echo "${DASHBOARD_FILES}" | wc -l | tr -d ' ')
echo -e "${BLUE}📋 Found ${TOTAL_COUNT} dashboard file(s)${NC}"
echo ""

# Restore each dashboard
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

while IFS= read -r FILE; do
    FILENAME=$(basename "${FILE}")
    echo "📤 Restoring: ${FILENAME}"
    
    # Check if file is valid JSON
    if ! python3 -c "import json; json.load(open('${FILE}'))" 2>/dev/null; then
        echo -e "  ${RED}✗ Invalid JSON file${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        continue
    fi
    
    # Prepare import payload
    IMPORT_PAYLOAD=$(python3 <<EOF
import json, sys

# Load backup file
with open('${FILE}', 'r') as f:
    backup = json.load(f)

# Extract dashboard (handle both formats)
if 'dashboard' in backup:
    dashboard = backup['dashboard']
else:
    dashboard = backup

# Update datasource UIDs
def update_datasource(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'datasource' and isinstance(value, dict):
                obj[key] = {'type': 'prometheus', 'uid': '${DATASOURCE_UID}'}
            elif key == 'datasource' and isinstance(value, str):
                obj[key] = '${DATASOURCE_UID}'
            elif isinstance(value, (dict, list)):
                update_datasource(value)
    elif isinstance(obj, list):
        for item in obj:
            update_datasource(item)

update_datasource(dashboard)

# Remove internal IDs
dashboard.pop('id', None)
dashboard.pop('version', None)

# Create import payload
payload = {
    'dashboard': dashboard,
    'overwrite': True,
    'message': 'Restored from backup'
}

print(json.dumps(payload))
EOF
)
    
    # Import to Grafana
    RESPONSE=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -H "Content-Type: application/json" \
        -X POST "${GRAFANA_URL}/api/dashboards/db" \
        -d "${IMPORT_PAYLOAD}")
    
    # Check response
    STATUS=$(echo "${RESPONSE}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'error'))
except:
    print('error')
")
    
    if [ "${STATUS}" = "success" ]; then
        DASHBOARD_URL=$(echo "${RESPONSE}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('url', ''))
except:
    pass
")
        echo -e "  ${GREEN}✓ Imported successfully${NC}"
        if [ -n "${DASHBOARD_URL}" ]; then
            echo -e "  ${BLUE}→ ${GRAFANA_URL}${DASHBOARD_URL}${NC}"
        fi
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        ERROR_MSG=$(echo "${RESPONSE}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('message', 'Unknown error'))
except:
    print('Invalid response')
")
        echo -e "  ${RED}✗ Failed: ${ERROR_MSG}${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
done <<< "${DASHBOARD_FILES}"

# Summary
echo "================================"
echo "📊 Restore Summary"
echo "  Source: ${BACKUP_DIR}"
echo "  Total: ${TOTAL_COUNT}"
echo -e "  ${GREEN}Success: ${SUCCESS_COUNT}${NC}"
if [ ${FAILED_COUNT} -gt 0 ]; then
    echo -e "  ${RED}Failed: ${FAILED_COUNT}${NC}"
fi
if [ ${SKIPPED_COUNT} -gt 0 ]; then
    echo -e "  ${YELLOW}Skipped: ${SKIPPED_COUNT}${NC}"
fi
echo ""

# Show backup manifest if available
if [ -f "${BACKUP_DIR}/manifest.txt" ]; then
    echo "📄 Backup Manifest:"
    head -n 10 "${BACKUP_DIR}/manifest.txt"
    echo ""
fi

# Exit with error if any failures
if [ ${FAILED_COUNT} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some dashboards failed to restore${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Restore completed successfully${NC}"
echo "View dashboards: ${GRAFANA_URL}/dashboards"
