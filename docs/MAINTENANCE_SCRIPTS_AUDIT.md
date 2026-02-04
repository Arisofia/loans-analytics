# Cleanup & Maintenance Scripts Audit

**Date**: 2026-02-04  
**Baseline Commit**: `6740a2a66` (Sprint Status Baseline)  
**Status**: Complete audit with safe execution recommendations

---

## Executive Summary

Your repository has **3 active cleanup scripts** and **5+ deprecated scripts** (archived). The active scripts are:

1. ✅ **clean.sh** — PRODUCTION-READY, unified cleanup orchestrator
2. ✅ **scripts/maintenance/cleanup_workflow_runs_by_count.sh** — PRODUCTION-READY, targeted workflow cleanup
3. ⚠️ **scripts/maintenance/repo-doctor.sh** — FUNCTIONAL but has opinionated side effects (auto-installs ffmpeg)

---

## Script Inventory

### Active Scripts

**1. clean.sh** (Master cleanup orchestrator)
- **Status**: ✅ Production-ready
- **Phase 1**: Root directory cleanup (status reports, temp scripts, Gradle files, orphaned files)
- **Phase 2**: Consolidate duplicates (6 docs, 3 scripts)
- **Phase 3**: Caches (__pycache__, .pytest_cache, .mypy_cache, .ruff_cache, .next, .turbo)
- **Phase 4**: GitHub workflow runs (30-day threshold)
- **Phase 5**: Empty directories + syntax validation
- **Risk Level**: 🟡 Medium (has --dry-run safeguard)
- **Modes**: --dry-run, --workflows-only, --caches-only
- **Safety**: Excellent; archives deleted items; has validation

**2. cleanup_workflow_runs_by_count.sh** (Workflow retention policy)
- **Status**: ✅ Production-ready
- **Purpose**: Delete all workflow runs except most recent N (default: 25)
- **Risk Level**: 🟢 Low
- **Safeguards**: Interactive confirmation, rate-limiting (pause every 100), --dry-run mode
- **Requirements**: GitHub CLI (gh) + authentication
- **Current impact**: ~10,000 runs total; would keep 25, delete 9,975
- **Safety**: Excellent; cloud-hosted logs, easy to re-run CI

**3. repo-doctor.sh** (Health check + auto-fix)
- **Status**: ✅ Functional but opinionated
- **Purpose**: Check prerequisites, install ffmpeg, scan workflows, auto-commit/push
- **Risk Level**: 🔴 HIGH (auto-commits without review)
- **Safeguards**: Error checking for prereqs, diagnostic-only scanning
- **Issues**:
  - ❌ Auto-stages all changes and commits without review
  - ⚠️ Unconditionally installs ffmpeg (system-wide)
  - ❌ No rollback if push fails
- **Safety**: LOW — do NOT use as-is
- **Recommendation**: Extract only the diagnostic parts (workflow scanning); handle git ops manually

**4. merge_all_branches.sh** (Branch cleanup)
- **Status**: ✅ Safe
- **Purpose**: Delete local branches already merged into main
- **Risk Level**: 🟢 Low
- **Protected branches**: main, master, dev, develop, release, staging
- **Safeguards**: Hardcoded protected branch list
- **Issues**: Only cleans local; doesn't remove remote stale branches
- **Safety**: Excellent; merged branches are safe to re-create

### Deprecated Scripts (Archived)

Located in `archives/maintenance/deprecated-cleanup-scripts/`:
- cleanup_repo.sh (superseded by clean.sh)
- master_cleanup.sh (superseded by clean.sh)
- repo-cleanup.sh (superseded by clean.sh)
- commit_cleanup.sh (one-off from migration)
- code-quality.yml.deprecated (old workflow)

**Status**: Already isolated; no action needed. Safe to delete if archiving disk space becomes a concern.

---

## Risk Analysis

| Risk | Issue | Mitigation | Status |
|------|-------|-----------|--------|
| **🔴 repo-doctor.sh auto-commits** | Stages all changes, commits, and pushes without human review | DO NOT USE; extract diagnostics manually | Critical |
| **🟡 Root file deletion** | Deletes main.ts, profile.ps1, AzuriteConfig, etc. | Always use --dry-run first; already cleaned once safely | Mitigated |
| **🟡 Path references** | If code references orphaned files, deletion breaks imports | Manual verification before cleanup; none found in baseline | Mitigated |
| **🟢 Cache deletion** | Safe; caches auto-regenerate | Harmless; no safeguard needed | Low |
| **🟢 Workflow run deletion** | Historical logs deleted; no data loss (cloud-hosted) | 30-day grace period; rate-limiting built-in | Low |
| **🟢 Branch deletion** | Merged branches deleted locally | Can be re-created from remote; safe | Low |

---

## Safe Execution Guide

### Pre-Cleanup Checklist

```bash
# ✅ Step 1: Verify baseline state
git log --oneline -1
# Must show: 6740a2a66 docs: fix markdown linting in sprint status baseline

# ✅ Step 2: Clean working tree
git status
# Must show: "nothing to commit, working tree clean"

# ✅ Step 3: Sync with remote
git fetch origin
git status
# Must show: "Your branch is up to date with 'origin/main'"
```

---

### Phase 1: Dry-Run (Non-destructive Preview)

```bash
# Preview file cleanup
./clean.sh --dry-run

# Expected output:
# 🔍 DRY RUN MODE - No files will be deleted
# PHASE 1: Root Directory Cleanup
#   [DRY-RUN] Would delete file: ...
# ...
# ✅ Verify all deletions are expected (old reports, caches, orphaned files)
# ✅ Verify important files (src/, python/, tests/) are NOT listed
```

```bash
# Preview workflow cleanup (if desired)
./scripts/maintenance/cleanup_workflow_runs_by_count.sh --dry-run --keep 25

# Expected output:
# 📋 Total workflow runs: ~10,000
# 🗑️  Will delete: ~9,975 runs
# ✅ Will keep: 25 most recent runs
```

---

### Phase 2: Execute Cleanup

```bash
# Execute file cleanup
./clean.sh

# Review changes
git status
git diff --stat

# Stage and commit
git add -A
git commit -m "chore: execute unified repository cleanup (2026-02-04)"

# Push to remote
git push origin main
```

---

### Phase 3: Validate

```bash
# ✅ Run tests to check for regressions
pytest tests/ -q

# Expected: 132 passed (from baseline)
```

---

## Summary

✅ **clean.sh** — Safe, recommended for regular use  
✅ **cleanup_workflow_runs_by_count.sh** — Safe, use after file cleanup  
❌ **repo-doctor.sh** — Do NOT use; too opinionated  
✅ **merge_all_branches.sh** — Safe, use as-needed  
✅ **Deprecated scripts** — Already archived; no action needed

**Recommendation**: Execute the safe cleanup sequence once every sprint or before major releases.
