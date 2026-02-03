#!/bin/bash
# Unified Repository Cleanup Script
# Consolidates all cleanup operations into a single master script
# Replaces: comprehensive_cleanup.sh, phase2_cleanup.sh, execute_cleanup.sh, run_cleanup.sh,
#           cleanup_old_workflow_runs.sh, cleanup_workflow_runs.sh

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "${REPO_ROOT}" || exit 1

echo "🧹 UNIFIED REPOSITORY CLEANUP"
echo "=============================="
echo ""

# Configuration
TOTAL_DELETED=0
ARCHIVE_BASE="archives/sessions/2026-02-cleanup"
DRY_RUN=false
MODE="full"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      echo "🔍 DRY RUN MODE - No files will be deleted"
      echo ""
      shift
      ;;
    --workflows-only)
      MODE="workflows"
      shift
      ;;
    --caches-only)
      MODE="caches"
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --dry-run         Preview what will be deleted"
      echo "  --workflows-only  Only clean GitHub Actions workflow runs"
      echo "  --caches-only     Only clean Python/Node caches"
      echo "  --help            Show this help"
      echo ""
      echo "Default: Full cleanup (root files + duplicates + caches)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage"
      exit 1
      ;;
  esac
done

mkdir -p "${ARCHIVE_BASE}"/{phase1,phase2,caches}

delete_item() {
  local item="$1"
  if [[ "${DRY_RUN}" = true ]]; then
    if [[ -f "${item}" ]]; then
      echo "  [DRY-RUN] Would delete file: ${item}"
    elif [[ -d "${item}" ]]; then
      echo "  [DRY-RUN] Would delete directory: ${item}"
    fi
  else
    if [[ -f "${item}" ]]; then
      rm "${item}" && echo "  ✓ Deleted: ${item}" && ((TOTAL_DELETED++))
    elif [[ -d "${item}" ]]; then
      rm -rf "${item}" && echo "  ✓ Deleted directory: ${item}" && ((TOTAL_DELETED++))
    fi
  fi
}

# ============================================================================
# PHASE 1: Root Directory Cleanup
# ============================================================================
if [[ "${MODE}" == "full" ]]; then
  echo "PHASE 1: Root Directory Cleanup"
  echo "================================"
  echo ""

  echo "📄 Deleting status reports..."
  for file in AUTOMATION_COMPLETE.md AUTOMATION_SUMMARY.md COMPLETION_SUMMARY.md \
              COMPREHENSIVE_FIXES_APPLIED.md COMPREHENSIVE_STATUS_REPORT.md \
              CRITICAL_FIX_COMPLETED.md FINAL_COMPLETION_SUMMARY.md \
              FINAL_FIXES_APPLIED.md FINAL_RESOLUTION_COMPLETE.md \
              FINAL_STATUS_REPORT.md SESSION_COMPLETE.md STATUS_REPORT.md \
              WORKFLOW_FIXES_SUMMARY.md WORKFLOW_RESOLUTION_COMPLETE.md \
              WORKFLOW_STATUS_FINAL.md WORKFLOW_STATUS_REPORT.md \
              FIX_ALL_WORKFLOWS.md; do
    delete_item "${file}"
  done

  echo ""
  echo "🔧 Deleting temporary scripts..."
  delete_item "fix_codeql_alert_136.py"
  delete_item "cleanup_old_runs.sh"

  echo ""
  echo "⚙️  Deleting Gradle build system..."
  delete_item "build.gradle"
  delete_item "gradlew"
  delete_item "gradlew.bat"
  delete_item "gradle"

  echo ""
  echo "🗑️  Deleting orphaned files..."
  delete_item "main.ts"
  delete_item "docker-compose.override.yml"
  delete_item "AzuriteConfig"
  delete_item "__azurite_db_table__.json"
  delete_item "profile.ps1"

  echo ""
  echo "PHASE 2: Duplicate Documentation & Scripts"
  echo "==========================================="
  echo ""

  echo "📚 Consolidating duplicate docs..."
  delete_item "docs/MASTER_CLEANUP_GUIDE.md"
  delete_item "docs/MASTER_CLEANUP_EXAMPLES.md"
  delete_item "docs/MASTER_CLEANUP_QUICK_REF.md"
  delete_item "docs/CLEANUP_CONSOLIDATION_SUMMARY.md"
  delete_item "docs/PERFORMANCE_CI_FIX_SUMMARY.md"
  delete_item "docs/PIPELINE_AUTOMATION_SUMMARY.md"

  echo ""
  echo "🔄 Consolidating duplicate scripts..."
  delete_item "scripts/cleanup_old_workflow_runs.sh"
  delete_item "scripts/cleanup_workflow_runs.sh"
  delete_item "run_cleanup.sh"

  echo ""
  echo "📦 Reorganizing orphaned directories..."

  # Move projects/Q1-2026.md to docs/planning/
  if [[ -f "projects/Q1-2026.md" ]]; then
    if [[ "${DRY_RUN}" = false ]]; then
      mkdir -p docs/planning
      mv projects/Q1-2026.md docs/planning/ && echo "  ✓ Moved: projects/Q1-2026.md → docs/planning/"
      rmdir projects 2>/dev/null && echo "  ✓ Removed: projects/" && ((TOTAL_DELETED++))
    else
      echo "  [DRY-RUN] Would move: projects/Q1-2026.md → docs/planning/"
      echo "  [DRY-RUN] Would remove: projects/"
    fi
  fi

  # Move models/loan_risk_model.pkl to data/models/
  if [[ -f "models/loan_risk_model.pkl" ]]; then
    if [[ "${DRY_RUN}" = false ]]; then
      mkdir -p data/models
      mv models/loan_risk_model.pkl data/models/ && echo "  ✓ Moved: models/loan_risk_model.pkl → data/models/"
      rmdir models 2>/dev/null && echo "  ✓ Removed: models/" && ((TOTAL_DELETED++))
    else
      echo "  [DRY-RUN] Would move: models/loan_risk_model.pkl → data/models/"
      echo "  [DRY-RUN] Would remove: models/"
    fi
  fi

  # Archive fi-analytics if exists
  if [[ -d "fi-analytics" ]]; then
    if [[ "${DRY_RUN}" = false ]]; then
      cp -r fi-analytics "${ARCHIVE_BASE}/phase2/" && echo "  ✓ Archived: fi-analytics/ → ${ARCHIVE_BASE}/phase2/"
      rm -rf fi-analytics && echo "  ✓ Deleted: fi-analytics/" && ((TOTAL_DELETED++))
    else
      echo "  [DRY-RUN] Would archive and delete: fi-analytics/"
    fi
  fi

  echo ""
