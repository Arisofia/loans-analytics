#!/usr/bin/env bash
# close-stale-dependabot-prs.sh
# Close all stale Dependabot PRs to trigger recreation against fresh main
# Alternative to update-dependabot-prs.sh when rebasing isn't working
#
# Usage: bash scripts/close-stale-dependabot-prs.sh

set -euo pipefail

REPO="Arisofia/abaco-loans-analytics"
PRS=(247 246 245 244 243 241 240 239 238 237)
BASE_COMMIT="8fbe75801"
TARGET_COMMIT="$(git rev-parse --short HEAD)"

COMMENT="Closing due to stale base branch (\`${BASE_COMMIT}\`).

This PR was created against a base that predates critical linting fixes in commit \`48c7f753f\` (f-string cleanup). All 10 Dependabot PRs created on 2026-02-05 fail the same CI checks for this reason.

Dependabot will automatically recreate this PR against the current main branch (\`${TARGET_COMMIT}\`) which includes all fixes.

**Root Cause Analysis**: See [docs/DEPENDABOT_PR_FAILURE_ANALYSIS_2026_02_05.md](../docs/DEPENDABOT_PR_FAILURE_ANALYSIS_2026_02_05.md)

**No Action Required**: This is automated cleanup. Dependabot runs on schedule and will recreate updated PRs within 24 hours.
"

echo "═══════════════════════════════════════════════════════════════"
echo "  Closing ${#PRS[@]} Stale Dependabot PRs"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Reason: Stale base branch ${BASE_COMMIT} (missing f-string fix)"
echo "Target: ${TARGET_COMMIT} (current main)"
echo ""
echo "⚠️  WARNING: This will close PRs and lose comment threads."
echo "Dependabot will recreate PRs against latest main automatically."
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! ${REPLY} =~ ^[Yy]$ ]]; then
	echo "❌ Aborted by user"
	exit 0
fi

CLOSED=0
FAILED=0

for pr_num in "${PRS[@]}"; do
	echo "Closing PR #${pr_num}..."

	if gh pr close "${pr_num}" --comment "${COMMENT}" 2>/dev/null; then
		echo "✅ PR #${pr_num} closed successfully"
		((CLOSED++))
	else
		echo "❌ Failed to close PR #${pr_num}"
		((FAILED++))
	fi

	echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "  Closure Summary"
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Closed: ${CLOSED}/${#PRS[@]}"
echo "❌ Failed: ${FAILED}/${#PRS[@]}"
echo ""
echo "Dependabot will recreate these PRs on its next scheduled run."
echo "Monitor with: gh pr list --author app/dependabot"
echo "═══════════════════════════════════════════════════════════════"
