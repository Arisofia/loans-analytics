#!/bin/bash
# Setup script for automated development environment

set -euo pipefail

echo "🚀 Setting up automated development environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Install pre-commit framework
echo -e "${BLUE}1. Installing pre-commit...${NC}"
pip install pre-commit 2>/dev/null || python3 -m pip install pre-commit

# 2. Install pre-commit hooks
echo -e "${BLUE}2. Installing pre-commit hooks...${NC}"
pre-commit install

# 3. Run pre-commit on all files to ensure compliance
echo -e "${BLUE}3. Running initial pre-commit checks...${NC}"
pre-commit run --all-files || echo "⚠️  Some hooks may need fixing"

# 4. Install Python development dependencies
echo -e "${BLUE}4. Installing Python dev dependencies...${NC}"
if [ -f "requirements-dev.txt" ]; then
  pip install -r requirements-dev.txt 2>/dev/null || python3 -m pip install -r requirements-dev.txt
fi

# 5. Initialize git hooks directory
echo -e "${BLUE}5. Configuring git hooks...${NC}"
git config core.hooksPath .git/hooks

# 6. Create useful git aliases for automation
echo -e "${BLUE}6. Setting up git aliases...${NC}"
git config --local alias.check '!pre-commit run --all-files'
git config --local alias.fmt '!black python/ .github/scripts/ && isort python/ .github/scripts/'
git config --local alias.test '!pytest tests/ -v'

echo -e "${GREEN}✅ Automation setup complete!${NC}"
echo ""
echo -e "${YELLOW}Available commands:${NC}"
echo "  git check        - Run all pre-commit checks"
echo "  git fmt          - Format all Python code"
echo "  git test         - Run pytest"
echo "  pre-commit run --all-files  - Manual pre-commit run"
echo ""
echo -e "${BLUE}💡 Tip: Pre-commit will automatically run on git commit${NC}"
