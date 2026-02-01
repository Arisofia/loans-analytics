#!/bin/bash
# ==============================================================================
#
#  MASTER CLEANUP SCRIPT - Abaco Loans Analytics
#
#  Purpose: Complete cleanup of local repository (filesystem, Docker, Git state)
#  Strategy: Remove ALL local backups, copies, caches, and temporary files
#  Outcome: Keep ONLY production/real project files locally - ONE VERSION, NO DUPLICATES
#
#  ⚠️  WARNING: This script is DESTRUCTIVE and IRREVERSIBLE (LOCAL ONLY)
#  ⚠️  Review each section before executing
#  ⚠️  Make a full backup BEFORE running if you're unsure
#
#  Usage:
#    ./scripts/master_cleanup.sh --dry-run    # Preview what will be deleted
#    ./scripts/master_cleanup.sh --execute    # Actually delete files
#    ./scripts/master_cleanup.sh --nuclear    # Nuclear option: everything
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default mode
DRY_RUN=true
NUCLEAR=false
FLAGS_PASSED=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      FLAGS_PASSED+=("dry-run")
      DRY_RUN=true
      shift
      ;;
    --execute)
      FLAGS_PASSED+=("execute")
      DRY_RUN=false
      shift
      ;;
    --nuclear)
      FLAGS_PASSED+=("nuclear")
      NUCLEAR=true
      DRY_RUN=false
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 [--dry-run|--execute|--nuclear]"
      exit 1
      ;;
  esac
done

