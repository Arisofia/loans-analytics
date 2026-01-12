#!/usr/bin/env bash
set -euo pipefail

REPO="Arisofia/abaco-loans-analytics"
BRANCH="work/pr-6"
PR_NUMBER=34
LABELS=("phase-1" "documentation" "ci-cd" "governance")

echo "Switching to branch ${BRANCH}"
git checkout "${BRANCH}"

mkdir -p docs/phase-1
cp -v PHASE-1-SUMMARY.md PR-393-NEXT-STEPS.md EXECUTION-CHECKLIST.md docs/phase-1/

git add docs/phase-1/
if git diff --staged --quiet; then
  echo "No changes to commit."
else
  git commit -m "docs(phase-1): add execution tracking documentation"
  git push origin "${BRANCH}"
fi

# Ensure labels exist (create if missing) and add to PR
for lbl in "${LABELS[@]}"; do
  if ! gh label list --repo "${REPO}" | grep -q "^${lbl}\b"; then
    echo "Label '${lbl}' not found in ${REPO}. Creating it."
    gh label create "${lbl}" --repo "${REPO}" --description "Phase 1 and documentation" --color "#0e8a16" || true
  fi
done

# Add labels to PR
gh pr edit "${PR_NUMBER}" --repo "${REPO}" --add-label "${LABELS[*]}" || true

# Post a summary comment
gh pr comment "${PR_NUMBER}" --repo "${REPO}" --body "Helper docs have been added to docs/phase-1/ and committed. Suggested labels applied. Please set PR to Ready for Review and add reviewers when ready."

echo "Setup complete. PR URL: https://github.com/${REPO}/pull/${PR_NUMBER}"
