# Phase 2 Cleanup Plan - Deeper Repository Cleanup

**Date**: February 2, 2026  
**Phase**: 2 of 2  
**Status**: Ready for execution

---

## What Will Be Cleaned

### 1. Duplicate Documentation (6 files)

**Problem**: Multiple versions of same content, outdated session summaries in docs/ root

Files to archive:

- `docs/MASTER_CLEANUP_GUIDE.md` (duplicates REPO_OPERATIONS_MASTER.md §1)
- `docs/MASTER_CLEANUP_EXAMPLES.md` (duplicates REPO_OPERATIONS_MASTER.md §1)
- `docs/MASTER_CLEANUP_QUICK_REF.md` (duplicates REPO_OPERATIONS_MASTER.md §1)
- `docs/CLEANUP_CONSOLIDATION_SUMMARY.md` (session artifact - belongs in archive/)
- `docs/PERFORMANCE_CI_FIX_SUMMARY.md` (belongs in CRITICAL_DEBT_FIXES_2026.md)
- `docs/PIPELINE_AUTOMATION_SUMMARY.md` (belongs in archive/)

**Action**: Archive to `archives/sessions/2026-02-phase2/docs-duplicate/`  
**Source of Truth**: `docs/REPO_OPERATIONS_MASTER.md` §1 (Repository Hygiene)

### 2. Duplicate Scripts (2 files)

**Problem**: 3 workflow cleanup scripts with 70% overlapping functionality

Files to consolidate:

- ~~`scripts/cleanup_old_workflow_runs.sh`~~ (159 lines, keeps by days)
- ~~`scripts/cleanup_workflow_runs.sh`~~ (113 lines, simple version)
- ✅ `scripts/cleanup_workflow_runs_by_count.sh` (134 lines, most complete) **KEEP**

**Action**: Archive old variants, keep newest version  
**Rationale**: `cleanup_workflow_runs_by_count.sh` has best CLI interface and options

### 3. Orphaned Directories (3 directories)

**Problem**: Directories with minimal content that belong elsewhere

#### fi-analytics/

- **Content**: 9 files (SPRINT_0 docs, test plans, checklists)
- **Issue**: Duplicate of content in `docs/planning/` and `tests/`
- **Action**: Archive entire directory (prompt user for confirmation)
- **Rationale**: Main analytics code is in `src/pipeline/`

#### projects/

- **Content**: Single file `Q1-2026.md`
- **Action**: Move to `docs/planning/Q1-2026.md`, delete directory
- **Rationale**: Better organization, follows docs structure

#### models/

- **Content**: Single file `loan_risk_model.pkl`
- **Action**: Move to `data/models/loan_risk_model.pkl`, delete directory
- **Rationale**: Follows data governance structure (data/ for all data artifacts)

### 4. Empty Directories

**Action**: Find and remove all empty directories (excluding .git, .venv, node_modules, archives)

---

## Impact Analysis

**Total Items**: 11+ items  
**Disk Space Saved**: ~50KB (documentation) + 1-2MB (ML model relocation)  
**Risk Level**: Low - All items archived before deletion

### Breaking Changes: None

- All content archived with git history
- No code dependencies on these locations
- Can restore from `archives/sessions/2026-02-phase2/` if needed

### Benefits

1. **Clearer documentation structure** - Single source of truth for cleanup operations
2. **Reduced script duplication** - 3 scripts → 1 canonical version
3. **Better organization** - Data artifacts in data/, planning docs in docs/planning/
4. **Faster navigation** - Less clutter in root directories

---

## Execution

### Automatic (Recommended)

```bash
bash archives/sessions/2026-01-cleanup/phase2_cleanup.sh
```

### Manual (If needed)

```bash
# 1. Archive duplicate docs
mkdir -p archives/sessions/2026-02-phase2/docs-duplicate
mv docs/MASTER_CLEANUP_*.md archives/sessions/2026-02-phase2/docs-duplicate/
mv docs/*SUMMARY*.md archives/sessions/2026-02-phase2/docs-duplicate/

# 2. Archive duplicate scripts
mkdir -p archives/sessions/2026-02-phase2/scripts-duplicate
mv scripts/cleanup_old_workflow_runs.sh archives/sessions/2026-02-phase2/scripts-duplicate/
mv scripts/cleanup_workflow_runs.sh archives/sessions/2026-02-phase2/scripts-duplicate/

# 3. Reorganize orphaned directories
mv projects/Q1-2026.md docs/planning/
rmdir projects

mv models/loan_risk_model.pkl data/models/
rmdir models

# 4. Review fi-analytics before archiving (confirm with team)
ls -la fi-analytics/
```

---

## Rollback Plan

All changes are git-tracked deletions. To restore:

```bash
# Restore specific file
git checkout HEAD~1 -- docs/MASTER_CLEANUP_GUIDE.md

# Restore entire directory
git checkout HEAD~1 -- fi-analytics/

# Or restore from archive
cp -r archives/sessions/2026-02-phase2/docs-duplicate/MASTER_CLEANUP_GUIDE.md docs/
```

---

## Post-Cleanup Verification

```bash
# Check git status
git status

# Verify no broken links in docs
grep -r "MASTER_CLEANUP" docs/
grep -r "fi-analytics" README.md docs/

# Run tests to ensure no code dependencies broken
make test
```

---

## References

- Phase 1 Cleanup: `archives/sessions/2026-01-cleanup/CLEANUP_LOG.md`
- Data Governance: `.github/copilot-instructions.md`
- Repository Structure: `REPO_STRUCTURE.md`
- Operations Manual: `docs/REPO_OPERATIONS_MASTER.md`
