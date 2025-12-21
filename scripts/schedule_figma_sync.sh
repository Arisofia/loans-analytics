#!/bin/bash
# Automate KPI table sync to Figma at 8 AM daily

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
SYNC_SCRIPT="$WORKSPACE/scripts/sync_kpi_table_to_figma.py"
LOG_PATH="$WORKSPACE/exports/figma_sync.log"

# Add to crontab: 0 8 * * * /bin/bash /path/to/this/script.sh
python3 "$SYNC_SCRIPT" >> "$LOG_PATH" 2>&1
