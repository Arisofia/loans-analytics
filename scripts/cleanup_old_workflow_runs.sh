#!/usr/bin/env bash
#
# Cleanup Old GitHub Actions Workflow Runs
#
# This script deletes old workflow runs to reduce storage and improve performance.
# It keeps recent runs (last 30 days) and successful runs from last 90 days.
#
# Usage:
#   ./scripts/cleanup_old_workflow_runs.sh [--dry-run] [--keep-days N]
#

set -euo pipefail

# Configuration
KEEP_RECENT_DAYS="${KEEP_DAYS:-30}"
KEEP_SUCCESS_DAYS="${KEEP_SUCCESS_DAYS:-90}"
DRY_RUN=false
BATCH_SIZE=100

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --keep-days)
            KEEP_RECENT_DAYS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--keep-days N]"
            echo ""
            echo "Options:"
            echo "  --dry-run      Show what would be deleted without actually deleting"
            echo "  --keep-days N  Keep runs from last N days (default: 30)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Calculate cutoff dates
CUTOFF_DATE=$(date -u -d "$KEEP_RECENT_DAYS days ago" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
              date -u -v-${KEEP_RECENT_DAYS}d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
              echo "")

if [ -z "$CUTOFF_DATE" ]; then
    echo -e "${RED}Error: Could not calculate cutoff date${NC}"
    exit 1
fi

echo -e "${GREEN}=== GitHub Actions Workflow Cleanup ===${NC}"
echo "Cutoff date: $CUTOFF_DATE"
echo "Keep recent: last $KEEP_RECENT_DAYS days"
echo "Dry run: $DRY_RUN"
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Function to delete old runs for a workflow
cleanup_workflow() {
    local workflow_file="$1"
    local workflow_name
    workflow_name=$(basename "$workflow_file")
    
    echo -e "${YELLOW}Processing workflow: ${workflow_name}${NC}"
    
    # Get old workflow runs
    local runs_to_delete
    runs_to_delete=$(gh run list \
        --workflow="$workflow_file" \
        --limit 1000 \
        --json databaseId,conclusion,status,createdAt \
        --jq ".[] | select(.createdAt < \"$CUTOFF_DATE\" and (.conclusion == \"failure\" or .conclusion == \"cancelled\" or .conclusion == \"skipped\")) | .databaseId" \
        2>/dev/null || echo "")
    
    if [ -z "$runs_to_delete" ]; then
        echo "  No old runs to delete"
        return
    fi
    
    local count=0
    while IFS= read -r run_id; do
        if [ -n "$run_id" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo "  [DRY RUN] Would delete run: $run_id"
            else
                if gh run delete "$run_id" --yes 2>/dev/null; then
                    echo -e "  ${GREEN}✓${NC} Deleted run: $run_id"
                else
                    echo -e "  ${RED}✗${NC} Failed to delete run: $run_id"
                fi
            fi
            ((count++))
            
            # Rate limiting: pause after each batch
            if ((count % BATCH_SIZE == 0)); then
                echo "  Processed $count runs, pausing for rate limits..."
                sleep 2
            fi
        fi
    done <<< "$runs_to_delete"
    
    echo "  Total: $count runs processed"
}

# Get all workflow files
workflow_files=$(find .github/workflows -name "*.yml" -type f 2>/dev/null || echo "")

if [ -z "$workflow_files" ]; then
    echo -e "${RED}Error: No workflow files found in .github/workflows/${NC}"
    exit 1
fi

# Process each workflow
total_workflows=0
while IFS= read -r workflow_file; do
    cleanup_workflow "$workflow_file"
    ((total_workflows++))
    echo ""
done <<< "$workflow_files"

echo -e "${GREEN}=== Cleanup Complete ===${NC}"
echo "Processed $total_workflows workflows"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Note: This was a dry run. No runs were actually deleted.${NC}"
    echo "Run without --dry-run to perform actual deletion."
fi

# Show current workflow run count
echo ""
echo "Current workflow runs:"
gh run list --limit 1 --json databaseId 2>/dev/null | jq -r 'length' || echo "Unable to get count"
