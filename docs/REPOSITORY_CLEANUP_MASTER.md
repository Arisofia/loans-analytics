# Repository Cleanup Master Reference

**Last Updated**: 2026-02-05  
**Repository**: Arisofia/abaco-loans-analytics  
**Status**: ✅ Production-Ready, Maintained  
**Current State**: Clean (1 branch, synchronized, no uncommitted changes)

---

## 🎯 Current Repository Status

### Repository Health Dashboard

```
✅ Branch Status:    main only (local + remote synchronized)
✅ Working Tree:     clean, no uncommitted changes
✅ HEAD Commit:      49d01e341 (2026-02-05)
✅ Dependencies:     10 Dependabot PRs merged (Feb 2026)
✅ CI/CD:           All workflows passing
✅ Documentation:    10 cleanup files, 3 archived sessions
```

### Recent Cleanup Operations (Feb 2026)

| Date       | Operation                          | Result                           |
|------------|-----------------------------------|----------------------------------|
| 2026-02-05 | Branch cleanup                    | 17+ branches deleted → main only |
| 2026-02-05 | Dependabot PR resolution          | 10 PRs merged successfully       |
| 2026-02-05 | Git worktree cleanup              | 1 worktree removed               |
| 2026-02-05 | CodeQL config fix                 | Removed queries parameter        |
| 2026-02-05 | Infrastructure updates            | Azure config, storage accounts   |
| 2026-02-03 | Comprehensive file reorganization | 30+ files archived/organized     |

---

## 📋 Cleanup Scripts Reference

### Active Production Scripts

#### 1. `clean.sh` — Master Cleanup Orchestrator

**Purpose**: Unified repository cleanup - caches, orphaned files, workflow runs, syntax validation  
**Location**: [clean.sh](../clean.sh)  
**Risk Level**: 🟢 LOW (with dry-run)

**Usage**:
```bash
# Dry run (recommended first)
./clean.sh --dry-run

# Execute cleanup
./clean.sh

# Workflows only
./clean.sh --workflows-only
```

