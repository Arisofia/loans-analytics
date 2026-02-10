#!/usr/bin/env bash
# Update all Dependabot PRs to rebase against current main
# Fixes CI failures caused by stale base branch 8fbe75801

set -euo pipefail

REPO="Arisofia/abaco-loans-analytics"
PRS=(247 246 245 244 243 241 240 239 238 237)

echo "═══════════════════════════════════════════════════════════════"
echo "  Updating ${#PRS[@]} Dependabot PRs to latest main"
echo "═══════════════════════════════════════════════════════════════"
echo ""

for pr_num in "${PRS[@]}"; do
	echo "Updating PR #${pr_num}..."

	# Try API method (requires maintainer permissions)
	if gh api "repos/${REPO}/pulls/${pr_num}/update-branch" \
		-X PUT -H "Accept: application/vnd.github+json" 2>/dev/null; then
		echo "✅ PR #${pr_num} updated successfully"
	else
		echo "⚠️  PR #${pr_num} requires manual update (open in browser):"
		gh pr view "${pr_num}" --json url --jq '.url'
	fi

	echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "  Update complete. CI checks will re-run automatically."
echo "═══════════════════════════════════════════════════════════════"
