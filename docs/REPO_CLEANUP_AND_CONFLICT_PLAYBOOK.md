# Repository Cleanup & Merge Conflict Playbook

**Project:** abaco-loans-analytics  
**Version:** 2.0 (2026-01-29)  
**Maintained by:** Repository Administrators

## Overview

This playbook enforces disciplined hygiene across local and remote branches, commits, and merge flows. It integrates our G4.x/G5.x pipeline realities, Supabase-driven integration tests, and multi-branch collaboration. Adopt these procedures to maintain stability, minimize merge friction, and keep Phase progress traceable.

## Table of Contents

1. [Repository Cleanup Procedures](#1-repository-cleanup-procedures)
2. [Merge Conflict Resolution Workflow](#2-merge-conflict-resolution-workflow)
3. [Best Practices (Prevention & Resolution)](#3-best-practices-prevention--resolution)
4. [Troubleshooting Matrix](#4-troubleshooting-matrix)
5. [Git Configuration Checklist](#5-git-configuration-checklist)
6. [References & Change Log](#6-references--change-log)

---

## 1. Repository Cleanup Procedures

### 1.1 Local Repository Hygiene

| Goal | Commands & Notes |
|------|------------------|
| Remove stale feature branches | `git branch` / `git branch -d feature-x` / `git branch -D tmp/*` |
| Prune remote-tracking refs | `git fetch --all --prune` (or nightly via automation) |
| Remove untracked clutter | `git clean -n` (dry run), `git clean -fd` (files+dirs), `git clean -fdx` (also ignored files) |
| Garbage collection | `git gc` (monthly), `git gc --aggressive` (quarterly or pre-archive) |

**When:**

- Before major merges/rebases
- After completing a feature phase (G4.x, G5.x, etc.)
- When local Git performance degrades

### 1.2 Remote Repository Hygiene

| Goal | Commands & Notes |
|------|------------------|
| Delete remote branches (CLI) | `git push origin --delete branch-name` |
| Delete remote branches (GitHub UI) | Repo → "Branches" → trash icon |
| Prune remote refs | `git remote prune origin` (mirrors `git fetch --prune`) |

**Policy:**

- Remove merged branches within 48h of merging to main.
- Archive "audit" / "phase" branches after the steering committee signs off.

### 1.3 Commit History Cleanup

| Action | Use |
|--------|-----|
| Interactive rebase | `git rebase -i HEAD~N` (squash/fixup/well-scoped commits) |
| Amend last commit | `git commit --amend -m "better message"` or `git commit --amend --no-edit` |
| Rewrite patch stack | Use interactive rebase on top of main for G4.x/G5.x sequences |

**Guideline:**

- Use squash/fixup to group WIP commits before opening a PR.
- Rebase frequently to avoid long-lived divergent stacks.

### 1.4 Large File Governance

| Task | Commands |
|------|----------|
| Identify large objects | `git rev-list --all --objects \| sort -k2 \| tail -20` |
| Track via Git LFS | `git lfs install`, `git lfs track "*.psd"`, commit `.gitattributes` |

**Note:** Our repo should remain lightweight (<1GB). Use LFS for infrequent binary assets; never version encrypted secrets.

### 1.5 Maintenance Cadence

| Frequency | Actions |
|-----------|---------|
| Weekly | Prune merged branches, clean untracked files |
| Monthly | `git gc`, review large files, rebase active feature branches |
| Quarterly | Audit branch list, archive legacy phases, sanity-check CI caches |
| Pre-release | Full cleanup sweep + test matrix run |

---

## 2. Merge Conflict Resolution Workflow

### 2.1 Detect & Analyze

On `git pull` / `git merge` / `git rebase`, Git highlights conflicting files.

Conflicts typically arise from parallel edits to the same files (e.g., `pytest.ini`, orchestrator, Supabase tests).

### 2.2 Resolution Strategies

| Strategy | Command / Action | When to Use |
|----------|------------------|-------------|
| Accept current | `git checkout --ours file` | Local branch is authoritative |
| Accept incoming | `git checkout --theirs file` | Remote branch should win |
| Manual merge | Edit conflict markers `<<<<<<<` / `=======` / `>>>>>>>` | Combine logic, especially for config/test files |
| Merge tool | `git mergetool` | Complex merges (e.g., orchestrator, large docs) |

**Manual merge checklist:**

- Understand intent of each change (read commit/PR context).
- Preserve both sets of business logic where applicable.
- Remove conflict markers before saving.

### 2.3 Complete the Merge

```bash
git add <resolved files>
git commit -m "merge: <source> into <target> (resolve conflicts)"
```

If rebasing:

```bash
git rebase --continue
```

### 2.4 PR Conflict Handling

**Command-line approach:**

```bash
git fetch origin
git checkout feature-branch
git merge origin/main       # or rebase
# Resolve conflicts, run tests
git push origin feature-branch
```

**GitHub UI:**

Open PR → "Resolve conflicts" → edit file(s), remove markers → "Mark as resolved" → "Commit merge".

---

## 3. Best Practices (Prevention & Resolution)

### 3.1 Conflict Prevention

- Keep feature branches short-lived; merge often.
- Pull latest main before pushing.
- Coordinate large edits (e.g., orchestrator) with team to avoid overlap.
- Use feature flags/config files for toggles (e.g., REAL/MOCK mode).

### 3.2 Conflict Resolution Discipline

- Understand the business logic you're merging; don't blindly accept ours/theirs.
- Run relevant tests (unit, integration, Supabase) after resolving.
- Document reasoning in commit messages ("kept REAL-mode config, dropped legacy flag").
- Request a peer review for high-risk merges.

### 3.3 Repository Health Guardrails

- Keep `.gitignore` accurate (venv, `.pytest_cache`, coverage artifacts).
- Commit messages: follow conventional commits or clear verbs (feat/chore/fix/test).
- Regularly rebase feature branches on main to avoid massive conflict bursts.
- Monitor repository size and GitHub Dependabot alerts; remediate promptly.

---

## 4. Troubleshooting Matrix

| Issue | Symptom | Resolution |
|-------|---------|------------|
| "Already up to date" but expecting changes | `git pull` shows nothing | `git fetch --all`, ensure you're on correct branch, `git merge origin/<branch>` explicitly |
| Accidental merge | Merge committed unintentionally | `git merge --abort` if in progress; `git reset --hard HEAD~1` if committed (not pushed) |
| Too many conflicts | Merge shows dozens of files | `git merge --abort`, rebase to latest main, or cherry-pick selective commits |
| Lost commits | Work disappeared | `git reflog` → identify commit → `git checkout <hash>` → new branch |
| "Upstream deleted branch" warnings | Stale remote-tracking branches | `git fetch --all --prune`, `git branch -r` to verify |

---

## 5. Git Configuration Checklist

| Config | Command | Purpose |
|--------|---------|---------|
| Fast-forward policy | `git config merge.ff only\|true\|false` | Enforce merge style per team policy |
| Merge tool | `git config --global merge.tool vimdiff` | Default tool for `git mergetool` |
| Conflict style | `git config --global merge.conflictstyle diff3` | Show base/common ancestor for clarity |
| Diff tool | `git config --global diff.tool vimdiff` | Optional for detailed comparisons |

---

## 6. References & Change Log

### References

- [Git Documentation: Merge & Rebase](https://git-scm.com/docs)
- [GitHub Docs: Resolving PR conflicts](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts)
- [Conventional Commits spec](https://www.conventionalcommits.org/)
- [SonarCloud, Dependabot, and security policy docs](https://github.com/Arisofia/abaco-loans-analytics/security)

### Change Log

| Date | Version | Summary |
|------|---------|---------|
| 2026-01-29 | 2.0 | Upgraded for G4.2/G5.0 workflows, Supabase integration, conflict-playbook alignment |
| 2026-01-11 | 1.0 | Initial release |

---

## Final Reminder

Keep this document up to date as Phase F tasks introduce new tooling (e.g., OpenTelemetry, advanced linting). Clean repositories and disciplined conflict handling are prerequisites for hitting our Phase F objectives (tracing, cost monitoring, security gates).
