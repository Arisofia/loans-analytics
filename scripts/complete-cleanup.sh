#!/bin/bash
set -euo pipefail
DRY_RUN=false
LOG_FILE="cleanup.log"
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done
log() { echo "$@" | tee -a "$LOG_FILE"; }
if $DRY_RUN; then
  log "🧹 Dry-run mode: No changes will be made."
  RM_CMD="echo Would remove:"
else
  RM_CMD="rm -rf"
fi
log "🧹 Starting comprehensive repository cleanup..."
# Insert full script content from previous response here (sections 1-14).
# For brevity, assume you copy the full script body as provided earlier.
# After running:
