#!/usr/bin/env bash
# Automated repo health check for abaco-loans-analytics

set -euo pipefail

# Ensure the script runs from the repo root
cd "$(dirname "$0")/.."

print_header() {
  echo "==== $1 ===="
}

print_header "GIT STATUS"
git status

print_header "GIT FETCH"
git fetch --all --prune

print_header "GIT BRANCHES"
git branch -vv

print_header "RECENT COMMITS"
git log --oneline --decorate --graph -n 10

print_header "REQUIREMENTS CONSISTENCY"
python - <<'PY'
from collections import Counter
from pathlib import Path

req_path = Path("requirements.txt")
lines = [line.strip() for line in req_path.read_text().splitlines() if line.strip() and not line.startswith('#')]
counts = Counter(lines)
duplicates = [item for item, count in counts.items() if count > 1]

if duplicates:
    print("Duplicate requirements detected:")
    for item in duplicates:
        print(f" - {item}")
    raise SystemExit(1)
print("Requirements file is free of duplicates.")
PY

print_header "LINT"
npm run lint || echo "Lint failed"

print_header "PYTHON TESTS"
pytest || echo "Pytest failed"

print_header "ENV FILES AUDIT"
ls -la .env* || echo "No env files found"

print_header "SECURITY AUDIT"
ls -la SECURITY.md || echo "SECURITY.md missing"

print_header "COMPLIANCE AUDIT"
ls -la COMPLIANCE_VALIDATION_SUMMARY.md || echo "COMPLIANCE_VALIDATION_SUMMARY.md missing"
