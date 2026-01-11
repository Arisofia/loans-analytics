#!/bin/bash

##############################################################################
# Script: resolve_merge_conflicts.sh
# Description: Automatically resolves merge conflicts by keeping HEAD version
#              and lists all files with unresolved conflicts for review
# Usage: ./scripts/resolve_merge_conflicts.sh [--auto-resolve] [--dry-run]
# Options:
#   --auto-resolve  Automatically resolve conflicts (removes merge markers)
#   --dry-run       Show what would be done without making changes
##############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
AUTO_RESOLVE=false
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-resolve)
            AUTO_RESOLVE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--auto-resolve] [--dry-run]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Merge Conflict Resolution Tool${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Get list of files with unresolved conflicts
echo -e "${YELLOW}Scanning for files with unresolved merge conflicts...${NC}"
echo ""

CONFLICT_FILES=$(git diff --name-only --diff-filter=U)

if [ -z "$CONFLICT_FILES" ]; then
    echo -e "${GREEN}✓ No unresolved merge conflicts found${NC}"
    echo ""
    exit 0
fi

# Count conflicts
CONFLICT_COUNT=$(echo "$CONFLICT_FILES" | wc -l)
echo -e "${RED}Found $CONFLICT_COUNT file(s) with unresolved conflicts:${NC}"
echo ""

# Display conflicted files
echo -e "${YELLOW}Files requiring manual review or auto-resolution:${NC}"
while IFS= read -r file; do
    echo -e "  ${RED}✗${NC} $file"
done <<< "$CONFLICT_FILES"
echo ""

# If auto-resolve flag is not set, just list and exit
if [ "$AUTO_RESOLVE" = false ]; then
    echo -e "${YELLOW}Run with --auto-resolve flag to automatically resolve these conflicts${NC}"
    echo -e "${YELLOW}(keeping HEAD version)${NC}"
    exit 0
fi

echo -e "${YELLOW}Starting automatic conflict resolution...${NC}"
echo ""

# Auto-resolve conflicts by keeping HEAD version
RESOLVED_COUNT=0
ERROR_COUNT=0

while IFS= read -r file; do
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would resolve: $file (keeping HEAD version)"
        ((RESOLVED_COUNT++))
    else
        # Extract the HEAD version and remove merge markers
        if git show :1:"$file" > /dev/null 2>&1; then
            # Get the HEAD version (ours/stage 2)
            git show :2:"$file" > "$file" 2>/dev/null || true
            
            # Mark as resolved
            git add "$file"
            
            echo -e "${GREEN}✓${NC} Resolved: $file (kept HEAD version)"
            ((RESOLVED_COUNT++))
        else
            echo -e "${RED}✗${NC} Error resolving: $file"
            ((ERROR_COUNT++))
        fi
    fi
done <<< "$CONFLICT_FILES"

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Resolution Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Total conflicts found: ${YELLOW}$CONFLICT_COUNT${NC}"
echo -e "Successfully resolved: ${GREEN}$RESOLVED_COUNT${NC}"
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "Resolution errors: ${RED}$ERROR_COUNT${NC}"
fi
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}This was a dry-run. No changes were made.${NC}"
    echo -e "${YELLOW}Run without --dry-run to apply changes.${NC}"
    echo ""
elif [ "$ERROR_COUNT" -eq 0 ] && [ "$RESOLVED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}All conflicts resolved! Stage the changes with:${NC}"
    echo -e "  ${BLUE}git add .${NC}"
    echo -e "  ${BLUE}git commit -m \"Resolve merge conflicts (kept HEAD version)\"${NC}"
    echo ""
fi

exit 0