**What It Cleans**:
- Python caches (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`)
- Build artifacts (`.next/`, `.turbo/`, `dist/`, `build/`)
- GitHub Actions runs (30+ days old)
- Empty directories
- Syntax validation (Python, Shell)

**Safeguards**:
- Dry-run mode available
- Excludes `.git`, `.venv`, `node_modules`, `archives`
- Requires `gh` CLI authentication for workflow cleanup
- Non-destructive syntax validation

---

#### 2. `scripts/maintenance/cleanup_workflow_runs_by_count.sh`

**Purpose**: Targeted GitHub Actions workflow run cleanup by count  
**Location**: [scripts/maintenance/cleanup_workflow_runs_by_count.sh](../scripts/maintenance/cleanup_workflow_runs_by_count.sh)  
**Risk Level**: 🟢 LOW

**Usage**:
```bash
# Keep last 10 runs per workflow
bash scripts/maintenance/cleanup_workflow_runs_by_count.sh 10

# Keep last 5 runs (more aggressive)
bash scripts/maintenance/cleanup_workflow_runs_by_count.sh 5
```

**Requirements**:
- GitHub CLI (gh) installed and authenticated
- Maintainer permissions on repository

---

#### 3. `scripts/maintenance/repo-doctor.sh`

**Purpose**: Repository health diagnostics  
**Location**: [scripts/maintenance/repo-doctor.sh](../scripts/maintenance/repo-doctor.sh)  
**Risk Level**: ⚠️ MEDIUM (auto-installs ffmpeg)

**Usage**:
```bash
bash scripts/maintenance/repo-doctor.sh
```

**Notes**:
- Functional but has opinionated side effects
- May auto-install system packages (ffmpeg)
- Review before running in CI/CD

---

### Deprecated Scripts (Archived)

The following scripts are archived in `archives/maintenance/deprecated-cleanup-scripts/`:
- `cleanup_repo.sh` - superseded by clean.sh
- `commit_cleanup.sh` - merged into main workflows
- `master_cleanup.sh` - consolidated functionality
- `repo-cleanup.sh` - duplicate of above

**Do not use archived scripts** - they may have stale logic or unvalidated assumptions.

---

## 🗂️ File Organization Standards

### Core Directory Structure

```
abaco-loans-analytics/
├── docs/                          # All documentation (except root essentials)
│   ├── planning/                  # Strategic planning (AGENTS.md, etc.)
│   ├── operations/                # Operational guides (GIT_CLEANUP.md, etc.)
│   ├── archive/                   # Historical documentation
│   └── *.md                       # Current documentation
├── archives/                      # Historical artifacts (organized by category)
│   ├── sessions/                  # Cleanup session logs
│   │   ├── 2026-01-cleanup/
│   │   └── 2026-02-cleanup/
│   ├── maintenance/               # Deprecated maintenance scripts
│   │   └── deprecated-cleanup-scripts/
│   ├── documentation/             # Superseded docs
│   └── releases/                  # Historical releases
├── scripts/                       # All automation scripts
│   ├── maintenance/               # Repository maintenance scripts
│   ├── deployment/                # Deployment automation
│   └── testing/                   # Test utilities
├── config/                        # Configuration files
├── src/                          # Source code
├── python/                       # Python modules
├── tests/                        # Test suites
└── [6 essential root .md files]  # README, CHANGELOG, LICENSE, etc.
```

### Root Directory Guidelines

**Essential Files Only** (6 files):
1. `README.md` - Project overview
2. `CHANGELOG.md` - Version history
3. `LICENSE` - License
4. `SECURITY.md` - Security policy
5. `REPO_STRUCTURE.md` - Repository map
6. `VERIFIED_REPOSITORY_STATE.md` - Current state documentation

**Everything else goes in subdirectories.**

---

## 🧹 Cleanup Workflows

### Weekly Maintenance Checklist

```bash
# 1. Update from remote
git fetch --prune
git pull origin main

# 2. Clean local caches
./clean.sh --dry-run  # Review first
./clean.sh            # Execute

# 3. Check for stale branches
git branch -vv | grep ': gone]'  # Identify stale tracking branches
git branch -d <stale-branch>     # Delete if safe

# 4. Verify repository health
git status               # Should show clean working tree
git log --oneline -5     # Review recent commits
```

### Monthly Maintenance Checklist

```bash
# 1. Aggressive cleanup
./clean.sh
git gc --aggressive      # Git garbage collection

# 2. Workflow run cleanup
bash scripts/maintenance/cleanup_workflow_runs_by_count.sh 10

# 3. Dependency updates
# Review and merge Dependabot PRs
gh pr list --label "dependencies"

# 4. Documentation audit
# Review docs/ for outdated content
# Archive superseded documentation to archives/documentation/
```

### Quarterly Maintenance Checklist

```bash
# 1. Security audit
npm audit                # Node.js dependencies
pip-audit                # Python dependencies

# 2. Test coverage verification
pytest --cov             # Run with coverage

# 3. Documentation consolidation
# Review and consolidate duplicate docs
# Update REPOSITORY_CLEANUP_MASTER.md (this file)

# 4. Archive old sessions
# Move >90 day old cleanup logs to archives/sessions/
```

---

## 🚨 Emergency Cleanup Procedures

### Scenario 1: Too Many Open Branches

**Symptoms**: Dozens of stale local/remote branches cluttering workspace

**Solution**:
```bash
# 1. List all branches
git branch -vv           # Local branches with tracking info
git branch -r            # Remote branches

# 2. Delete merged local branches
git branch --merged main | grep -v "^\*" | grep -v "main" | xargs -r git branch -d

# 3. Remove worktrees blocking deletion
git worktree list
git worktree remove <worktree-path> --force

# 4. Delete stale remote branches (CAREFUL!)
git branch -r | grep -v "HEAD" | grep -v "main" | sed 's/origin\///' | xargs -I {} git push origin --delete {}

# 5. Prune stale tracking references
git fetch --prune
```

### Scenario 2: Failing CI Due to Stale Base Branch

**Symptoms**: PRs failing checks that should pass

**Root Cause**: PR branched from old commit, missing recent fixes

**Solution**:
```bash
# Option A: Update PR base (requires maintainer permissions)
gh pr edit <PR-number> --base main

# Option B: Rebase PR locally and force push
git checkout <pr-branch>
git fetch origin
git rebase origin/main
git push --force-with-lease

# Option C: GitHub API update-branch (requires maintainer)
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/Arisofia/abaco-loans-analytics/pulls/<PR-number>/update-branch
```

**Reference**: See [PR_CLOSURE_STRATEGY_2026_02_05.md](PR_CLOSURE_STRATEGY_2026_02_05.md) for detailed analysis

### Scenario 3: Repository Sync Issues

**Symptoms**: Local and remote out of sync, merge conflicts

**Solution**:
```bash
# 1. Check current state
git status
git log --oneline --all --graph --decorate -10

# 2. Discard local uncommitted changes (if safe)
git stash push -m "Emergency cleanup stash"

# 3. Hard reset to remote (if local changes not needed)
git fetch origin
git reset --hard origin/main

# 4. Or: resolve conflicts manually
git merge origin/main
# Fix conflicts in editor
git add <resolved-files>
git commit

# 5. Verify sync
git log --oneline -5
git status
```

---

## 📊 Cleanup Session Archive

### 2026-02-05 Session: Branch Cleanup & Dependabot PRs

**Objective**: Resolve all Dependabot PRs, clean all branches, verify deployment

**Results**:
- ✅ 10 Dependabot PRs merged (#247-#237)
- ✅ 17+ branches deleted (local + remote)
- ✅ 1 git worktree removed
- ✅ CodeQL config fixed
- ✅ Infrastructure updates deployed
- ✅ Repository synchronized

**Documentation**: 
- [DEPENDABOT_PR_FAILURE_ANALYSIS_2026_02_05.md](DEPENDABOT_PR_FAILURE_ANALYSIS_2026_02_05.md)
- [PR_CLOSURE_STRATEGY_2026_02_05.md](PR_CLOSURE_STRATEGY_2026_02_05.md)

### 2026-02-03 Session: Comprehensive File Reorganization

**Objective**: Archive 30+ files, organize scripts, consolidate documentation

**Results**:
- ✅ 30+ files archived by category
- ✅ Scripts organized into subdirectories
- ✅ Documentation consolidated in docs/
- ✅ Root directory reduced to 6 essential files

**Documentation**: [COMPLETE_CLEANUP_SUMMARY_2026-02-03.md](COMPLETE_CLEANUP_SUMMARY_2026-02-03.md)

### January 2026 Sessions

**Multiple cleanup iterations** focusing on:
- Supabase RLS testing infrastructure
- Secret scanning fixes
- Linting standardization
- Docker configuration cleanup

**Documentation**: `archives/sessions/2026-01-cleanup/`

---

## 🎓 Best Practices

### DO ✅

- **Always dry-run first**: Use `--dry-run` flags when available
- **Archive, don't delete**: Historical context is valuable
- **Document cleanup sessions**: Create summary docs in archives/sessions/
- **Test after cleanup**: Run `make test` to verify nothing broke
- **Sync frequently**: `git fetch --prune` to avoid stale references
- **Use scripts**: Prefer `clean.sh` over manual rm commands
- **Check CI**: Verify workflows pass after cleanup

### DON'T ❌

- **Never force-push to main**: Protected branch, use PRs
- **Don't delete .github/workflows**: CI/CD is critical
- **Avoid aggressive git gc in active dev**: Can disrupt ongoing work
- **Don't archive current docs**: Only historical/superseded content
- **Never delete without backup**: Stash or archive first
- **Don't cleanup during deployments**: Wait for stable state

---

## 🔗 Related Documentation

### Essential References
- [REPO_OPERATIONS_MASTER.md](REPO_OPERATIONS_MASTER.md) - Master operations runbook
- [CLEANUP_SCRIPTS_AUDIT.md](CLEANUP_SCRIPTS_AUDIT.md) - Detailed script analysis
- [GIT_CLEANUP.md](operations/GIT_CLEANUP.md) - Git-specific cleanup operations

### Historical Context
- [COMPLETE_CLEANUP_SUMMARY_2026-02-03.md](COMPLETE_CLEANUP_SUMMARY_2026-02-03.md) - Feb 3 cleanup session
- [REPOSITORY_CLEANUP_2026-02-03.md](REPOSITORY_CLEANUP_2026-02-03.md) - Cleanup guidelines
- `archives/sessions/` - All cleanup session logs

### Troubleshooting
- [REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md](REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md) - Merge conflict resolution (archived, see REPO_OPERATIONS_MASTER.md)

---

## 📝 Change Log

### 2026-02-05
- **Created** REPOSITORY_CLEANUP_MASTER.md as single source of truth
- **Consolidated** multiple cleanup docs into unified reference
- **Added** emergency cleanup procedures
- **Documented** Feb 2026 cleanup session (branch cleanup, Dependabot PRs)

### 2026-02-04
- **Created** CLEANUP_SCRIPTS_AUDIT.md with detailed script analysis

### 2026-02-03
- **Completed** comprehensive file reorganization (30+ files)
- **Created** COMPLETE_CLEANUP_SUMMARY_2026-02-03.md

### 2026-01-29
- **Archived** REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md (superseded by REPO_OPERATIONS_MASTER.md)

---

## 🤝 Maintenance

**Owner**: Repository Administrators  
**Review Frequency**: Monthly  
**Update Trigger**: After significant cleanup sessions

**To update this document**:
1. Document cleanup operations in appropriate section
2. Update "Current Repository Status" dashboard
3. Add entry to Change Log
4. Commit with message: `docs: Update REPOSITORY_CLEANUP_MASTER.md`

---

**Version**: 1.0  
**Status**: Active, Production-Ready  
**Last Verified**: 2026-02-05 at commit 49d01e341