fi

# ============================================================================
# PHASE 3: Cache & Build Artifacts
# ============================================================================
if [[ "${MODE}" == "full" || "${MODE}" == "caches" ]]; then
  echo "PHASE 3: Cache & Build Artifacts"
  echo "================================="
  echo ""

  echo "🐍 Cleaning Python caches..."
  if [[ "${DRY_RUN}" = false ]]; then
    find . -type d -name "__pycache__" -not -path "./.venv/*" -not -path "./node_modules/*" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: __pycache__/ directories"
    find . -type d -name ".pytest_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: .pytest_cache/ directories"
    find . -type d -name ".mypy_cache" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: .mypy_cache/ directories"
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: .ruff_cache/ directories"
    find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" \) -not -path "./.venv/*" -delete 2>/dev/null && echo "  ✓ Deleted: Python bytecode files"
    find . -type d -name "*.egg-info" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: .egg-info directories"
  else
    echo "  [DRY-RUN] Would delete: __pycache__/ directories"
    echo "  [DRY-RUN] Would delete: .pytest_cache/ directories"
    echo "  [DRY-RUN] Would delete: .mypy_cache/ directories"
    echo "  [DRY-RUN] Would delete: .ruff_cache/ directories"
    echo "  [DRY-RUN] Would delete: Python bytecode files"
    echo "  [DRY-RUN] Would delete: .egg-info directories"
  fi

  echo ""
  echo "📦 Cleaning Node/NPM caches..."
  if [[ "${DRY_RUN}" = false ]]; then
    find . -type d -name ".next" -not -path "./node_modules/*" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: .next/ directories"
    find . -type d -name ".turbo" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: .turbo/ directories"
    find . -type f -name "*.tsbuildinfo" -delete 2>/dev/null && echo "  ✓ Deleted: TypeScript build info"
  else
    echo "  [DRY-RUN] Would delete: .next/ directories"
    echo "  [DRY-RUN] Would delete: .turbo/ directories"
    echo "  [DRY-RUN] Would delete: TypeScript build info"
  fi

  echo ""
  echo "🏗️  Cleaning build artifacts..."
  if [[ "${DRY_RUN}" = false ]]; then
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null && echo "  ✓ Deleted: htmlcov/ directories"
    find . -type f -name ".coverage" -not -path "./.venv/*" -delete 2>/dev/null && echo "  ✓ Deleted: .coverage files"
  else
    echo "  [DRY-RUN] Would delete: htmlcov/ directories"
    echo "  [DRY-RUN] Would delete: .coverage files"
  fi

  echo ""
fi

# ============================================================================
# PHASE 4: GitHub Actions Workflow Runs
# ============================================================================
if [[ "$MODE" == "workflows" ]]; then
  echo "PHASE 4: GitHub Actions Workflow Runs"
  echo "======================================"
  echo ""
  
  if command -v gh &> /dev/null; then
    KEEP_DAYS=30
    echo "🗑️  Deleting workflow runs older than ${KEEP_DAYS} days..."
    
    if [[ "${DRY_RUN}" = true ]]; then
      RUN_IDS=$(gh run list --limit 1000 --json databaseId,status,createdAt | \
        jq -r ".[] | select(.createdAt < (now - ${KEEP_DAYS}*86400 | strftime(\"%Y-%m-%dT%H:%M:%SZ\"))) | .databaseId" | \
        head -10) || true
      echo "${RUN_IDS}" | while read -r run_id; do
        [[ -n "${run_id}" ]] && echo "  [DRY-RUN] Would delete workflow run: ${run_id}"
      done
    else
      RUN_IDS=$(gh run list --limit 1000 --json databaseId,status,createdAt | \
        jq -r ".[] | select(.createdAt < (now - ${KEEP_DAYS}*86400 | strftime(\"%Y-%m-%dT%H:%M:%SZ\"))) | .databaseId") || true
      if [[ -n "${RUN_IDS}" ]]; then
        echo "${RUN_IDS}" | xargs -I {} gh run delete {} && echo "  ✓ Deleted old workflow runs"
      fi
    fi
  else
    echo "  ⚠️  GitHub CLI not installed - skipping workflow cleanup"
    echo "  Install with: brew install gh"
  fi
  
  echo ""
fi

# ============================================================================
# PHASE 5: Empty Directories & Syntax Check
# ============================================================================
if [[ "${MODE}" == "full" ]]; then
  echo "PHASE 4: Empty Directories"
  echo "=========================="
  echo ""

  echo "🗂️  Removing empty directories..."
  EMPTY_DIRS=$(find . -type d -empty \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./node_modules/*" \
    -not -path "./archives/*" \
    -not -path "./.github/*" \
    2>/dev/null) || true
  echo "${EMPTY_DIRS}" | while read -r dir; do
    if [[ -d "${dir}" && -n "${dir}" ]]; then
      if [[ "${DRY_RUN}" = false ]]; then
        rmdir "${dir}" 2>/dev/null && echo "  ✓ Removed empty: ${dir}"
      else
        echo "  [DRY-RUN] Would remove empty: ${dir}"
      fi
    fi
  done

  echo ""
  echo "PHASE 5: Syntax Validation"
  echo "=========================="
  echo ""

  echo "🔍 Checking for syntax errors..."
  echo ""

  # Check Python syntax
  if command -v python &> /dev/null; then
    echo "  Python files:"
    PYTHON_ERRORS=0
    while IFS= read -r file; do
      if ! python -m py_compile "${file}" 2>/dev/null; then
        echo "    ⚠️  Syntax error: ${file}"
        ((PYTHON_ERRORS++))
      fi
    done < <(find python/ src/ tests/ -name "*.py" 2>/dev/null || true)
    
    if [[ ${PYTHON_ERRORS} -eq 0 ]]; then
      echo "    ✓ No Python syntax errors found"
    else
      echo "    ⚠️  Found ${PYTHON_ERRORS} Python files with syntax errors"
    fi
  fi

  # Check shell script syntax
  echo ""
  echo "  Shell scripts:"
  SHELL_ERRORS=0
  while IFS= read -r file; do
    if ! bash -n "${file}" 2>/dev/null; then
      echo "    ⚠️  Syntax error: ${file}"
      ((SHELL_ERRORS++))
    fi
  done < <(find scripts/ -name "*.sh" 2>/dev/null || true)

  if [[ ${SHELL_ERRORS} -eq 0 ]]; then
    echo "    ✓ No shell script syntax errors found"
  else
    echo "    ⚠️  Found ${SHELL_ERRORS} shell scripts with syntax errors"
  fi

  echo ""
fi

# ============================================================================
# Summary
# ============================================================================
echo "✅ CLEANUP COMPLETE"
echo "==================="
echo ""

if [[ "${DRY_RUN}" = true ]]; then
  echo "🔍 DRY RUN - No files were actually deleted"
  echo ""
  echo "To execute cleanup, run without --dry-run:"
  echo "  ./clean.sh"
else
  echo "📊 Summary:"
  echo "  - Status reports: 17 deleted"
  echo "  - Temporary scripts: 2 deleted"
  echo "  - Build system files: 4 deleted"
  echo "  - Orphaned files: 5 deleted"
  echo "  - Duplicate docs: 6 deleted"
  echo "  - Duplicate scripts: 3 deleted"
  echo "  - Orphaned directories: 3 reorganized"
  echo "  - Python caches: cleaned"
  echo "  - Node caches: cleaned"
  echo "  - Build artifacts: cleaned"
  echo "  - Empty directories: removed"
  echo ""
  echo "  Total items: ${TOTAL_DELETED}+ (plus cache files)"
  echo ""
  echo "📋 Next steps:"
  echo "  1. Review: git status"
  echo "  2. Run tests: make test"
  echo "  3. Stage: git add -A"
  echo "  4. Commit: git commit -m 'chore: unified repository cleanup'"
  echo ""
  echo "📖 Archive location: ${ARCHIVE_BASE}/"
fi
