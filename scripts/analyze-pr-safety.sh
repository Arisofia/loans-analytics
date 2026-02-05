#!/usr/bin/env bash
# Comprehensive PR Safety Analysis Script
# Analyzes open PRs for safety, compliance, and merge readiness

set -euo pipefail

echo "═══════════════════════════════════════════════════════════════"
echo "     PR SAFETY ANALYSIS - COMPREHENSIVE REVIEW"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gh CLI is available
if ! command -v gh &>/dev/null; then
	echo -e "${RED}❌ GitHub CLI (gh) not found. Install with: brew install gh${NC}"
	exit 1
fi

# Check if authenticated
if ! gh auth status &>/dev/null; then
	echo -e "${YELLOW}⚠️  Not authenticated with GitHub CLI${NC}"
	echo "Run: gh auth login"
	exit 1
fi

echo -e "${BLUE}📊 Fetching open PRs...${NC}"
echo ""

# Get all open PRs
OPEN_PRS=$(gh pr list --repo Arisofia/abaco-loans-analytics --state open --json number,title,headRefName,mergeable,author --limit 20)

if [[ $(echo "${OPEN_PRS}" | jq '. | length') -eq 0 ]]; then
	echo -e "${GREEN}✅ No open PRs found${NC}"
	exit 0
fi

echo "Total open PRs: $(echo "${OPEN_PRS}" | jq '. | length')"
echo ""

# Categorize PRs
COPILOT_PRS=$(echo "${OPEN_PRS}" | jq '[.[] | select(.headRefName | contains("copilot"))]')
DEPENDABOT_PRS=$(echo "${OPEN_PRS}" | jq '[.[] | select(.headRefName | contains("dependabot"))]')
OTHER_PRS=$(echo "${OPEN_PRS}" | jq '[.[] | select((.headRefName | contains("dependabot") | not) and (.headRefName | contains("copilot") | not))]')

echo "═══════════════════════════════════════════════════════════════"
echo " CATEGORY 1: STALE COPILOT PRS (SHOULD BE CLOSED)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

COPILOT_COUNT=$(echo "${COPILOT_PRS}" | jq '. | length')

if [[ ${COPILOT_COUNT} -eq 0 ]]; then
	echo -e "${GREEN}✅ No Copilot PRs found${NC}"
else
	echo -e "${YELLOW}Found ${COPILOT_COUNT} Copilot PR(s)${NC}"
	echo ""

	echo "${COPILOT_PRS}" | jq -r '.[] | "PR #\(.number): \(.title)\n  Branch: \(.headRefName)\n  Status: ⚠️  STALE - Should be closed\n"'

	echo -e "${RED}⚠️  ACTION REQUIRED:${NC}"
	echo "These PRs are based on older commits and would remove:"
	echo "  - diagnose-rls.sh"
	echo "  - load-env.sh"
	echo "  - RLS governance improvements"
	echo ""
	echo "Recommended action:"
	echo '  gh pr close <PR_NUMBER> --comment "❌ Closing as stale - removes critical RLS diagnostic tools"'
	echo ""
fi

echo "═══════════════════════════════════════════════════════════════"
echo " CATEGORY 2: DEPENDABOT PRS (REQUIRE CI ANALYSIS)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

DEPENDABOT_COUNT=$(echo "${DEPENDABOT_PRS}" | jq '. | length')

if [[ ${DEPENDABOT_COUNT} -eq 0 ]]; then
	echo -e "${GREEN}✅ No Dependabot PRs found${NC}"
