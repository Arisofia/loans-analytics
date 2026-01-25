#!/bin/bash
set -euo pipefail
# Automate KPI table sync to Figma at 8 AM daily

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
SYNC_SCRIPT="$WORKSPACE/scripts/sync_kpi_table_to_figma.py"
LOG_PATH="$WORKSPACE/exports/figma_sync.log"

# Add to crontab: 0 8 * * * /bin/bash /path/to/this/script.sh
mkdir -p "$(dirname "$LOG_PATH")"

if ! command -v python3 >/dev/null 2>&1; then
  printf '%b\n' "Python3 is not available on PATH; aborting."
  exit 1
fi

if [ ! -f "$SYNC_SCRIPT" ]; then
  printf '%b\n' "Sync script not found: $SYNC_SCRIPT - nothing to run"
  exit 0
fi

python3 "$SYNC_SCRIPT" >> "$LOG_PATH" 2>&1
