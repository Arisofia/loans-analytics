#!/bin/bash
# Bulk delete old workflow runs to reduce from 26K to manageable number

set -e

REPO="Arisofia/abaco-loans-analytics"
KEEP_RECENT=50  # Keep last 50 runs
DRY_RUN=${1:-false}

echo "🧹 Workflow Run Cleanup Script"
echo "Repository: $REPO"
echo "Keep recent: $KEEP_RECENT runs"
echo "Dry run: $DRY_RUN"
echo ""

# Get total count
TOTAL=$(gh run list --repo "$REPO" --limit 1000 --json databaseId --jq 'length')
echo "📊 Found $TOTAL workflow runs (showing first 1000)"

# Get runs to delete (skip first KEEP_RECENT)
echo "🔍 Fetching runs to delete..."
RUNS_TO_DELETE=$(gh run list --repo "$REPO" --limit 1000 --json databaseId,status,conclusion,createdAt --jq ".[$KEEP_RECENT:][] | .databaseId")

DELETE_COUNT=$(echo "$RUNS_TO_DELETE" | wc -l | tr -d ' ')
echo "🗑️  Will delete $DELETE_COUNT runs"

if [ "$DRY_RUN" = "true" ]; then
    echo "✅ Dry run complete - no runs deleted"
    exit 0
fi

# Delete runs in batches
echo "🚀 Starting deletion..."
COUNTER=0
for RUN_ID in $RUNS_TO_DELETE; do
    COUNTER=$((COUNTER + 1))
    if gh run delete "$RUN_ID" --repo "$REPO" 2>/dev/null; then
        echo "✓ Deleted run $RUN_ID ($COUNTER/$DELETE_COUNT)"
    else
        echo "✗ Failed to delete run $RUN_ID"
    fi
    
    # Rate limiting: pause every 50 deletions
    if [ $((COUNTER % 50)) -eq 0 ]; then
        echo "⏸️  Pausing for rate limits..."
        sleep 5
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo "📉 Deleted $COUNTER workflow runs"
echo "📊 Remaining runs: ~$KEEP_RECENT (plus any created during cleanup)"
