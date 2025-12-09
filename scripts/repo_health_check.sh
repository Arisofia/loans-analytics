#!/bin/zsh
# Automated repo health check for abaco-loans-analytics

echo "==== GIT STATUS ===="
git status

echo "==== GIT FETCH ===="
git fetch --all

echo "==== GIT BRANCHES ===="
git branch -vv

echo "==== RECENT COMMITS ===="
git log --oneline --decorate --graph -n 10

echo "==== LINT ===="
npm run lint || echo "Lint failed"

echo "==== PYTHON TESTS ===="
pytest || echo "Pytest failed"

echo "==== ENV FILES AUDIT ===="
ls -la .env* || echo "No env files found"

echo "==== SECURITY AUDIT ===="
ls -la SECURITY.md || echo "SECURITY.md missing"

echo "==== COMPLIANCE AUDIT ===="
ls -la COMPLIANCE_VALIDATION_SUMMARY.md || echo "COMPLIANCE_VALIDATION_SUMMARY.md missing"
