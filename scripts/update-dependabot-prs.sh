#!/usr/bin/env bash
# update-dependabot-prs.sh
# Update all Dependabot PRs to rebase against current main
# Fixes CI failures caused by stale base branch 8fbe75801
#
# Usage: bash scripts/update-dependabot-prs.sh

set -euo pipefail

REPO="Arisofia/abaco-loans-analytics"
PRS=(247 246 245 244 243 241 240 239 238 237)

echo "═══════════════════════════════════════════════════════════════"
echo "  Updating ${#PRS[@]} Dependabot PRs to latest main"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Base: 8fbe75801 (stale - missing f-string fix)"
echo "Target: $(git rev-parse --short HEAD) (current main - includes fixes)"
echo ""

SUCCESS=0
MANUAL=0

for pr_num in "${PRS[@]}"; do
	echo "Updating PR #${pr_num}..."

	# Try API method (requires maintainer permissions)
	if gh api "repos/${REPO}/pulls/${pr_num}/update-branch" \
		-X PUT -H "Accept: application/vnd.github+json" 2>/dev/null; then
		echo "✅ PR #${pr_num} updated successfully"
		((SUCCESS++))
	else
		echo "⚠️  PR #${pr_num} requires manual update:"
		gh pr view "${pr_num}" --json url --jq '.url'
		((MANUAL++))
	fi

	echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "  Update Summary"
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Automated updates: ${SUCCESS}/${#PRS[@]}"
echo "⚠️  Manual updates needed: ${MANUAL}/${#PRS[@]}"
echo ""
echo "CI checks will re-run automatically for updated PRs."
echo "Verify with: bash scripts/analyze-pr-safety.sh"
echo "═══════════════════════════════════════════════════════════════"
