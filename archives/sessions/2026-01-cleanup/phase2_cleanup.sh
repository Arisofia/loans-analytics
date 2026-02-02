#!/bin/bash
# Phase 2 Cleanup - Deeper Repository Cleanup
# Consolidates duplicate docs, scripts, and unused directories

set -e

cd "$(git rev-parse --show-toplevel)" || exit 1

echo "🧹 Phase 2: Deeper Repository Cleanup"
echo "========================================"
echo ""

TOTAL_DELETED=0
ARCHIVE_BASE="archives/sessions/2026-02-phase2"

# Create archive directory
mkdir -p "$ARCHIVE_BASE"

# Function to archive and delete
archive_and_delete() {
  local item="$1"
  local category="$2"
  
  if [ -f "$item" ] || [ -d "$item" ]; then
    local basename=$(basename "$item")
    local archive_dir="$ARCHIVE_BASE/$category"
    mkdir -p "$archive_dir"
    
    if [ -f "$item" ]; then
      cp "$item" "$archive_dir/" && rm "$item" && echo "  ✓ Archived & deleted: $item" && ((TOTAL_DELETED++))
    elif [ -d "$item" ]; then
      cp -r "$item" "$archive_dir/" && rm -rf "$item" && echo "  ✓ Archived & deleted directory: $item" && ((TOTAL_DELETED++))
    fi
  fi
}

delete_item() {
  local item="$1"
  if [ -f "$item" ]; then
    rm "$item" && echo "  ✓ Deleted: $item" && ((TOTAL_DELETED++))
  elif [ -d "$item" ]; then
    rm -rf "$item" && echo "  ✓ Deleted directory: $item" && ((TOTAL_DELETED++))
  fi
}

echo "📄 1. Consolidating duplicate docs..."
echo ""

# Duplicate cleanup guides (3 variants - keep REPO_OPERATIONS_MASTER as source of truth)
archive_and_delete "docs/MASTER_CLEANUP_GUIDE.md" "docs-duplicate"
archive_and_delete "docs/MASTER_CLEANUP_EXAMPLES.md" "docs-duplicate"
archive_and_delete "docs/MASTER_CLEANUP_QUICK_REF.md" "docs-duplicate"

# Duplicate summary files in docs/ root (belong in archive/)
archive_and_delete "docs/CLEANUP_CONSOLIDATION_SUMMARY.md" "docs-summaries"
archive_and_delete "docs/PERFORMANCE_CI_FIX_SUMMARY.md" "docs-summaries"
archive_and_delete "docs/PIPELINE_AUTOMATION_SUMMARY.md" "docs-summaries"

echo ""
echo "🔧 2. Consolidating duplicate scripts..."
echo ""

# 3 workflow cleanup scripts with overlapping functionality
# Keep: cleanup_workflow_runs_by_count.sh (newest, most complete)
# Delete: older variants
archive_and_delete "scripts/cleanup_old_workflow_runs.sh" "scripts-duplicate"
archive_and_delete "scripts/cleanup_workflow_runs.sh" "scripts-duplicate"

echo ""
echo "📦 3. Cleaning up orphaned project directories..."
echo ""

# fi-analytics - Duplicate analytics files (main analytics in src/pipeline/)
if [ -d "fi-analytics" ]; then
  echo "  ⚠️  fi-analytics/ contains:"
  ls -1 fi-analytics/ | head -5
  read -p "  Archive fi-analytics/? (y/N): " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] && archive_and_delete "fi-analytics" "orphaned-dirs"
fi

# projects/ - Single file Q1-2026.md (belongs in docs/planning/)
if [ -d "projects" ] && [ -f "projects/Q1-2026.md" ]; then
  mkdir -p docs/planning
  mv projects/Q1-2026.md docs/planning/ && echo "  ✓ Moved: projects/Q1-2026.md → docs/planning/"
  rmdir projects && echo "  ✓ Removed empty directory: projects/" && ((TOTAL_DELETED++))
fi

# models/ - Single ML pickle file (belongs in data/models/)
if [ -d "models" ] && [ -f "models/loan_risk_model.pkl" ]; then
  mkdir -p data/models
  mv models/loan_risk_model.pkl data/models/ && echo "  ✓ Moved: models/loan_risk_model.pkl → data/models/"
  rmdir models && echo "  ✓ Removed empty directory: models/" && ((TOTAL_DELETED++))
fi

echo ""
echo "🗄️  4. Checking for empty directories..."
echo ""

# Find and remove empty directories (except .git, .venv, node_modules, archives)
find . -type d -empty \
  -not -path "./.git/*" \
  -not -path "./.venv/*" \
  -not -path "./node_modules/*" \
  -not -path "./archives/*" \
  -not -path "./.zencoder/*" \
  -not -path "./.zenflow/*" \
  2>/dev/null | while read dir; do
    if [ -d "$dir" ]; then
      rmdir "$dir" && echo "  ✓ Removed empty: $dir" && ((TOTAL_DELETED++))
    fi
  done

echo ""
echo "✅ Phase 2 Cleanup Complete!"
echo "   Total items processed: $TOTAL_DELETED"
echo ""
echo "📋 Summary:"
echo "  - Consolidated 3 duplicate cleanup guides"
echo "  - Consolidated 3 duplicate summary docs"
echo "  - Consolidated 2 duplicate workflow cleanup scripts"
echo "  - Reorganized orphaned directories"
echo "  - Removed empty directories"
echo ""
echo "📖 Review changes: git status"
echo "📁 Archived items: $ARCHIVE_BASE/"
