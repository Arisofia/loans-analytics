#!/bin/bash
# Automated cleanup script for Abaco Loans Analytics
# Removes temporary files, caches, and unnecessary artifacts to keep the repo clean.

set -e

echo "Starting repository cleanup..."

# Remove Python caches
echo "Cleaning Python caches..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +
find . -type d -name ".ruff_cache" -exec rm -rf {} +

# Remove test coverage artifacts
echo "Cleaning test coverage artifacts..."
rm -rf htmlcov .coverage

# Remove logs from old runs (optional: keep last 5)
# echo "Cleaning old run logs..."
# ls -dt logs/runs/* | tail -n +6 | xargs rm -rf

# Remove temporary data archives if needed
# echo "Cleaning temporary archives..."
# rm -rf data/archives/raw/tmp*

echo "Cleanup complete!"
