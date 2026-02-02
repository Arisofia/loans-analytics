#!/bin/bash
# Execute the repository cleanup
# This script will actually delete the unnecessary files

set -e

cd "$(dirname "$0")/../../.." || exit 1

echo "🧹 Executing repository cleanup..."
echo "📍 Working directory: $(pwd)"
echo ""

# Arrays of files to delete
declare -a STATUS_FILES=(
  "AUTOMATION_COMPLETE.md"
  "AUTOMATION_SUMMARY.md"
  "COMPLETION_SUMMARY.md"
  "COMPREHENSIVE_FIXES_APPLIED.md"
  "COMPREHENSIVE_STATUS_REPORT.md"
  "CRITICAL_FIX_COMPLETED.md"
  "FINAL_COMPLETION_SUMMARY.md"
  "FINAL_FIXES_APPLIED.md"
  "FINAL_RESOLUTION_COMPLETE.md"
  "FINAL_STATUS_REPORT.md"
  "SESSION_COMPLETE.md"
  "STATUS_REPORT.md"
  "WORKFLOW_FIXES_SUMMARY.md"
  "WORKFLOW_RESOLUTION_COMPLETE.md"
  "WORKFLOW_STATUS_FINAL.md"
  "WORKFLOW_STATUS_REPORT.md"
  "FIX_ALL_WORKFLOWS.md"
)

declare -a TEMP_SCRIPTS=(
  "fix_codeql_alert_136.py"
  "cleanup_old_runs.sh"
)

declare -a BUILD_FILES=(
  "build.gradle"
  "gradlew"
  "gradlew.bat"
  "gradle"
)

declare -a ORPHAN_FILES=(
  "main.ts"
  "docker-compose.override.yml"
  "AzuriteConfig"
  "__azurite_db_table__.json"
  "profile.ps1"
)

DELETED_COUNT=0

delete_item() {
  local item="$1"
  if [ -f "$item" ]; then
    rm "$item" && echo "  ✓ Deleted file: $item" && ((DELETED_COUNT++))
  elif [ -d "$item" ]; then
    rm -rf "$item" && echo "  ✓ Deleted directory: $item" && ((DELETED_COUNT++))
  fi
}

echo "📄 Deleting session status reports (${#STATUS_FILES[@]} files)..."
for file in "${STATUS_FILES[@]}"; do
  delete_item "$file"
done

echo ""
echo "🔧 Deleting temporary scripts (${#TEMP_SCRIPTS[@]} files)..."
for file in "${TEMP_SCRIPTS[@]}"; do
  delete_item "$file"
done

echo ""
echo "⚙️  Deleting legacy build system (${#BUILD_FILES[@]} items)..."
for file in "${BUILD_FILES[@]}"; do
  delete_item "$file"
done

echo ""
echo "🗑️  Deleting orphaned files (${#ORPHAN_FILES[@]} files)..."
for file in "${ORPHAN_FILES[@]}"; do
  delete_item "$file"
done

echo ""
echo "✅ Cleanup complete! Deleted $DELETED_COUNT items"
echo ""
echo "📊 Next steps:"
echo "  1. Review changes: git status"
echo "  2. Stage deletions: git add -A"
echo "  3. Commit: git commit -m 'chore: remove 28 unnecessary files from root directory'"
echo ""
echo "📖 Full documentation: archives/sessions/2026-01-cleanup/CLEANUP_LOG.md"
