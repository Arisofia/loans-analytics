#!/bin/bash
# delete-remote-branches.sh

BRANCHES_TO_DELETE=(
  "chore/ci-gate-polish"
  "chore/deploy-verify-automation"
  "chore/fix-markdownlint"
  "chore/workflow-cleanup"
  "ci/fix-continued-headings"
  "ci/cleanup-remove-empty-files"
  "fix/workflows-lint-fix2"
  # Agrega más según necesites
)

for branch in "${BRANCHES_TO_DELETE[@]}"; do
  echo "Eliminando $branch..."
  git push origin --delete "$branch" 2>/dev/null || echo "  ⚠️  Branch no existe: $branch"
done

echo "✅ Branches remotas eliminadas!"