# Validate that only one mode was specified
if [ ${#FLAGS_PASSED[@]} -gt 1 ]; then
  echo -e "${RED}Error: Multiple modes specified (${FLAGS_PASSED[*]}). Use only one of: --dry-run, --execute, or --nuclear${NC}"
  exit 1
fi

# Banner
echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${RED}║                                                                ║${NC}"
echo -e "${BOLD}${RED}║           🧹 MASTER CLEANUP SCRIPT - ABACO ANALYTICS           ║${NC}"
echo -e "${BOLD}${RED}║                                                                ║${NC}"
echo -e "${BOLD}${RED}║  ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE. PRODUCTION.    ║${NC}"
echo -e "${BOLD}${RED}║                                                                ║${NC}"
echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}${BOLD}🔍 MODE: DRY-RUN (Preview Only - No Files Deleted)${NC}"
else
  echo -e "${RED}${BOLD}💥 MODE: EXECUTE (FILES WILL BE DELETED!)${NC}"
  if [ "$NUCLEAR" = true ]; then
    echo -e "${RED}${BOLD}☢️  NUCLEAR MODE ACTIVE - MAXIMUM DESTRUCTION${NC}"
  fi
  echo ""
  echo -e "${YELLOW}Press CTRL+C to cancel or Enter to continue...${NC}"
  read -r
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Helper function to delete files/directories
cleanup_item() {
  local path="$1"
  local description="$2"
  
  if [ -e "$path" ]; then
    if [ "$DRY_RUN" = true ]; then
      echo -e "${YELLOW}  [WOULD DELETE] $description: $path${NC}"
      if [ -d "$path" ]; then
        du -sh "$path" 2>/dev/null || echo "    (directory size unknown)"
      fi
    else
      echo -e "${RED}  [DELETING] $description: $path${NC}"
      rm -rf -- "$path"
      echo -e "${GREEN}    ✓ Deleted${NC}"
    fi
  fi
}

# Helper function to find and delete patterns
cleanup_pattern() {
  local pattern="$1"
  local description="$2"
  echo -e "${YELLOW}  Searching for $description...${NC}"
  
  local found_files
  found_files=$(find . -type f -name "$pattern" ! -path "./.venv/*" ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./build/*" 2>/dev/null || true)
  
  if [ -z "$found_files" ]; then
    echo -e "${GREEN}    ✓ No $description found${NC}"
  else
    local count=$(echo "$found_files" | wc -l | xargs)
    echo -e "${YELLOW}    Found $count file(s)${NC}"
    
    echo "$found_files" | while read -r file; do
      if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}    [WOULD DELETE] $file${NC}"
      else
        echo -e "${RED}    [DELETING] $file${NC}"
        rm -f -- "$file"
      fi
    done
  fi
}

# Helper function to find and delete path patterns (includes directory structure)
cleanup_path_pattern() {
  local path_pattern="$1"
  local description="$2"

  echo -e "${YELLOW}  Searching for $description...${NC}"

  local found_files
  found_files=$(find . -type f -path "$path_pattern" \
    ! -path "./.venv/*" ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./build/*" \
    2>/dev/null || true)

  if [ -z "$found_files" ]; then
    echo -e "${GREEN}    ✓ No $description found${NC}"
  else
    local count=$(echo "$found_files" | wc -l | xargs)
    echo -e "${YELLOW}    Found $count file(s)${NC}"
    echo "$found_files" | while read -r file; do
      if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}    [WOULD DELETE] $file${NC}"
      else
        echo -e "${RED}    [DELETING] $file${NC}"
        rm -f -- "$file"
      fi
    done
  fi
}

# =============================================================================
# SECTION 1: PYTHON ENVIRONMENT CLEANUP
# =============================================================================
echo -e "${CYAN}${BOLD}[1/10] 🐍 Python Environment Cleanup${NC}"
echo ""

# Python cache
cleanup_item ".pytest_cache" "pytest cache"
cleanup_item ".mypy_cache" "mypy cache"
cleanup_item ".ruff_cache" "ruff cache"
cleanup_item ".cache" "general Python cache"
cleanup_item "htmlcov" "coverage reports"
cleanup_item ".coverage" "coverage data"
cleanup_item ".eggs" "eggs directory"

# Find and delete all *.egg-info directories
echo -e "${YELLOW}  Searching for *.egg-info directories...${NC}"
egginfo_dirs=$(find . -type d -name "*.egg-info" ! -path "./.venv/*" ! -path "./node_modules/*" ! -path "./.git/*" 2>/dev/null || true)
if [ -z "$egginfo_dirs" ]; then
  echo -e "${GREEN}    ✓ No *.egg-info directories found${NC}"
else
  count=$(echo "$egginfo_dirs" | wc -l | xargs)
  echo -e "${YELLOW}    Found $count *.egg-info director(ies)${NC}"
  echo "$egginfo_dirs" | while read -r dir; do
    cleanup_item "$dir" "*.egg-info"
  done
fi

# Find and delete all __pycache__ directories
echo -e "${YELLOW}  Searching for __pycache__ directories...${NC}"
pycache_dirs=$(find . -type d -name "__pycache__" ! -path "./.venv/*" ! -path "./node_modules/*" ! -path "./.git/*" 2>/dev/null || true)
if [ -z "$pycache_dirs" ]; then
  echo -e "${GREEN}    ✓ No __pycache__ directories found${NC}"
else
  count=$(echo "$pycache_dirs" | wc -l | xargs)
  echo -e "${YELLOW}    Found $count __pycache__ director(ies)${NC}"
  echo "$pycache_dirs" | while read -r dir; do
    cleanup_item "$dir" "__pycache__"
  done
fi

# Python bytecode and temp files
cleanup_pattern "*.pyc" "Python bytecode files"
cleanup_pattern "*.pyo" "Python optimized bytecode"
cleanup_pattern "*.pyd" "Python DLL files"

echo ""

# =============================================================================
# SECTION 2: NODE/NPM CLEANUP
# =============================================================================
echo -e "${CYAN}${BOLD}[2/10] 📦 Node/NPM Environment Cleanup${NC}"
echo ""

cleanup_item "node_modules" "node modules"
cleanup_item ".npm" "npm cache"
cleanup_item ".yarn" "yarn cache"
cleanup_item ".next" "Next.js build"
cleanup_item ".turbo" "Turbo cache"
cleanup_item "dist" "distribution builds"
cleanup_item "out" "output directory"
cleanup_pattern "*.tsbuildinfo" "TypeScript build info"
cleanup_pattern ".pnpm-debug.log*" "pnpm debug logs"

echo ""

# =============================================================================
# SECTION 3: BUILD ARTIFACTS & GRADLE
# =============================================================================
echo -e "${CYAN}${BOLD}[3/10] 🏗️  Build Artifacts Cleanup${NC}"
echo ""

cleanup_item ".gradle" "Gradle cache"
cleanup_item "build" "build directory"
cleanup_item "coverage" "coverage directory"

echo ""

# =============================================================================
# SECTION 4: BACKUP & COPY FILES
# =============================================================================
echo -e "${CYAN}${BOLD}[4/10] 💾 Backup & Copy Files Cleanup${NC}"
echo ""

cleanup_pattern "*.backup" "backup files"
cleanup_pattern "*.bak" "bak files"
cleanup_pattern "*.old" "old files"
cleanup_pattern "*.orig" "original files"
cleanup_pattern "*.copy" "copy files"
cleanup_pattern "*.Copy" "Copy files"
cleanup_pattern "*~" "editor backup files"
cleanup_pattern "*.cleanup-backup" "cleanup backup files"

# Numbered copies (macOS Finder, VS Code, browser downloads)
cleanup_pattern "* (1).*" "numbered copies (1)"
cleanup_pattern "* (2).*" "numbered copies (2)"
cleanup_pattern "* (3).*" "numbered copies (3)"
cleanup_pattern "* (4).*" "numbered copies (4)"
cleanup_pattern "* (5).*" "numbered copies (5)"
cleanup_pattern "* copy.*" "copy files (lowercase)"
cleanup_pattern "* Copy.*" "copy files (capitalized)"

echo ""

# =============================================================================
# SECTION 5: TEMPORARY FILES
# =============================================================================
echo -e "${CYAN}${BOLD}[5/10] 🗑️  Temporary Files Cleanup${NC}"
echo ""

cleanup_item "tmp" "tmp directory"
cleanup_item ".tmp" "hidden tmp directory"
cleanup_pattern "*.tmp" "tmp files"
cleanup_pattern "*.temp" "temp files"
cleanup_pattern "*.swp" "vim swap files"
cleanup_pattern "*.swo" "vim swap files"
cleanup_pattern ".*.swp" "hidden vim swap files"

echo ""

# =============================================================================
# SECTION 6: LOGS & REPORTS
# =============================================================================
echo -e "${CYAN}${BOLD}[6/10] 📋 Logs & Reports Cleanup${NC}"
echo ""

cleanup_item "logs" "logs directory"
cleanup_pattern "*.log" "log files"
cleanup_item "playwright-report" "Playwright reports"
cleanup_item "test-results" "test results"
cleanup_item "pytest-report" "pytest reports"
cleanup_pattern "coverage.xml" "coverage XML"
cleanup_pattern "junit.xml" "JUnit XML"

# Temporary markdown reports (as defined in .gitignore)
cleanup_pattern "AUTOMATION_SUMMARY*.md" "automation summary reports"
cleanup_pattern "CLEANUP_COMPLETE.md" "cleanup complete reports"
cleanup_pattern "CONSOLIDATION_*.md" "consolidation reports"
cleanup_pattern "OPTIMIZATION_REPORT.md" "optimization reports"
cleanup_pattern "PROJECT_CLEANUP_STATUS.md" "project status reports"
cleanup_pattern "SESSION_COMPLETE.md" "session complete reports"
cleanup_pattern "TECHNICAL_DEBT_*.md" "technical debt reports"

echo ""

# =============================================================================
# SECTION 7: DATA DIRECTORY CLEANUP
# =============================================================================
echo -e "${CYAN}${BOLD}[7/10] 📊 Data Directory Cleanup${NC}"
echo ""

# Temporary run data (as defined in .gitignore)
cleanup_path_pattern "*/data/archives/raw/tmp*.csv" "temporary raw archives"
cleanup_path_pattern "*/data/metrics/run_*.csv" "run CSV files"
cleanup_path_pattern "*/data/metrics/run_*.parquet" "run Parquet files"
cleanup_path_pattern "*/data/metrics/run_*_metrics.json" "run metrics JSON"
cleanup_path_pattern "*/data/metrics/timeseries/run_*.parquet" "timeseries run files"

# Data cascade tmp files
cleanup_path_pattern "*/data/archives/cascade/tmp*.csv" "cascade temporary files"

echo ""

# =============================================================================
# SECTION 8: IDE & EDITOR FILES
# =============================================================================
echo -e "${CYAN}${BOLD}[8/10] 💻 IDE & Editor Files Cleanup${NC}"
echo ""

cleanup_item ".idea" "IntelliJ IDEA"
cleanup_item ".settings" "Eclipse settings"
cleanup_pattern "*.code-workspace" "VS Code workspaces"
cleanup_item ".vscode/history" "VS Code history"
cleanup_item ".vscode/cache" "VS Code cache"
cleanup_pattern ".DS_Store" "macOS Finder metadata"

echo ""

# =============================================================================
# SECTION 9: DOCKER CLEANUP
# =============================================================================
echo -e "${CYAN}${BOLD}[9/10] 🐳 Docker Cleanup${NC}"
echo ""

if command -v docker &> /dev/null; then
  echo -e "${YELLOW}  Docker is installed - checking resources...${NC}"
  
  # Stopped containers
  stopped_containers=$(docker ps -aq --filter "status=exited" 2>/dev/null || true)
  if [ -n "$stopped_containers" ]; then
    container_count=$(echo "$stopped_containers" | wc -l | xargs)
    if [ "$DRY_RUN" = true ]; then
      echo -e "${YELLOW}    [WOULD DELETE] $container_count stopped container(s)${NC}"
    else
      echo -e "${RED}    [DELETING] $container_count stopped container(s)${NC}"
      docker rm $stopped_containers
      echo -e "${GREEN}      ✓ Deleted${NC}"
    fi
  else
    echo -e "${GREEN}    ✓ No stopped containers${NC}"
  fi
  
  # Dangling images
  dangling_images=$(docker images -qf "dangling=true" 2>/dev/null || true)
  if [ -n "$dangling_images" ]; then
    image_count=$(echo "$dangling_images" | wc -l | xargs)
    if [ "$DRY_RUN" = true ]; then
      echo -e "${YELLOW}    [WOULD DELETE] $image_count dangling image(s)${NC}"
    else
      echo -e "${RED}    [DELETING] $image_count dangling image(s)${NC}"
      docker rmi $dangling_images
      echo -e "${GREEN}      ✓ Deleted${NC}"
    fi
  else
    echo -e "${GREEN}    ✓ No dangling images${NC}"
  fi
  
  # Volumes (only in nuclear mode)
  if [ "$NUCLEAR" = true ]; then
    unused_volumes=$(docker volume ls -qf "dangling=true" 2>/dev/null || true)
    if [ -n "$unused_volumes" ]; then
      volume_count=$(echo "$unused_volumes" | wc -l | xargs)
      if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}    [NUCLEAR] [WOULD DELETE] $volume_count unused volume(s)${NC}"
      else
        echo -e "${RED}    [NUCLEAR] [DELETING] $volume_count unused volume(s)${NC}"
        docker volume rm $unused_volumes
        echo -e "${GREEN}      ✓ Deleted${NC}"
      fi
    else
      echo -e "${GREEN}    ✓ No unused volumes${NC}"
    fi
    
    # System prune
    if [ "$DRY_RUN" = true ]; then
      echo -e "${YELLOW}    [NUCLEAR] [WOULD RUN] docker system prune -af --volumes${NC}"
    else
      echo -e "${RED}    [NUCLEAR] Running docker system prune...${NC}"
      docker system prune -af --volumes
      echo -e "${GREEN}      ✓ Complete${NC}"
    fi
  fi
  
  # Local data directories
  cleanup_item "grafana/data" "Grafana data"
else
  echo -e "${GREEN}  ✓ Docker not installed - skipping${NC}"
fi

echo ""

# =============================================================================
# SECTION 10: GIT REPOSITORY CLEANUP
# =============================================================================
echo -e "${CYAN}${BOLD}[10/10] 🔧 Git Repository Cleanup${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo -e "${YELLOW}  ⚠ Not in a git repository - skipping Git cleanup${NC}"
elif [ "$DRY_RUN" = false ]; then
  # Fetch and prune
  echo -e "${YELLOW}  Fetching and pruning remote references...${NC}"
  git fetch --all --prune
  echo -e "${GREEN}    ✓ Complete${NC}"
  
  # Delete merged local branches
  echo -e "${YELLOW}  Checking for merged local branches...${NC}"
  merged_branches=$(git branch --merged | grep -v "\*" | grep -v "main" | grep -v "master" | grep -v "develop" 2>/dev/null || true)
  if [ -n "$merged_branches" ]; then
    count=$(echo "$merged_branches" | wc -l | xargs)
    echo -e "${YELLOW}    Found $count merged branch(es)${NC}"
    echo "$merged_branches" | while read -r branch; do
      echo -e "${RED}      Deleting: $branch${NC}"
      git branch -d "$branch" 2>/dev/null || true
    done
    echo -e "${GREEN}    ✓ Merged branches deleted${NC}"
  else
    echo -e "${GREEN}    ✓ No merged branches to delete${NC}"
  fi
  
  # Git garbage collection
  if [ "$NUCLEAR" = true ]; then
    echo -e "${YELLOW}  [NUCLEAR] Running aggressive garbage collection...${NC}"
    git gc --aggressive --prune=now
    echo -e "${GREEN}    ✓ Complete${NC}"
  else
    echo -e "${YELLOW}  Running standard garbage collection...${NC}"
    git gc
    echo -e "${GREEN}    ✓ Complete${NC}"
  fi
  
  # Git reflog cleanup (nuclear only)
  if [ "$NUCLEAR" = true ]; then
    echo -e "${RED}  [NUCLEAR] Expiring reflog entries...${NC}"
    git reflog expire --expire=now --all
    git gc --prune=now
    echo -e "${GREEN}    ✓ Complete${NC}"
  fi
else
  echo -e "${YELLOW}  ℹ Git cleanup skipped in dry-run mode${NC}"
fi

echo ""

# =============================================================================
# FINAL REPORT
# =============================================================================
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}${BOLD}🔍 DRY-RUN COMPLETE${NC}"
  echo ""
  echo -e "${YELLOW}No files were deleted. This was a preview only.${NC}"
  echo ""
  echo -e "${CYAN}To actually execute the cleanup:${NC}"
  echo -e "${CYAN}  ./scripts/master_cleanup.sh --execute${NC}"
  echo ""
  echo -e "${CYAN}For maximum cleanup (including Docker, volumes, reflog):${NC}"
  echo -e "${CYAN}  ./scripts/master_cleanup.sh --nuclear${NC}"
else
  echo -e "${GREEN}${BOLD}✅ CLEANUP COMPLETE${NC}"
  echo ""
  
  # Repository statistics
  REPO_SIZE=$(du -sh .git 2>/dev/null | cut -f1 || echo "unknown")
  WORK_SIZE=$(du -sh . 2>/dev/null | cut -f1 || echo "unknown")

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached-HEAD")
  else
    CURRENT_BRANCH="not a git repository"
  fi
  
  echo -e "${BLUE}Repository Statistics:${NC}"
  echo -e "${BLUE}  Git Directory Size: ${REPO_SIZE}${NC}"
  echo -e "${BLUE}  Working Tree Size: ${WORK_SIZE}${NC}"
  echo -e "${BLUE}  Current Branch: ${CURRENT_BRANCH}${NC}"
  echo ""
  
  echo -e "${GREEN}✨ Your repository is now clean!${NC}"
  echo -e "${GREEN}   ONE VERSION. NO BACKUPS. NO COPIES. NO CACHE.${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
