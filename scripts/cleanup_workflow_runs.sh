#!/bin/bash
# Bulk delete old GitHub Actions workflow runs
# Usage: ./scripts/cleanup_workflow_runs.sh [--dry-run] [--keep-days N]

set -euo pipefail

REPO="Arisofia/abaco-loans-analytics"
KEEP_DAYS="${KEEP_DAYS:-30}"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --keep-days)
      KEEP_DAYS="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dry-run] [--keep-days N]"
      exit 1
      ;;
  esac
done

echo "🧹 GitHub Actions Workflow Runs Cleanup"
echo "Repository: $REPO"
echo "Keep runs from last: $KEEP_DAYS days"
echo "Dry run: $DRY_RUN"
echo ""

# Calculate cutoff date
if [[ "$OSTYPE" == "darwin"* ]]; then
  CUTOFF_DATE=$(date -v-${KEEP_DAYS}d -u +"%Y-%m-%dT%H:%M:%SZ")
else
  CUTOFF_DATE=$(date -u -d "${KEEP_DAYS} days ago" +"%Y-%m-%dT%H:%M:%SZ")
fi

echo "🗓️  Cutoff date: $CUTOFF_DATE"
echo ""

# Get total runs before cleanup
TOTAL_RUNS=$(gh api "/repos/$REPO/actions/runs?per_page=1" --jq '.total_count')
echo "📊 Total workflow runs before cleanup: $TOTAL_RUNS"

# Get old runs
echo "🔍 Finding runs older than $KEEP_DAYS days..."
OLD_RUNS=$(gh api "/repos/$REPO/actions/runs?per_page=100" \
  --paginate \
  --jq ".workflow_runs[] | select(.created_at < \"$CUTOFF_DATE\") | .id")

OLD_RUN_COUNT=$(echo "$OLD_RUNS" | grep -c . || echo "0")
echo "📋 Found $OLD_RUN_COUNT old runs to delete"

if [[ $OLD_RUN_COUNT -eq 0 ]]; then
  echo "✅ No old runs to delete"
  exit 0
fi

if [[ "$DRY_RUN" == true ]]; then
  echo ""
  echo "🔍 DRY RUN MODE - Would delete these runs:"
  echo "$OLD_RUNS" | head -20
  if [[ $OLD_RUN_COUNT -gt 20 ]]; then
    echo "... and $(($OLD_RUN_COUNT - 20)) more"
  fi
  echo ""
  echo "💡 Remove --dry-run flag to actually delete"
  exit 0
fi

echo ""
echo "⚠️  This will permanently delete $OLD_RUN_COUNT workflow runs"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Aborted"
  exit 1
fi

echo ""
echo "🗑️  Deleting old runs..."

DELETED=0
FAILED=0

while IFS= read -r run_id; do
  if gh api -X DELETE "/repos/$REPO/actions/runs/$run_id" &> /dev/null; then
    DELETED=$((DELETED + 1))
    if [[ $((DELETED % 10)) -eq 0 ]]; then
      echo "   Deleted $DELETED/$OLD_RUN_COUNT runs..."
    fi
  else
    FAILED=$((FAILED + 1))
  fi
done <<< "$OLD_RUNS"

echo ""
echo "✅ Cleanup complete!"
echo "   Deleted: $DELETED runs"
if [[ $FAILED -gt 0 ]]; then
  echo "   Failed: $FAILED runs"
fi

# Get total runs after cleanup
TOTAL_RUNS_AFTER=$(gh api "/repos/$REPO/actions/runs?per_page=1" --jq '.total_count')
echo "   Remaining: $TOTAL_RUNS_AFTER runs"
echo "   Freed: $(($TOTAL_RUNS - $TOTAL_RUNS_AFTER)) runs"
