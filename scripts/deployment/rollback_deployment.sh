#!/bin/bash

###############################################################################
# Rollback Abaco Analytics Dashboard Deployment
#
# This script rolls back a failed deployment to the previous working version.
#
# How it works:
# 1. Identifies the last successful deployment commit
# 2. Resets git to that commit
# 3. Re-triggers deployment from that known-good state
# 4. Validates health of rolled-back deployment
#
# Usage:
#   ./scripts/deployment/rollback_deployment.sh [COMMITS_BACK]
#
# Examples:
#   ./scripts/deployment/rollback_deployment.sh         # Rollback 1 commit
#   ./scripts/deployment/rollback_deployment.sh 3       # Rollback 3 commits
#
# Requirements:
#   - GitHub CLI (gh) installed
#   - Origin set to GitHub repository
#   - All changes committed to git
###############################################################################

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMMITS_BACK="${1:-1}"
REPO_OWNER="Arisofia"
REPO_NAME="abaco-loans-analytics"
APP_URL="${ABACO_APP_URL:-}"
HEALTH_PATH="/?page=health"

if [[ -z "$APP_URL" ]]; then
	echo -e "${RED}❌ Missing ABACO_APP_URL for post-rollback health checks.${NC}"
	echo "Set ABACO_APP_URL to your real free-tier URL (Render/Fly/Railway)."
	exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Rollback Utility${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}⚠️  WARNING: This will reset the codebase to a previous state!${NC}\n"

# Verify we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ $CURRENT_BRANCH != "main" ]]; then
	echo -e "${RED}❌ Not on 'main' branch. Rollback only works on main.${NC}"
	exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
	echo -e "${RED}❌ Uncommitted changes detected. Please commit or stash changes first.${NC}"
	git status
	exit 1
fi

# Display rollback target
TARGET_COMMIT="HEAD~$COMMITS_BACK"
echo -e "${YELLOW}Analyzing rollback target...${NC}\n"

COMMIT_HASH=$(git rev-parse "$TARGET_COMMIT" 2>/dev/null || echo "")
if [[ -z $COMMIT_HASH ]]; then
	echo -e "${RED}❌ Invalid rollback target: $COMMITS_BACK commits back${NC}"
	exit 1
fi

COMMIT_MESSAGE=$(git log -1 --format="%s" "$COMMIT_HASH")
COMMIT_DATE=$(git log -1 --format="%ci" "$COMMIT_HASH")
COMMIT_AUTHOR=$(git log -1 --format="%an" "$COMMIT_HASH")

echo "Current HEAD: $(git log -1 --oneline)"
echo ""
echo "Rolling back to:"
echo "  Commit: $COMMIT_HASH"
echo "  Message: $COMMIT_MESSAGE"
echo "  Date: $COMMIT_DATE"
echo "  Author: $COMMIT_AUTHOR"
echo ""

# Confirm rollback
read -p "Proceed with rollback? (yes/no): " CONFIRM
if [[ $CONFIRM != "yes" ]]; then
	echo "Rollback cancelled."
	exit 0
fi

echo ""
echo -e "${YELLOW}[Step 1] Resetting to target commit...${NC}"
git reset --hard "$COMMIT_HASH"
echo -e "${GREEN}✅ Reset complete${NC}\n"

echo -e "${YELLOW}[Step 2] Force-pushing to origin...${NC}"
git push --force-with-lease origin main
if [[ $? -eq 0 ]]; then
	echo -e "${GREEN}✅ Pushed to origin${NC}\n"
else
	echo -e "${RED}❌ Push failed. Please resolve and try again.${NC}"
	exit 1
fi

echo -e "${YELLOW}[Step 3] Triggering re-deployment...${NC}"

if command -v gh &>/dev/null; then
	gh workflow run deploy_dashboard.yml -R "$REPO_OWNER/$REPO_NAME" --ref main
	echo -e "${GREEN}✅ Deployment workflow triggered${NC}\n"
	echo "Monitor at: https://github.com/$REPO_OWNER/$REPO_NAME/actions/workflows/deploy_dashboard.yml"
else
	echo -e "${YELLOW}⚠️  GitHub CLI not found. Manually trigger deployment:${NC}"
	echo "GitHub -> Actions -> Deploy (Zero-Cost Free Tier) -> Run workflow"
fi

echo ""
echo -e "${YELLOW}[Step 4] Waiting for deployment (60 seconds)...${NC}"
sleep 60

echo -e "${YELLOW}[Step 5] Health check...${NC}"

for i in {1..10}; do
	if curl -f -s "$APP_URL$HEALTH_PATH" >/dev/null 2>&1; then
		echo -e "${GREEN}✅ Health check passed${NC}"
		break
	elif [[ $i -lt 10 ]]; then
		echo "Attempt $i/10 - retrying..."
		sleep 10
	else
		echo -e "${YELLOW}⚠️  Health check not responding yet${NC}"
	fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Rollback complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo "Next steps:"
echo "  1. Monitor deployment at: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
echo "  2. Check app health at: $APP_URL"
echo "  3. Review logs in the active provider dashboard for any issues"
echo "  4. Once verified stable, investigate the cause of the failed deployment"
echo ""

# Display git log for reference
echo "Recent commits (for investigation):"
git log --oneline -5
