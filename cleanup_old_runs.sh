#!/bin/bash
set -e

echo "🧹 Starting bulk cleanup of old workflow runs..."
echo "⚠️  This will delete failed and cancelled runs older than 7 days"
echo ""

# Get timestamp for 7 days ago
CUTOFF_DATE=$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -v-7d '+%Y-%m-%dT%H:%M:%SZ')

echo "📅 Deleting runs older than: $CUTOFF_DATE"
echo ""

# Count runs to be deleted
TOTAL=$(gh run list --limit 1000 --json databaseId,status,conclusion,createdAt | \
  jq -r ".[] | select(.createdAt < \"$CUTOFF_DATE\" and (.conclusion == \"failure\" or .conclusion == \"cancelled\")) | .databaseId" | \
  wc -l | tr -d ' ')

echo "Found $TOTAL runs to delete"
echo ""

if [ "$TOTAL" -eq 0 ]; then
  echo "✅ No old runs to clean up"
  exit 0
fi

# Delete in batches
BATCH_SIZE=50
DELETED=0

gh run list --limit 1000 --json databaseId,status,conclusion,createdAt | \
  jq -r ".[] | select(.createdAt < \"$CUTOFF_DATE\" and (.conclusion == \"failure\" or .conclusion == \"cancelled\")) | .databaseId" | \
  while read -r run_id; do
    echo "Deleting run $run_id..."
    gh run delete "$run_id" --confirm 2>/dev/null || echo "  ⚠️  Failed to delete $run_id"
    DELETED=$((DELETED + 1))
    
    # Progress indicator
    if [ $((DELETED % 10)) -eq 0 ]; then
      echo "  Progress: $DELETED/$TOTAL deleted"
    fi
    
    # Rate limiting - pause every batch
    if [ $((DELETED % BATCH_SIZE)) -eq 0 ]; then
      echo "  Pausing for rate limiting..."
      sleep 2
    fi
  done

echo ""
echo "✅ Cleanup complete! Deleted $DELETED workflow runs"
