#!/bin/bash
# ==============================================================================
#
#  UNIFIED REPOSITORY MAINTENANCE SCRIPT - Abaco Loans Analytics
#
#  Purpose: Complete repository maintenance (cleanup, formatting, linting, git)
#
#  Consolidates functionality from:
#    - cleanup_repo.sh (code quality and formatting)
#    - commit_cleanup.sh (commit automation)
#    - master_cleanup.sh (filesystem cleanup)
#    - repo-cleanup.sh (git repository cleanup)
#
#  Usage:
#    ./scripts/repo_maintenance.sh --mode=standard    # Standard cleanup
#    ./scripts/repo_maintenance.sh --mode=aggressive  # Aggressive cleanup + gc
#    ./scripts/repo_maintenance.sh --mode=nuclear     # Maximum cleanup
#    ./scripts/repo_maintenance.sh --dry-run          # Preview only
#    ./scripts/repo_maintenance.sh --format-only      # Only code formatting
#    ./scripts/repo_maintenance.sh --ci               # CI-friendly mode
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default settings
MODE="standard"
DRY_RUN=false
FORMAT_ONLY=false
CI_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
	case $1 in
	--mode=*)
		MODE="${1#*=}"
		shift
		;;
	--dry-run)
		DRY_RUN=true
		shift
		;;
	--format-only)
		FORMAT_ONLY=true
		shift
		;;
	--ci)
		CI_MODE=true
		shift
		;;
	--help)
		echo "Usage: $0 [OPTIONS]"
		echo ""
		echo "Options:"
		echo "  --mode=standard     Standard cleanup (default)"
		echo "  --mode=aggressive   Aggressive cleanup with git gc"
		echo "  --mode=nuclear      Maximum cleanup (use with caution)"
		echo "  --dry-run           Preview changes without executing"
		echo "  --format-only       Only run code formatting"
		echo "  --ci                CI-friendly mode (no interactive prompts)"
		echo "  --help              Show this help message"
		exit 0
		;;
	*)
		echo -e "${RED}Unknown option: $1${NC}"
		echo "Use --help for usage information"
		exit 1
		;;
	esac
done

# Validate MODE parameter
if [[ ! $MODE =~ ^(standard|aggressive|nuclear)$ ]]; then
	echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
	echo -e "${YELLOW}Valid modes: standard, aggressive, nuclear${NC}"
	exit 1
fi

# Banner
echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║                                                                ║${NC}"
echo -e "${BOLD}${BLUE}║         🧹 REPOSITORY MAINTENANCE - ABACO ANALYTICS           ║${NC}"
echo -e "${BOLD}${BLUE}║                                                                ║${NC}"
echo -e "${BOLD}${BLUE}║   Unified script for cleanup, formatting, linting & git ops   ║${NC}"
echo -e "${BOLD}${BLUE}║                                                                ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Display mode
if [ "$DRY_RUN" = true ]; then
	echo -e "${YELLOW}${BOLD}🔍 MODE: DRY-RUN (Preview Only)${NC}"
elif [ "$FORMAT_ONLY" = true ]; then
	echo -e "${CYAN}${BOLD}✨ MODE: FORMAT ONLY${NC}"
else
	echo -e "${GREEN}${BOLD}⚙️  MODE: $MODE${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Helper function for cleanup operations
cleanup_item() {
	local path="$1"
	local description="$2"

	if [ -e "$path" ]; then
		if [ "$DRY_RUN" = true ]; then
			echo -e "${YELLOW}  [WOULD DELETE] $description: $path${NC}"
			if [ -d "$path" ]; then
				du -sh "$path" 2>/dev/null || echo "    (size unknown)"
			fi
		else
			echo -e "${RED}  [DELETING] $description: $path${NC}"
			rm -rf -- "$path"
			echo -e "${GREEN}    ✓ Deleted${NC}"
		fi
	fi
}

# Helper function for pattern-based cleanup
cleanup_pattern() {
	local pattern="$1"
	local description="$2"

	# Build base find command with exclusions
	local -a find_cmd
	find_cmd=(find . -type f -name "$pattern"
		! -path "./.venv/*" ! -path "./node_modules/*" ! -path "./.git/*")

	# Count matching files (suppress errors to keep set -e from aborting)
	local count
	count=$("${find_cmd[@]}" -print 2>/dev/null | wc -l | xargs)

	if [ "$count" != "0" ]; then
		if [ "$DRY_RUN" = true ]; then
			echo -e "${YELLOW}  [WOULD DELETE] $count $description${NC}"
		else
			# Use -exec to safely delete files even with spaces/newlines in names
			"${find_cmd[@]}" -exec rm -f -- {} + 2>/dev/null || true
			echo -e "${GREEN}  ✓ Deleted $count $description${NC}"
		fi
	fi
}

# =============================================================================
# SECTION 1: CODE FORMATTING AND LINTING
# =============================================================================
echo -e "${CYAN}${BOLD}[1/5] ✨ Code Formatting & Linting${NC}"
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ] && [ "$CI_MODE" = false ]; then
	echo -e "${YELLOW}  Activating virtual environment...${NC}"
	source .venv/bin/activate
fi

# Check if formatting tools are available
HAS_BLACK=$(command -v black &>/dev/null && echo true || echo false)
HAS_ISORT=$(command -v isort &>/dev/null && echo true || echo false)
HAS_RUFF=$(command -v ruff &>/dev/null && echo true || echo false)

# Track formatting failures
FORMAT_FAILED=false

if [ "$HAS_BLACK" = true ]; then
	echo -e "${YELLOW}  Running Black formatter...${NC}"
	if [ "$DRY_RUN" = true ]; then
		black --check . 2>&1 | head -5 || echo "    (would format files)"
	else
		if black src/ tests/ scripts/ python/ --exclude '\.venv|venv|build|dist|\.eggs|archives'; then
			echo -e "${GREEN}  ✓ Black complete${NC}"
		else
			echo -e "${RED}  ✗ Black failed${NC}"
			FORMAT_FAILED=true
		fi
	fi
else
	echo -e "${YELLOW}  ⚠ Black not installed, skipping${NC}"
fi

if [ "$HAS_ISORT" = true ]; then
	echo -e "${YELLOW}  Running isort...${NC}"
	if [ "$DRY_RUN" = true ]; then
		isort --check . 2>&1 | head -5 || echo "    (would sort imports)"
	else
		if isort src/ tests/ scripts/ python/ --profile black --skip .venv --skip venv --skip archives; then
			echo -e "${GREEN}  ✓ isort complete${NC}"
		else
			echo -e "${RED}  ✗ isort failed${NC}"
			FORMAT_FAILED=true
		fi
	fi
else
	echo -e "${YELLOW}  ⚠ isort not installed, skipping${NC}"
fi

if [ "$HAS_RUFF" = true ]; then
	echo -e "${YELLOW}  Running Ruff...${NC}"
	if [ "$DRY_RUN" = true ]; then
		ruff check . 2>&1 | head -10 || true
	else
		if ruff check src python scripts tests --fix; then
			echo -e "${GREEN}  ✓ Ruff complete${NC}"
		else
			echo -e "${RED}  ✗ Ruff found issues${NC}"
			FORMAT_FAILED=true
		fi
	fi
else
	echo -e "${YELLOW}  ⚠ Ruff not installed, skipping${NC}"
fi

# Exit early if format-only mode
if [ "$FORMAT_ONLY" = true ]; then
	echo ""
	if [ "$FORMAT_FAILED" = true ]; then
		echo -e "${RED}❌ Code formatting completed with errors${NC}"
		exit 1
	else
		echo -e "${GREEN}✅ Code formatting complete!${NC}"
		exit 0
	fi
fi

echo ""

# =============================================================================
# SECTION 2: PYTHON ENVIRONMENT CLEANUP
# =============================================================================
echo -e "${CYAN}${BOLD}[2/5] 🐍 Python Environment Cleanup${NC}"
echo ""

cleanup_item ".pytest_cache" "pytest cache"
cleanup_item ".mypy_cache" "mypy cache"
cleanup_item ".ruff_cache" "ruff cache"
cleanup_item ".coverage" "coverage data"
cleanup_item "htmlcov" "coverage reports"

# Cleanup __pycache__ directories
pycache_dirs=$(find . -type d -name "__pycache__" \
	! -path "./.venv/*" ! -path "./node_modules/*" ! -path "./.git/*" \
	2>/dev/null || true)

if [ -n "$pycache_dirs" ]; then
	count=$(echo "$pycache_dirs" | wc -l | xargs)
	if [ "$DRY_RUN" = true ]; then
		echo -e "${YELLOW}  [WOULD DELETE] $count __pycache__ directories${NC}"
	else
		echo "$pycache_dirs" | xargs -r rm -rf
		echo -e "${GREEN}  ✓ Deleted $count __pycache__ directories${NC}"
	fi
else
	echo -e "${GREEN}  ✓ No __pycache__ directories found${NC}"
fi

# Cleanup Python bytecode
cleanup_pattern "*.pyc" "Python bytecode files"
cleanup_pattern "*.pyo" "Python optimized bytecode"

echo ""

# =============================================================================
# SECTION 3: BUILD ARTIFACTS AND TEMPORARY FILES
# =============================================================================
echo -e "${CYAN}${BOLD}[3/5] 🏗️  Build Artifacts & Temp Files${NC}"
echo ""

cleanup_item "build" "build directory"
cleanup_item "dist" "distribution builds"
cleanup_item "node_modules" "node modules"
cleanup_item ".next" "Next.js build"

cleanup_pattern "*.backup" "backup files"
cleanup_pattern "*.bak" "bak files"
cleanup_pattern "*.old" "old files"
cleanup_pattern "*.tmp" "tmp files"
cleanup_pattern "*.temp" "temp files"
cleanup_pattern "*.swp" "vim swap files"
cleanup_pattern ".DS_Store" "macOS metadata"

# Cleanup numbered copies
for i in {1..5}; do
	cleanup_pattern "* ($i).*" "numbered copies ($i)"
done

echo ""

# =============================================================================
# SECTION 4: GIT REPOSITORY MAINTENANCE
# =============================================================================
echo -e "${CYAN}${BOLD}[4/5] 🔧 Git Repository Maintenance${NC}"
echo ""

if ! git rev-parse --git-dir >/dev/null 2>&1; then
	echo -e "${YELLOW}  ⚠ Not in a git repository - skipping${NC}"
else
	if [ "$DRY_RUN" = false ]; then
		# Fetch and prune
		echo -e "${YELLOW}  Fetching and pruning...${NC}"
		git fetch --all --prune 2>/dev/null || true
		echo -e "${GREEN}  ✓ Fetch & prune complete${NC}"

		# Delete merged branches (not in CI mode)
		if [ "$CI_MODE" = false ]; then
			merged_branches=$(git branch --merged | grep -v "\*" | grep -vE "^(main|master|develop)$" 2>/dev/null || true)
			if [ -n "$merged_branches" ]; then
				count=$(echo "$merged_branches" | wc -l | xargs)
				echo -e "${YELLOW}  Deleting $count merged branch(es)...${NC}"
				echo "$merged_branches" | xargs -r git branch -d 2>/dev/null || true
				echo -e "${GREEN}  ✓ Merged branches deleted${NC}"
			else
				echo -e "${GREEN}  ✓ No merged branches to delete${NC}"
			fi
		fi

		# Garbage collection
		if [ "$MODE" = "aggressive" ] || [ "$MODE" = "nuclear" ]; then
			echo -e "${YELLOW}  Running aggressive garbage collection...${NC}"
			git gc --aggressive --prune=now 2>/dev/null || true
			echo -e "${GREEN}  ✓ Aggressive GC complete${NC}"
		else
			echo -e "${YELLOW}  Running standard garbage collection...${NC}"
			git gc 2>/dev/null || true
			echo -e "${GREEN}  ✓ GC complete${NC}"
		fi

		# Nuclear mode: reflog cleanup (with confirmation)
		if [ "$MODE" = "nuclear" ]; then
			if [ "$CI_MODE" = false ]; then
				echo -e "${RED}${BOLD}  ⚠️  WARNING: Nuclear mode will permanently delete reflog history!${NC}"
				echo -e "${YELLOW}  This action is IRREVERSIBLE. Type 'yes' to confirm: ${NC}"
				read -r confirmation
				if [ "$confirmation" != "yes" ]; then
					echo -e "${YELLOW}  Skipping reflog cleanup (user cancelled)${NC}"
				else
					echo -e "${RED}  [NUCLEAR] Expiring reflog...${NC}"
					git reflog expire --expire=now --all 2>/dev/null || true
					git gc --prune=now 2>/dev/null || true
					echo -e "${GREEN}  ✓ Reflog cleanup complete${NC}"
				fi
			else
				echo -e "${RED}  [NUCLEAR] Expiring reflog (CI mode - no confirmation)...${NC}"
				git reflog expire --expire=now --all 2>/dev/null || true
				git gc --prune=now 2>/dev/null || true
				echo -e "${GREEN}  ✓ Reflog cleanup complete${NC}"
			fi
		fi
	else
		echo -e "${YELLOW}  ℹ Git cleanup skipped in dry-run mode${NC}"
	fi