else
	echo -e "${BLUE}Found ${DEPENDABOT_COUNT} Dependabot PR(s)${NC}"
	echo ""

	# Analyze each Dependabot PR
	echo "${DEPENDABOT_PRS}" | jq -r '.[].number' | while read -r PR_NUM; do
		echo "─────────────────────────────────────────────────────────"
		echo -e "${BLUE}PR #${PR_NUM}${NC}"

		PR_INFO=$(gh pr view "${PR_NUM}" --json title,statusCheckRollup,mergeable)
		TITLE=$(echo "${PR_INFO}" | jq -r '.title')
		MERGEABLE=$(echo "${PR_INFO}" | jq -r '.mergeable')

		echo "Title: ${TITLE}"
		echo "Mergeable: ${MERGEABLE}"
		echo ""

		# Count check statuses
		TOTAL_CHECKS=$(echo "${PR_INFO}" | jq '[.statusCheckRollup[] | select(.__typename == "CheckRun")] | length')
		PASSED=$(echo "${PR_INFO}" | jq '[.statusCheckRollup[] | select(.__typename == "CheckRun" and .conclusion == "SUCCESS")] | length')
		FAILED=$(echo "${PR_INFO}" | jq '[.statusCheckRollup[] | select(.__typename == "CheckRun" and .conclusion == "FAILURE")] | length')
		NEUTRAL=$(echo "${PR_INFO}" | jq '[.statusCheckRollup[] | select(.__typename == "CheckRun" and .conclusion == "NEUTRAL")] | length')

		echo "CI Status:"
		echo "  ✅ Passed: ${PASSED}/${TOTAL_CHECKS}"
		echo "  ❌ Failed: ${FAILED}/${TOTAL_CHECKS}"
		echo "  ⚪ Neutral: ${NEUTRAL}/${TOTAL_CHECKS}"
		echo ""

		# List failed checks
		if [[ ${FAILED} -gt 0 ]]; then
			echo -e "${RED}❌ Failed Checks:${NC}"
			echo "${PR_INFO}" | jq -r '.statusCheckRollup[] | select(.__typename == "CheckRun" and .conclusion == "FAILURE") | "  - \(.name)"'
			echo ""

			# Decision
			echo -e "${YELLOW}⚠️  DECISION: DO NOT MERGE${NC}"
			echo "Reason: CI checks failing"
			echo "Action: Investigate or close"
		else
			if [[ ${MERGEABLE} == "MERGEABLE" ]]; then
				echo -e "${GREEN}✅ SAFE TO MERGE${NC}"
				echo "All CI checks passed, no conflicts"
			else
				echo -e "${YELLOW}⚠️  CONFLICTS DETECTED${NC}"
				echo "Reason: Merge conflicts with main"
				echo "Action: Rebase or close"
			fi
		fi
		echo ""
	done
fi

echo "═══════════════════════════════════════════════════════════════"
echo " CATEGORY 3: OTHER PRS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

OTHER_COUNT=$(echo "${OTHER_PRS}" | jq '. | length')

if [[ ${OTHER_COUNT} -eq 0 ]]; then
	echo -e "${GREEN}✅ No other PRs found${NC}"
else
	echo "${OTHER_PRS}" | jq -r '.[] | "PR #\(.number): \(.title)\n  Author: \(.author.login)\n  Branch: \(.headRefName)\n"'
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " SUMMARY & RECOMMENDED ACTIONS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Stale Copilot PRs: ${COPILOT_COUNT}"
if [[ ${COPILOT_COUNT} -gt 0 ]]; then
	echo "   → CLOSE ALL (remove RLS tools)"
	echo "${COPILOT_PRS}" | jq -r '.[].number' | while read -r num; do
		echo "     gh pr close ${num} --comment \"❌ Stale - removes RLS diagnostic tools\""
	done
fi

echo ""
echo "2️⃣  Dependabot PRs: ${DEPENDABOT_COUNT}"
if [[ ${DEPENDABOT_COUNT} -gt 0 ]]; then
	# Count safe vs unsafe
	SAFE_COUNT=0
	UNSAFE_COUNT=0

	echo "${DEPENDABOT_PRS}" | jq -r '.[].number' | while read -r PR_NUM; do
		PR_INFO=$(gh pr view "${PR_NUM}" --json statusCheckRollup,mergeable 2>/dev/null || echo '{}')
		FAILED=$(echo "${PR_INFO}" | jq '[.statusCheckRollup[]? | select(.__typename == "CheckRun" and .conclusion == "FAILURE")] | length')

		if [[ ${FAILED} -gt 0 ]]; then
			((UNSAFE_COUNT++)) || true
		else
			((SAFE_COUNT++)) || true
		fi
	done

	echo "   → Safe to merge: ${SAFE_COUNT}"
	echo "   → Failing CI: ${UNSAFE_COUNT}"
fi

echo ""
echo "3️⃣  Other PRs: ${OTHER_COUNT}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " COMPLETE - Review recommendations above"
echo "═══════════════════════════════════════════════════════════════"
