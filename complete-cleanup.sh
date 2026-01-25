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
  RM_CMD=(echo "Would remove")
else
  RM_CMD=(rm -rf)
fi

log "🧹 Starting comprehensive repository cleanup..."

log "📁 Removing external integration scripts and directories..."
${RM_CMD[@]} \
  scripts/post_to_slack.py \
  scripts/fetch_cascade_data.py \
  scripts/upload_to_figma.py \
  scripts/sync_kpi_table_to_figma.py \
  scripts/export_figma_file_data.py \
  scripts/export_chart_for_figma.py \
  scripts/schedule_figma_sync.sh \
  scripts/update_figma_slides.js \
  scripts/notion-actions.js

log "🗂️ Removing integration code modules (if present)..."
${RM_CMD[@]} src/integrations/slack_client.py \
  src/integrations/figma_client.py \
  src/integrations/notion_client.py \
  src/integrations/hubspot_client.py

log "🧹 Removing integration-specific data exports..."
${RM_CMD[@]} data/raw/looker_exports

log "🧹 Removing integration workflow files..."
${RM_CMD[@]} \
  .github/workflows/cascade_ingest.yml \
  .github/workflows/daily-ingest.yml \
  .github/workflows/comment-to-figma.yml \
  .github/workflows/export-figma-file-data.yml \
  .github/workflows/kpi-csv-sync-to-figma.yml \
  .github/workflows/meta-to-figma-dashboard.yml \
  .github/workflows/supabase-figma-scheduled.yml

log "🗂️ Removing Looker-specific files/references..."
find . -type f \( -name "*looker*" -o -name "*Looker*" \) \
  -not -path "./.git/*" -not -path "./.venv/*" -not -path "./node_modules/*" \
  -exec ${RM_CMD[@]} {} + 2>/dev/null || true

log "🧹 Removing integration references from configs/docs..."
if command -v rg >/dev/null 2>&1; then
  rg -l -i "slack|notion|figma|cascade|hubspot|looker" \
    --glob '!node_modules/**' --glob '!.git/**' \
    | xargs -r sed -i -e 's/[sS]lack//g' -e 's/[nN]otion//g' -e 's/[fF]igma//g' \
      -e 's/[cC]ascade//g' -e 's/[hH]ubspot//g' -e 's/[lL]ooker//g' || true
fi

log "🔧 Unifying configs (integrations.yml into pipeline.yml if present)..."
if [ -f config/integrations.yml ]; then
  cat config/integrations.yml >> config/pipeline.yml
  ${RM_CMD[@]} config/integrations.yml
  log "✅ Unified integrations into pipeline.yml"
fi

log "✅ Cleanup complete. Review cleanup.log and git status."
