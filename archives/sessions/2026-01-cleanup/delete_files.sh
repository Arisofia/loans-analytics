#!/bin/bash
# Cleanup script for unnecessary repository files
# Generated: February 2, 2026
# See CLEANUP_LOG.md for full rationale

set -e

cd "$(git rev-parse --show-toplevel)" || exit 1

echo "🧹 Starting repository cleanup..."
echo ""

# Count files first
TOTAL=0

# Session status reports
STATUS_FILES=(
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

# Temporary scripts
SCRIPT_FILES=(
  "fix_codeql_alert_136.py"
  "cleanup_old_runs.sh"
)

# Legacy build system
BUILD_FILES=(
  "build.gradle"
  "gradlew"
  "gradlew.bat"
)

# Orphaned files
ORPHAN_FILES=(
  "main.ts"
  "docker-compose.override.yml"
  "AzuriteConfig"
  "__azurite_db_table__.json"
  "profile.ps1"
)

# Function to safely delete file
delete_file() {
  if [ -f "$1" ]; then
    rm "$1"
    echo "  ✓ Deleted: $1"
    ((TOTAL++))
  elif [ -d "$1" ]; then
    rm -rf "$1"
    echo "  ✓ Deleted directory: $1"
    ((TOTAL++))
  fi
}

echo "📄 Deleting session status reports..."
for file in "${STATUS_FILES[@]}"; do
  delete_file "$file"
done

echo ""
echo "🔧 Deleting temporary scripts..."
for file in "${SCRIPT_FILES[@]}"; do
  delete_file "$file"
done

echo ""
echo "⚙️ Deleting legacy build system files..."
for file in "${BUILD_FILES[@]}"; do
  delete_file "$file"
done
delete_file "gradle"

echo ""
echo "🗑️ Deleting orphaned files..."
for file in "${ORPHAN_FILES[@]}"; do
  delete_file "$file"
done

echo ""
echo "✅ Cleanup complete! Removed $TOTAL files/directories"
echo ""
echo "📝 Summary:"
echo "  - Session reports: ${#STATUS_FILES[@]}"
echo "  - Temporary scripts: ${#SCRIPT_FILES[@]}"
echo "  - Build system files: $((${#BUILD_FILES[@]} + 1))"
echo "  - Orphaned files: ${#ORPHAN_FILES[@]}"
echo ""
echo "📋 Review changes with: git status"
echo "📖 See full rationale: archives/sessions/2026-01-cleanup/CLEANUP_LOG.md"
