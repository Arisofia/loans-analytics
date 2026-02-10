#!/bin/bash

###############################################################################
# Deploy Abaco Loans Analytics Dashboard to Azure App Service
#
# This script automates the deployment process:
# 1. Validates local state (git, tests, dependencies)
# 2. Ensures main branch is clean and pushed
# 3. Triggers GitHub Actions workflow
# 4. Monitors deployment status
# 5. Performs post-deployment health checks
#
# Usage:
#   ./scripts/deploy_to_azure.sh
#
# Requirements:
#   - GitHub CLI (gh) installed and authenticated
#   - All local changes committed
#   - AZURE_CREDENTIALS or AZURE_WEBAPP_PUBLISH_PROFILE secret in GitHub
#   - curl for health checks
###############################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="Arisofia"
REPO_NAME="abaco-loans-analytics"
WORKFLOW_NAME="deployment.yml"
APP_URL="https://abaco-loans-dashboard.azurewebsites.net"
HEALTH_CHECK_PATH="/?page=health"
MAX_HEALTH_CHECK_ATTEMPTS=10
HEALTH_CHECK_INTERVAL=30

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Abaco Analytics Deployment Automation${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Step 1: Validate local state
echo -e "${YELLOW}[Step 1] Validating local repository state...${NC}"

if ! command -v gh &>/dev/null; then
	echo -e "${RED}❌ GitHub CLI (gh) not found. Please install: https://github.com/cli/cli${NC}"
	exit 1
fi

git_status_output=$(git status -s)
if [[ -n ${git_status_output} ]]; then
	echo -e "${RED}❌ Uncommitted changes detected. Please commit all changes first.${NC}"
	git status
	exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)
if [[ ${CURRENT_BRANCH} != "main" ]]; then
	echo -e "${RED}❌ Not on 'main' branch. Currently on: ${CURRENT_BRANCH}${NC}"
	exit 1
fi

echo -e "${GREEN}✅ Local state is clean${NC}\n"

# Step 2: Verify branch is synced with remote
echo -e "${YELLOW}[Step 2] Syncing with remote...${NC}"

git fetch origin main
LOCAL_COMMIT=$(git rev-parse main)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [[ ${LOCAL_COMMIT} != "${REMOTE_COMMIT}" ]]; then
	echo -e "${RED}❌ Local and remote main branches differ.${NC}"
	echo "Local: ${LOCAL_COMMIT}"
	echo "Remote: ${REMOTE_COMMIT}"
	echo "Please pull/push to sync."
	exit 1
fi

echo -e "${GREEN}✅ main branch is synced with origin/main${NC}"
echo "Latest commit: $(git log -1 --oneline || true)"
echo ""

# Step 3: Validate tests pass locally
echo -e "${YELLOW}[Step 3] Running local tests...${NC}"

if [[ -f ".venv/bin/activate" ]]; then
	source .venv/bin/activate
fi

if command -v pytest &>/dev/null; then
	if pytest tests/ -q --tb=line; then
		echo -e "${GREEN}✅ All tests passed${NC}\n"
	else
		echo -e "${RED}❌ Tests failed. Fix issues before deploying.${NC}"
		exit 1
	fi
else
	echo -e "${YELLOW}⚠️  pytest not found, skipping local tests${NC}\n"
fi

# Step 4: Check GitHub secrets exist
echo -e "${YELLOW}[Step 4] Checking GitHub deployment secrets...${NC}"

if gh secret list -R "${REPO_OWNER}/${REPO_NAME}" | grep -qE "AZURE_CREDENTIALS|AZURE_WEBAPP_PUBLISH_PROFILE"; then
	echo -e "${GREEN}✅ Azure deployment secrets configured${NC}\n"
else
	echo -e "${RED}❌ Neither AZURE_CREDENTIALS nor AZURE_WEBAPP_PUBLISH_PROFILE found.${NC}"
	echo "Add one of these secrets to GitHub: Settings → Secrets and variables → Actions"
	exit 1
fi

# Step 5: Trigger GitHub Actions workflow
echo -e "${YELLOW}[Step 5] Triggering GitHub Actions deployment...${NC}"

WORKFLOW_RUN=$(gh workflow run "${WORKFLOW_NAME}" -R "${REPO_OWNER}/${REPO_NAME}" --ref main 2>&1 | grep -oP '(?<=Run ID: )\d+' || echo "")