fi

echo ""

# =============================================================================
# SECTION 5: DOCKER CLEANUP (if Docker is available)
# =============================================================================
if [ "$MODE" = "aggressive" ] || [ "$MODE" = "nuclear" ]; then
	echo -e "${CYAN}${BOLD}[5/5] 🐳 Docker Cleanup${NC}"
	echo ""

	if command -v docker &>/dev/null; then
		if [ "$DRY_RUN" = false ]; then
			# Remove stopped containers
			stopped=$(docker ps -aq --filter "status=exited" 2>/dev/null || true)
			if [ -n "$stopped" ]; then
				count=$(echo "$stopped" | wc -l | xargs)
				echo -e "${RED}  Removing $count stopped container(s)...${NC}"
				echo "$stopped" | xargs -r docker rm 2>/dev/null || true
				echo -e "${GREEN}  ✓ Complete${NC}"
			fi

			# Remove dangling images
			dangling=$(docker images -qf "dangling=true" 2>/dev/null || true)
			if [ -n "$dangling" ]; then
				count=$(echo "$dangling" | wc -l | xargs)
				echo -e "${RED}  Removing $count dangling image(s)...${NC}"
				echo "$dangling" | xargs -r docker rmi 2>/dev/null || true
				echo -e "${GREEN}  ✓ Complete${NC}"
			fi

			if [ "$MODE" = "nuclear" ]; then
				if [ "$CI_MODE" = false ]; then
					echo -e "${RED}${BOLD}  ⚠️  WARNING: Nuclear mode will remove ALL unused Docker resources including volumes!${NC}"
					echo -e "${YELLOW}  This action is IRREVERSIBLE. Type 'yes' to confirm: ${NC}"
					read -r confirmation
					if [ "$confirmation" != "yes" ]; then
						echo -e "${YELLOW}  Skipping Docker system prune (user cancelled)${NC}"
					else
						echo -e "${RED}  [NUCLEAR] Running docker system prune...${NC}"
						docker system prune -af --volumes 2>/dev/null || true
						echo -e "${GREEN}  ✓ Complete${NC}"
					fi
				else
					echo -e "${RED}  [NUCLEAR] Running docker system prune (CI mode - no confirmation)...${NC}"
					docker system prune -af --volumes 2>/dev/null || true
					echo -e "${GREEN}  ✓ Complete${NC}"
				fi
			fi
		else
			echo -e "${YELLOW}  ℹ Docker cleanup skipped in dry-run mode${NC}"
		fi
	else
		echo -e "${GREEN}  ✓ Docker not installed - skipping${NC}"
	fi

	echo ""
else
	echo -e "${CYAN}${BOLD}[5/5] 🐳 Docker Cleanup${NC}"
	echo ""
	echo -e "${YELLOW}  ℹ Skipped (use --mode=aggressive or --mode=nuclear)${NC}"
	echo ""
fi

# =============================================================================
# FINAL SUMMARY
# =============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
	echo -e "${YELLOW}${BOLD}🔍 DRY-RUN COMPLETE${NC}"
	echo ""
	echo -e "${YELLOW}No changes were made. This was a preview only.${NC}"
	echo ""
	echo -e "${CYAN}To execute:${NC}"
	echo -e "${CYAN}  ./scripts/repo_maintenance.sh --mode=standard${NC}"
else
	echo -e "${GREEN}${BOLD}✅ MAINTENANCE COMPLETE${NC}"
	echo ""

	# Repository statistics
	if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		REPO_SIZE=$(du -sh .git 2>/dev/null | cut -f1 || echo "unknown")
		COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo "unknown")
		BRANCHES=$(git branch | wc -l 2>/dev/null || echo "unknown")

		echo -e "${BLUE}Repository Statistics:${NC}"
		echo -e "${BLUE}  Git Size: ${REPO_SIZE}${NC}"
		echo -e "${BLUE}  Commits: ${COMMITS}${NC}"
		echo -e "${BLUE}  Branches: ${BRANCHES}${NC}"
		echo ""
	fi

	echo -e "${GREEN}✨ Your repository is clean and well-maintained!${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
