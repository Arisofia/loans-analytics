#!/bin/bash
#
# Repository Cleanup Automation Script
# Based on: docs/REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md
# Usage: ./scripts/repo-cleanup.sh [--aggressive] [--remote] [--all]
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default flags
AGGRESSIVE=false
REMOTE=false
ALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --aggressive)
      AGGRESSIVE=true
      shift
      ;;
    --remote)
      REMOTE=true
      shift
      ;;
    --all)
      ALL=true
      AGGRESSIVE=true
      REMOTE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--aggressive] [--remote] [--all]"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Repository Cleanup & Maintenance${NC}"
echo -e "${BLUE}Version 2.0 (2026-01-29)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Verify we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo -e "${RED}✗ Error: Not in a git repository${NC}"
  exit 1
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
echo -e "${GREEN}✓ Repository: ${REPO_NAME}${NC}"
echo -e "${GREEN}✓ Current Branch: $(git branch --show-current)${NC}"
echo ""

# 2. Local Hygiene: Fetch and prune
echo -e "${YELLOW}[1/6] Fetching and pruning remote references...${NC}"
git fetch --all --prune
echo -e "${GREEN}✓ Fetch & prune complete${NC}"
echo ""

# 3. Remove untracked files (dry run first)
echo -e "${YELLOW}[2/6] Checking untracked files...${NC}"
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard | wc -l)
if [ "$UNTRACKED_COUNT" -gt 0 ]; then
  echo -e "${YELLOW}  Found ${UNTRACKED_COUNT} untracked file(s):${NC}"
  git ls-files --others --exclude-standard | head -5
  if [ "$UNTRACKED_COUNT" -gt 5 ]; then
    echo -e "${YELLOW}  ... and $((UNTRACKED_COUNT - 5)) more${NC}"
  fi
  echo -e "${YELLOW}  Run 'git clean -fd' to remove them${NC}"
else
  echo -e "${GREEN}✓ No untracked files${NC}"
fi
echo ""

# 4. Delete merged local branches
echo -e "${YELLOW}[3/6] Cleaning up merged local branches...${NC}"
MERGED_BRANCHES=$(git branch --merged | grep -v "\*" | grep -v "main" | grep -v "master" | grep -v "develop" || true)
if [ -z "$MERGED_BRANCHES" ]; then
  echo -e "${GREEN}✓ No merged branches to clean${NC}"
else
  echo -e "${YELLOW}  Merged branches found:${NC}"
  echo "$MERGED_BRANCHES" | while read branch; do
    echo -e "${YELLOW}    Deleting: $branch${NC}"
    git branch -d "$branch" 2>/dev/null || true
  done
  echo -e "${GREEN}✓ Merged branches cleaned${NC}"
fi
echo ""

# 5. Delete stale remote branches (optional)
if [ "$REMOTE" = true ]; then
  echo -e "${YELLOW}[4/6] Cleaning up stale remote branches (--remote flag active)...${NC}"
  
  # Get list of remote branches that have been deleted
  git remote prune origin --dry-run 2>/dev/null || true
  echo -e "${GREEN}✓ Remote prune complete${NC}"
  echo ""
fi

# 6. Garbage collection
echo -e "${YELLOW}[5/6] Running garbage collection...${NC}"
if [ "$AGGRESSIVE" = true ]; then
  echo -e "${YELLOW}  Mode: Aggressive (may take longer)${NC}"
  git gc --aggressive --prune=now
  echo -e "${GREEN}✓ Aggressive garbage collection complete${NC}"
else
  echo -e "${YELLOW}  Mode: Standard${NC}"
  git gc
  echo -e "${GREEN}✓ Garbage collection complete${NC}"
fi
echo ""

# 7. Repository stats
echo -e "${YELLOW}[6/6] Repository Statistics${NC}"
REPO_SIZE=$(du -sh .git | cut -f1)
OBJECT_COUNT=$(git rev-list --count --all)
COMMIT_COUNT=$(git rev-list --count HEAD)
BRANCH_COUNT=$(git branch | wc -l)
REMOTE_BRANCH_COUNT=$(git branch -r | wc -l)

echo -e "${BLUE}  Repository Size: ${REPO_SIZE}${NC}"
echo -e "${BLUE}  Total Objects: ${OBJECT_COUNT}${NC}"
echo -e "${BLUE}  Commits on HEAD: ${COMMIT_COUNT}${NC}"
echo -e "${BLUE}  Local Branches: ${BRANCH_COUNT}${NC}"
echo -e "${BLUE}  Remote References: ${REMOTE_BRANCH_COUNT}${NC}"
echo ""

# 8. Final status
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Repository cleanup complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  • Local branches cleaned"
if [ "$REMOTE" = true ]; then
  echo "  • Remote branches pruned"
fi
if [ "$AGGRESSIVE" = true ]; then
  echo "  • Aggressive garbage collection performed"
else
  echo "  • Standard garbage collection performed"
fi
echo "  • Repository statistics updated"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review any untracked files"
echo "  2. Run your test suite: pytest or npm test"
echo "  3. Commit any necessary changes"
echo ""
