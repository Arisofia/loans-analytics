#!/bin/bash
# Delete all workflow runs except the most recent N runs
# Usage: ./scripts/maintenance/cleanup_workflow_runs_by_count.sh [--dry-run] [--keep N]

set -euo pipefail

KEEP_COUNT="${KEEP_COUNT:-25}"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
	case $1 in
	--dry-run)
		DRY_RUN=true
		shift
		;;
	--keep)
		KEEP_COUNT="$2"
		shift 2
		;;
	--help)
		echo "Usage: $0 [--dry-run] [--keep N]"
		echo ""
		echo "Options:"
		echo "  --dry-run   Show what would be deleted without actually deleting"
		echo "  --keep N    Keep the N most recent runs (default: 25)"
		echo "  --help      Show this help message"
		exit 0
		;;
	*)
		echo "Unknown option: $1"
		echo "Use --help for usage information"
		exit 1
		;;
	esac
done

echo "🧹 GitHub Actions Workflow Runs Cleanup (by count)"
echo "Keep most recent: $KEEP_COUNT runs"
echo "Dry run: $DRY_RUN"
echo ""

# Check if gh CLI is available
if ! command -v gh &>/dev/null; then
	echo "❌ Error: GitHub CLI (gh) is not installed"
	echo "Install it from: https://cli.github.com/"
	exit 1
fi

# Check authentication
if ! gh auth status &>/dev/null; then
	echo "❌ Error: Not authenticated with GitHub CLI"
	echo "Run: gh auth login"
	exit 1
fi

# Get total run count
TOTAL_RUNS=$(gh run list --limit 1 --json databaseId | jq 'length' || echo "0")
echo "📊 Fetching workflow runs..."

# Get all runs sorted by creation date (newest first)
ALL_RUNS=$(gh run list --limit 10000 --json databaseId,createdAt,conclusion,workflowName |
	jq -r 'sort_by(.createdAt) | reverse | .[].databaseId')

TOTAL_COUNT=$(echo "$ALL_RUNS" | wc -l | tr -d ' ')
echo "📋 Total workflow runs: $TOTAL_COUNT"

if [[ $TOTAL_COUNT -le $KEEP_COUNT ]]; then
	echo "✅ Current runs ($TOTAL_COUNT) <= keep count ($KEEP_COUNT). Nothing to delete."
	exit 0
fi

# Skip first N runs (most recent), delete the rest
RUNS_TO_DELETE=$(echo "$ALL_RUNS" | tail -n +$((KEEP_COUNT + 1)))
DELETE_COUNT=$(echo "$RUNS_TO_DELETE" | wc -l | tr -d ' ')

echo "🗑️  Will delete: $DELETE_COUNT runs"
echo "✅ Will keep: $KEEP_COUNT most recent runs"
echo ""

if [[ $DRY_RUN == true ]]; then
	echo "🔍 DRY RUN MODE - Would delete these runs:"
	echo "$RUNS_TO_DELETE" | head -20
	if [[ $DELETE_COUNT -gt 20 ]]; then
		echo "... and $((DELETE_COUNT - 20)) more"
	fi
	echo ""
	echo "💡 Remove --dry-run flag to actually delete"
	exit 0
fi

echo "⚠️  This will permanently delete $DELETE_COUNT workflow runs"
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
	if gh run delete "$run_id" --confirm 2>/dev/null; then
		DELETED=$((DELETED + 1))
		if [[ $((DELETED % 50)) -eq 0 ]]; then
			echo "   Deleted $DELETED/$DELETE_COUNT runs..."
		fi
	else
		FAILED=$((FAILED + 1))
	fi

	# Rate limiting: pause every 100 deletions
	if [[ $((DELETED % 100)) -eq 0 ]]; then
		echo "   Pausing for rate limits..."
		sleep 2
	fi
done <<<"$RUNS_TO_DELETE"

echo ""
echo "✅ Cleanup complete!"
echo "   Deleted: $DELETED runs"
if [[ $FAILED -gt 0 ]]; then
	echo "   Failed: $FAILED runs"
fi

# Get final count
FINAL_COUNT=$(gh run list --limit 1000 --json databaseId | jq 'length' || echo "0")
echo "   Remaining: $FINAL_COUNT runs"
echo "   Freed: $((TOTAL_COUNT - FINAL_COUNT)) runs"
