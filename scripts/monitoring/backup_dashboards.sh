#!/bin/bash

# backup_dashboards.sh - Export all Grafana dashboards to JSON files
# Usage: ./scripts/monitoring/backup_dashboards.sh [output-directory]
# Default output: grafana/dashboards/backups/YYYY-MM-DD_HH-MM-SS/

set -euo pipefail

# Configuration
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
BACKUP_DIR="${1:-grafana/dashboards/backups}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR="${BACKUP_DIR}/${TIMESTAMP}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔄 Grafana Dashboard Backup"
echo "================================"
echo "Grafana URL: ${GRAFANA_URL}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Check if Grafana is accessible
if ! curl -s -f -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "${GRAFANA_URL}/api/health" >/dev/null 2>&1; then
	echo -e "${RED}❌ ERROR: Cannot connect to Grafana at ${GRAFANA_URL}${NC}"
	echo "Ensure Grafana is running: make monitoring-start"
	exit 1
fi

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Get list of all dashboards
echo "📋 Fetching dashboard list..."
DASHBOARDS=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
	"${GRAFANA_URL}/api/search?type=dash-db" |
	python3 -c "
import sys, json
data = json.load(sys.stdin)
for d in data:
    print(f\"{d['uid']}|{d['title']}|{d.get('folderTitle', 'General')}\")
")

if [ -z "${DASHBOARDS}" ]; then
	echo -e "${YELLOW}⚠️  No dashboards found${NC}"
	exit 0
fi

DASHBOARD_COUNT=$(echo "${DASHBOARDS}" | wc -l | tr -d ' ')
echo -e "${GREEN}✓ Found ${DASHBOARD_COUNT} dashboard(s)${NC}"
echo ""

# Export each dashboard
SUCCESS_COUNT=0
FAILED_COUNT=0

while IFS='|' read -r uid title folder; do
	echo "📥 Exporting: ${title} (folder: ${folder})"

	# Sanitize filename
	SAFE_TITLE=$(echo "${title}" | tr ' /' '_' | tr -cd '[:alnum:]_-')
	SAFE_FOLDER=$(echo "${folder}" | tr ' /' '_' | tr -cd '[:alnum:]_-')
	FILENAME="${SAFE_FOLDER}__${SAFE_TITLE}.json"

	# Fetch dashboard JSON
	DASHBOARD_JSON=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
		"${GRAFANA_URL}/api/dashboards/uid/${uid}")

	# Check if successful
	if echo "${DASHBOARD_JSON}" | grep -q '"dashboard"'; then
		# Extract dashboard object and pretty-print
		echo "${DASHBOARD_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
dashboard = data.get('dashboard', {})
# Remove internal IDs for portability
dashboard.pop('id', None)
dashboard.pop('version', None)
# Add metadata
metadata = {
    'uid': '${uid}',
    'title': '${title}',
    'folder': '${folder}',
    'exported_at': '${TIMESTAMP}',
    'grafana_url': '${GRAFANA_URL}'
}
output = {
    'dashboard': dashboard,
    'metadata': metadata
}
print(json.dumps(output, indent=2, sort_keys=True))
" >"${OUTPUT_DIR}/${FILENAME}"

		echo -e "  ${GREEN}✓ Saved to ${FILENAME}${NC}"
		SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
	else
		echo -e "  ${RED}✗ Failed to export ${title}${NC}"
		FAILED_COUNT=$((FAILED_COUNT + 1))
	fi
	echo ""
done <<<"${DASHBOARDS}"

# Create backup manifest
cat >"${OUTPUT_DIR}/manifest.txt" <<EOF
Grafana Dashboard Backup
========================
Date: ${TIMESTAMP}
Grafana URL: ${GRAFANA_URL}
Total Dashboards: ${DASHBOARD_COUNT}
Successfully Exported: ${SUCCESS_COUNT}
Failed: ${FAILED_COUNT}

Dashboard List:
EOF

while IFS='|' read -r uid title folder; do
	SAFE_TITLE=$(echo "${title}" | tr ' /' '_' | tr -cd '[:alnum:]_-')
	SAFE_FOLDER=$(echo "${folder}" | tr ' /' '_' | tr -cd '[:alnum:]_-')
	FILENAME="${SAFE_FOLDER}__${SAFE_TITLE}.json"
	echo "- ${title} (${folder}) → ${FILENAME}" >>"${OUTPUT_DIR}/manifest.txt"
done <<<"${DASHBOARDS}"

# Summary
echo "================================"
echo "📊 Backup Summary"
echo "  Location: ${OUTPUT_DIR}"
echo "  Total: ${DASHBOARD_COUNT}"
echo -e "  ${GREEN}Success: ${SUCCESS_COUNT}${NC}"
if [ ${FAILED_COUNT} -gt 0 ]; then
	echo -e "  ${RED}Failed: ${FAILED_COUNT}${NC}"
fi
echo ""
echo "Manifest: ${OUTPUT_DIR}/manifest.txt"

# Create latest symlink
if [ -L "${BACKUP_DIR}/latest" ]; then
	rm "${BACKUP_DIR}/latest"
fi
ln -s "${TIMESTAMP}" "${BACKUP_DIR}/latest"
echo "Latest backup: ${BACKUP_DIR}/latest → ${TIMESTAMP}"

# Exit with error if any failures
if [ ${FAILED_COUNT} -gt 0 ]; then
	exit 1
fi

echo -e "\n${GREEN}✅ Backup completed successfully${NC}"
