#!/usr/bin/env bash
set -euo pipefail

# Install a pinned version of actionlint for consistent validation
# Preferable local install methods:
#  - macOS Homebrew: brew install actionlint
#  - Go install: go install github.com/rhysd/actionlint/cmd/actionlint@v1.6.23
# CI usage: prefer using the rint/actionlint GitHub Action in workflows instead of installing here.

ACTIONLINT_VER="v1.6.23"

echo "Attempting to run actionlint (preferred: locally installed e.g. via brew or go install)..."
if command -v actionlint >/dev/null 2>&1; then
  # Find all yml workflow files under any .github/workflows directory and run actionlint on them.
  # Exclude third-party vendor workflow directories (like node_modules) to avoid noisy warnings.
  WORKFLOW_FILES=$(find . -type f -name '*.yml' -path '*/.github/workflows/*' -not -path '*/node_modules/*' -print0 | xargs -0 -n1 echo || true)
  if [ -z "$WORKFLOW_FILES" ]; then
    echo "No workflow files found under .github/workflows/* (excluding node_modules)"
    exit 0
  fi
  echo "Running actionlint on the following workflow files (excluding node_modules):"
  printf '%s\n' $WORKFLOW_FILES
  # Use find with -print0 to safely handle spaces and pass to actionlint
  # Exclude node_modules vendor workflows from validation
  find . -type f -name '*.yml' -path '*/.github/workflows/*' -not -path '*/node_modules/*' -print0 | xargs -0 actionlint || exit 1
else
  echo "actionlint not found. To install locally run: 'brew install actionlint' or 'go install github.com/rhysd/actionlint/cmd/actionlint@${ACTIONLINT_VER}'"
  exit 1
fi

echo "All workflows pass actionlint checks."