if [[ -z ${WORKFLOW_RUN} ]]; then
	# Try alternative approach if previous didn't work
	echo "Attempting alternative workflow trigger..."
	gh workflow run "${WORKFLOW_NAME}" -R "${REPO_OWNER}/${REPO_NAME}" --ref main
	sleep 5
	WORKFLOW_RUN=$(gh run list -R "${REPO_OWNER}/${REPO_OWNER}/${REPO_NAME}" -w "${WORKFLOW_NAME}" --limit 1 --json databaseId -q '.[0].databaseId')
fi

if [[ -z ${WORKFLOW_RUN} ]]; then
	echo -e "${YELLOW}⚠️  Could not capture workflow run ID automatically.${NC}"
	echo "Visit: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_NAME}"
	echo "to monitor the deployment manually."
else
	echo -e "${GREEN}✅ Workflow triggered: Run ID ${WORKFLOW_RUN}${NC}"
	echo "Monitor at: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/runs/${WORKFLOW_RUN}"
fi

echo ""

# Step 6: Wait for deployment to complete
echo -e "${YELLOW}[Step 6] Waiting for deployment to complete (this may take 5-15 minutes)...${NC}"
echo "Check workflow status above while we wait..."
echo ""

if [[ -n ${WORKFLOW_RUN} ]]; then
	# Poll workflow status
	for _ in {1..60}; do
		STATUS=$(gh run view "${WORKFLOW_RUN}" -R "${REPO_OWNER}/${REPO_NAME}" --json conclusion -q '.conclusion' 2>/dev/null || echo "pending")

		if [[ ${STATUS} == "success" ]]; then
			echo -e "${GREEN}✅ Deployment workflow completed successfully${NC}\n"
			break
		elif [[ ${STATUS} == "failure" ]]; then
			echo -e "${RED}❌ Deployment workflow failed${NC}"
			echo "View logs: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/runs/${WORKFLOW_RUN}"
			exit 1
		else
			echo -n "."
			sleep 10
		fi
	done
fi

# Step 7: Wait for App Service to be ready
echo ""
echo -e "${YELLOW}[Step 7] Waiting for Azure App Service to initialize (60 seconds)...${NC}"
sleep 60
echo -e "${GREEN}✅ Initialization period complete${NC}\n"

# Step 8: Health check
echo -e "${YELLOW}[Step 8] Running post-deployment health checks...${NC}"

HEALTH_CHECK_URL="${APP_URL}${HEALTH_CHECK_PATH}"
ATTEMPT=0
SUCCESS=false

while [[ ${ATTEMPT} -lt ${MAX_HEALTH_CHECK_ATTEMPTS} ]]; do
	ATTEMPT=$((ATTEMPT + 1))
	echo "Health check attempt ${ATTEMPT}/${MAX_HEALTH_CHECK_ATTEMPTS}..."

	if RESPONSE=$(curl -f -s -o /dev/null -w "%{http_code}" "${HEALTH_CHECK_URL}" 2>/dev/null); then
		if [[ ${RESPONSE} == "200" ]]; then
			echo -e "${GREEN}✅ Health check passed (HTTP 200)${NC}"
			SUCCESS=true
			break
		else
			echo "HTTP ${RESPONSE} - retrying..."
		fi
	else
		echo "Connection failed - retrying..."
	fi

	if [[ ${ATTEMPT} -lt ${MAX_HEALTH_CHECK_ATTEMPTS} ]]; then
		sleep "${HEALTH_CHECK_INTERVAL}"
	fi
done

if [[ ${SUCCESS} == false ]]; then
	echo -e "${YELLOW}⚠️  Health check did not pass in ${MAX_HEALTH_CHECK_ATTEMPTS} attempts${NC}"
	echo "The app may still be initializing. Check status at:"
	echo "  - URL: ${APP_URL}"
	echo "  - Azure Portal: https://portal.azure.com"
	echo "  - Logs: Tail App Service logs for details"
else
	echo ""
	echo -e "${GREEN}✅ App is healthy and responding${NC}"
	echo "Access your dashboard: ${BLUE}${APP_URL}${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "Branch: main"
echo "Commit: $(git log -1 --oneline || true)"
echo "Workflow: ${WORKFLOW_NAME}"
if [[ -n ${WORKFLOW_RUN} ]]; then
	echo "Run ID: ${WORKFLOW_RUN}"
fi
echo "App URL: ${APP_URL}"
echo ""
echo -e "${GREEN}✅ Deployment automation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Visit ${APP_URL} to verify the app loads"
echo "  2. Test key features (upload, analysis, dashboards)"
echo "  3. Monitor logs in Azure Portal for the next 24 hours"
echo "  4. Confirm scheduled workflows run successfully"
echo ""
