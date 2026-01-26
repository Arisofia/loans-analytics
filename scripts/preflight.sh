#!/bin/bash
set -e

echo "🚀 Starting Preflight Checks..."

# Check Python version
python3 --version

# Check if requirements are installed
echo "📦 Checking dependencies..."
pip check

# Check for critical directories
echo "📂 Checking directory structure..."
[ -d "python" ] || { echo "❌ src/ directory missing"; exit 1; }
[ -d "tests" ] || { echo "❌ tests/ directory missing"; exit 1; }
[ -d "data" ] || { echo "⚠️ data/ directory missing (creating...)"; mkdir -p data; }

echo "✅ Preflight checks passed!"
exit 0
