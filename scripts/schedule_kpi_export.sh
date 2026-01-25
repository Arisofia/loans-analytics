#!/bin/bash
# Automate KPI table export at 8 AM daily

WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_PATH="$WORKSPACE/scripts/export_kpi_table_to_csv.py"
LOG_PATH="$WORKSPACE/exports/kpi_export.log"

# Add to crontab: 0 8 * * * /bin/bash /path/to/this/script.sh
python3 "$SCRIPT_PATH" >> "$LOG_PATH" 2>&1
