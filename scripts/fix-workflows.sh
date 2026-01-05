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
  # Run actionlint across all workflow YAML files (avoid passing the directory)
  find .github/workflows -name '*.yml' -print0 | xargs -0 actionlint || exit 1
else
  echo "actionlint not found. To install locally run: 'brew install actionlint' or 'go install github.com/rhysd/actionlint/cmd/actionlint@${ACTIONLINT_VER}'"
  exit 1
fi

echo "All workflows pass actionlint checks."