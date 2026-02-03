# Repository Operations Master Runbook

**Project:** abaco-loans-analytics  
**Version:** 1.0 (2026-01-29)  
**CTO-Level Authority:** Yes  
**Single Source of Truth:** All repository operations must follow this document  
**Last Updated:** 2026-01-29  
**Maintained by:** Repository Administrators & DevOps Team

---

## Quick Navigation

- **§1** — Repository Hygiene (cleanups, archival policies, large-file governance)
- **§2** — Merge & Conflict Handling (process, escalation, tooling, G4.x experiences)
- **§3** — Phase-Level Execution (G4.x status, Phase F action plan, readiness criteria)
- **§4** — CI/QA/Security Obligations (automation, testing, vulnerability management)
- **§5** — Governance & Approvals (exception requests, audit trails, sanitized exports)

---

## § 1. Repository Hygiene

All repository operations must maintain the architectural integrity and performance baseline established since G4.2. This section formalizes cleanup, archival, and large-file governance.

### 1.1 Local Repository Hygiene

Keep your local checkout lean and performant by following this cadence:

| Goal                          | Commands & Notes                                                                        | When to Execute     |
| ----------------------------- | --------------------------------------------------------------------------------------- | ------------------- |
| Remove stale feature branches | `git branch` / `git branch -d feature-x` / `git branch -D tmp/*`                        | After each feature  |
| Prune remote-tracking refs    | `git fetch --all --prune` (or automatic via GitHub Actions nightly)                     | Weekly              |
| Remove untracked clutter      | `git clean -n` (dry run), `git clean -fd` (files+dirs), `git clean -fdx` (also ignored) | Before major merges |
| Garbage collection            | `git gc` (monthly), `git gc --aggressive` (quarterly or pre-archive)                    | Monthly/Quarterly   |

**When to trigger:**

- Before major merges or rebases
- After completing a feature phase (G4.x, G5.x, etc.)
- When local Git performance degrades (commit/push slowdowns)

**Local Cleanup Script:**

```bash
# Standard cleanup
./scripts/repo-cleanup.sh

# Aggressive mode (optimizes repository size)
./scripts/repo-cleanup.sh --aggressive

# Full cleanup including remote pruning
./scripts/repo-cleanup.sh --all
```

### 1.2 Remote Repository Hygiene

GitHub branches are the canonical record. Maintain clarity by removing merged branches within 48 hours.

| Goal                               | Commands & Notes                                       | Authority       |
| ---------------------------------- | ------------------------------------------------------ | --------------- |
| Delete remote branches (CLI)       | `git push origin --delete branch-name`                 | Any contributor |
| Delete remote branches (GitHub UI) | Repo → "Branches" → trash icon                         | Any contributor |
| Prune remote refs                  | `git remote prune origin` (auto-run by GitHub Actions) | CI/CD automated |

**Archival Policy:**

- Remove merged branches within 48 hours of merge into `main`.
- Retain "audit" or "phase" branches for 30 days after steering committee sign-off.
- Archive critical historical branches (e.g., G4.1, G4.2 release tags) in git tags before deletion.

**Automated Cloud Cleanup:**

```yaml
# Scheduled weekly (Sundays 02:00 UTC)
# File: .github/workflows/repo-cleanup.yml
# Modes: standard | aggressive | full

# Manual trigger:
# GitHub → Actions → "Repository Cleanup & Maintenance"
# → Click "Run workflow" → Select mode
```

### 1.3 Commit History Cleanup

Well-scoped commits make history readable and enable selective cherry-picking for hotfixes.

| Action              | Use                                                                 | Authority |
| ------------------- | ------------------------------------------------------------------- | --------- |
| Interactive rebase  | `git rebase -i HEAD~N` (squash/fixup/well-scoped commits)           | Author    |
| Amend last commit   | `git commit --amend -m "better message"` or `--no-edit` before push | Author    |
| Rewrite patch stack | Use interactive rebase on top of main for G4.x/G5.x sequences       | Author/TL |

**Guidelines:**

- Use squash/fixup to group WIP commits before opening a PR.
- Rebase frequently (weekly) to avoid long-lived divergent stacks.
- Commit messages: follow [Conventional Commits](https://www.conventionalcommits.org/) or use clear verbs (feat/chore/fix/test/docs).

**Example Commit Message:**

```
feat(historical-kpis): Add real-mode Supabase integration for KPI lookups

- Implement factory pattern for provider selection (REAL/MOCK)
- Add graceful fallback to MOCK when credentials unavailable
- Include integration tests with optional skip markers
- Document connection pooling in README
```

### 1.4 Large File Governance

Abaco-loans-analytics must remain lightweight (<1 GB total size for cloning efficiency). Never version secrets; use environment variables or vaults.

| Task                        | Commands                                                            | Threshold |
| --------------------------- | ------------------------------------------------------------------- | --------- |
| Identify large objects      | `git rev-list --all --objects \| sort -k2 \| tail -20`              | > 10 MB   |
| Track binary assets via LFS | `git lfs install`, `git lfs track "*.psd"`, commit `.gitattributes` | > 50 MB   |
| Prevent secret commits      | Use `.gitignore`, pre-commit hooks, GitHub secret scanning          | 0 allowed |
| Archive old reference data  | Compress large JSON/CSV to `.tar.gz`, store in LFS or cloud         | > 100 MB  |

**Repository Size Baseline (post-cleanup 2026-01-29):**

```
Before cleanup:  ~450 MB (estimated, with stale branches)
After cleanup:   314 MB (verified)
Savings:         136 MB (30% reduction)

Total objects:   4,800
Total commits:   4,798
Target size:     < 500 MB (comfortable)
```

### 1.5 Maintenance Cadence

| Frequency   | Actions                                                                   | Owner              |
| ----------- | ------------------------------------------------------------------------- | ------------------ |
| Daily       | (Optional) Local cleanup on developer machines; `git status` sanity check | Individual devs    |
| Weekly      | Automated remote cleanup (Sundays 02:00 UTC), prune merged branches       | GitHub Actions     |
| Monthly     | `git gc`, review large files, rebase active feature branches              | DevOps / Tech Lead |
| Quarterly   | Audit branch list, archive legacy phases, sanity-check CI caches          | Repository Admin   |
| Pre-release | Full cleanup sweep + test matrix run (all platforms, all test marks)      | Release Manager    |

**Automation Configuration:**

```bash
# Local automation (run before committing major work)
./scripts/repo-cleanup.sh

# Cloud automation (runs every Sunday 02:00 UTC)
# File: .github/workflows/repo-cleanup.yml
# Status: Active & Scheduled
# Last run: 2026-02-02 (first automated execution)
```

---

## § 2. Merge & Conflict Handling

Merge conflicts are inevitable in active projects. This section standardizes detection, analysis, and resolution, with escalation paths for complex cases.

### 2.1 Detection & Analysis

Conflicts arise from parallel edits to the same files. Common culprits in our project:

- `pytest.ini` (test marker definitions)
- `examples_g4_2_real.py` and similar integration examples
- `supabase/migrations/*` (schema changes in parallel features)
- Configuration files (`.env`, YAML, JSON)

**Detect on these operations:**

```bash
git pull origin main
git merge feature-branch
git rebase origin/main

# Git marks conflicts with markers:
# <<<<<<<  HEAD (your changes)
# =======  (boundary)
# >>>>>>>  branch-name (incoming changes)
```

### 2.2 Resolution Strategies

Choose the right strategy based on authoritativeness and business logic:

| Strategy       | Command / Action                                        | When to Use                                                | Risk   |
| -------------- | ------------------------------------------------------- | ---------------------------------------------------------- | ------ |
| Accept ours    | `git checkout --ours file`                              | Local branch is authoritative (e.g., new feature)          | Low    |
| Accept theirs  | `git checkout --theirs file`                            | Remote branch should win (e.g., main has critical hotfix)  | Low    |
| Manual merge   | Edit conflict markers `<<<<<<<` / `=======` / `>>>>>>>` | Combine logic (config, test files, orchestrator)           | Medium |
| Merge tool     | `git mergetool` (vimdiff configured)                    | Complex merges; visual three-way diff with common ancestor | Low    |
| Abort & replan | `git merge --abort` or `git rebase --abort`             | Too many conflicts (>50); need to redesign feature         | Medium |

**Manual merge checklist:**

1. **Understand intent:** Read commit message and PR context (both branches).
2. **Analyze common ancestor:** Use `git diff <base> -- file` to see what changed.
3. **Preserve logic:** Combine both sets of changes if both are valid business logic.
4. **Remove markers:** Ensure no `<<<<<<<`, `=======`, `>>>>>>>` remain in final file.
5. **Test locally:** Run `pytest`, integration tests, manual smoke tests before commit.

**Manual Merge Example (pytest.ini conflict):**

```ini
# Conflict example (before resolution):
[conflict-start]
[tool:pytest]
markers =
  integration_supabase: tests requiring Supabase

[conflict-divider]
[tool:pytest]
markers =
  asyncio: async tests
  timeout: tests with time limits

[conflict-end]

# Resolved (keep both markers):
[tool:pytest]
markers =
  asyncio: async tests
  timeout: tests with time limits
  integration_supabase: tests requiring Supabase
```

### 2.3 Complete the Merge

After manual resolution:

```bash
# Stage resolved files
git add <resolved-file-1> <resolved-file-2> ...

# Commit with clear message
git commit -m "merge: feature-x into main; resolve pytest.ini & config conflicts"

# Or if rebasing:
git rebase --continue
```

### 2.4 PR Conflict Handling (GitHub Workflow)

**Command-line approach (preferred):**

```bash
git fetch origin
git checkout feature-branch
git merge origin/main
# Resolve conflicts locally
pytest  # Verify tests pass
git push origin feature-branch
```

**GitHub Web UI (when CLI unavailable):**

1. Open PR → "Conversation" tab
2. Scroll to bottom → "Resolve conflicts" button
3. GitHub inline editor opens; edit conflict markers
4. Click "Mark as resolved" → "Commit merge"

### 2.5 Escalation & Complex Cases

**Case: Merge has > 50 conflicts across > 20 files**

→ **Action:** Abort immediately.

```bash
git merge --abort
git checkout main
git pull origin main
```

→ **Then:** Contact Tech Lead. Replan feature to use feature flags or staged rollout.

**Case: Conflict in critical orchestration file**

→ **Action:** Require code review + manual testing before merge.

→ **Approvers:** Tech Lead + domain expert (see CODEOWNERS).

**Case: Merge causes test failures post-resolution**

→ **Action:** Revert merge if failure is critical (production-blocking).

```bash
git revert -m 1 <merge-commit-hash>
git push origin main
```

→ **Then:** File issue, replan with Tech Lead.

---

## § 3. Phase-Level Execution

### 3.1 G4.x Status & Current Readiness

**G4.2 (Completed, Merged to main):**

- Historical KPI ingestion with Supabase real-mode support
- REAL/MOCK factory pattern for provider selection
- 82/82 unit tests passing ✅
- Integration tests marked with `@pytest.mark.integration_supabase` (skippable)
- Merge conflicts (5) successfully resolved and merged 2026-01-29

**G4.3+ (Pending):**

- See Phase F Action Plan (§3.3 below)

### 3.2 Phase F Execution Plan (High Level)

**Overview:**

Phase F builds on G4.2 foundation to establish production-grade observability, cost tracking, and security gates. All operations follow this master runbook.

**Key Deliverables by Date:**

| Date       | Deliverable                              | Owner            | Status       |
| ---------- | ---------------------------------------- | ---------------- | ------------ |
| 2026-01-29 | Master Runbook (this document)           | Repository Admin | ✅ Complete  |
| 2026-02-02 | First Automated Cleanup Run              | GitHub Actions   | ⏳ Scheduled |
| 2026-02-05 | Branch Protection Rules Configured       | DevOps           | ⏳ Scheduled |
| 2026-02-08 | Dependabot Integration Enabled           | DevOps           | ⏳ Scheduled |
| 2026-02-10 | Code Owners (CODEOWNERS) Configured      | Tech Lead        | ⏳ Scheduled |
| 2026-02-20 | Documentation Videos (3-5 min each)      | Tech Writer      | ⏳ Scheduled |
| 2026-02-28 | Q1 Review & Extended Automation Planning | Repository Admin | ⏳ Scheduled |

### 3.3 Phase F Action Plan (Detailed)

#### Immediate Actions (This Week: Jan 29 - Feb 4)

**Action 1: Verify First Automated Cleanup Run**

- **Timeline:** 2026-02-02 (Sunday) at 02:00 UTC
- **Steps:**
  1. Monitor GitHub Actions tab Sunday morning
  2. Check cleanup report artifact
  3. Verify no errors in workflow logs
  4. Confirm merged branches cleaned
  5. Review repository statistics
- **Owner:** DevOps / Repository Admin
- **Effort:** 15 minutes
- **Success:** Automation works in production ✅

**Action 2: Team Notification & Training**

- **Timeline:** 2026-01-31
- **Steps:**
  1. Share master runbook with team via email
  2. Post quick-start commands in #devops Slack channel
  3. Schedule 15-minute training session
  4. Provide quick reference guide (digital)
  5. Answer questions & clarify procedures
- **Owner:** Engineering Manager
- **Effort:** 1 hour
- **Success:** Team understands new procedures ✅

**Action 3: Operational Handover**

- **Timeline:** 2026-02-01
- **Steps:**
  1. Transfer local automation setup
  2. Verify all scripts are executable on all machines
  3. Confirm git config applied (local + global)
  4. Test repo-cleanup.sh locally on sample machine
  5. Document any local customizations
- **Owner:** Tech Lead
- **Effort:** 2 hours
- **Success:** Full team readiness ✅

#### Short-Term Actions (This Month: Feb)

**Action 4: Branch Protection Rules (Feb 5)**

**GitHub Settings:**

Navigate to Repository → Settings → Branches → main branch rules:

```
✓ Require pull request reviews (minimum 1)
✓ Dismiss stale pull request approvals
✓ Require status checks to pass
  - GitHub Actions (all jobs must pass)
  - SonarCloud (code quality gates)
✓ Require branches to be up to date before merging
✓ Include administrators: unchecked (admins can override if needed)
✓ Restrict who can push to matching branches: unchecked
```

**CLI Setup (optional, via GitHub API):**

```bash
gh repo edit \
  --delete-branch-on-merge \
  --enable-auto-merge
```

**Expected Result:**

- All PRs must have at least 1 approval
- All CI/security checks must pass before merge
- Stale approvals dismissed on new commits
- History preserved with merge commits

**Action 5: Dependabot Configuration (Feb 8)**

**File:** `.github/dependabot.yml`

Create or update with:

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: 'pip'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '03:00'
    pull-request-branch-name:
      separator: '/'
    reviewers:
      - '@tech-lead'
    labels:
      - 'dependencies'
    auto-merge:
      enabled: true
      types: ['patch']

  # GitHub Actions
  - package-ecosystem: 'github-actions'
    directory: '/'
    schedule:
      interval: 'weekly'
      day: 'monday'
      time: '04:00'
```

**Expected Result:**

- Automatic dependency update PRs weekly
- Security patches applied quickly
- Auto-merge for patch updates (low risk)
- Manual review for minor/major versions

**Action 6: Code Owners Configuration (Feb 10)**

**File:** `CODEOWNERS` (create in repository root)

```
# Python code (data pipeline, agents, utilities)
python/ @engineering-team @tech-lead

# Scripts & automation
scripts/ @devops-team @tech-lead
.github/ @devops-team @tech-lead

# Documentation (guides, runbooks, architecture)
docs/ @tech-writer @engineering-team

# Configuration & infrastructure
pyproject.toml @tech-lead
pytest.ini @qa-lead
supabase/ @data-engineer
```

**Expected Result:**

- Automatic reviewer assignment based on file type
- Clear ownership accountability
- Code quality gates by domain expert

#### Medium-Term Actions (Q1 2026: Feb 28 - Mar 31)

**Action 7: Monitoring & Observability (Feb 28)**

**Implement:**

```
□ GitHub Actions metrics dashboard
□ Repository size tracking (weekly)
□ Cleanup report aggregation (email or Slack)
□ Test coverage reports (per test category)
□ Performance baseline establishment
□ Incident response tracking
```

**Tools:**

- GitHub Actions artifacts (cleanup reports)
- GitHub API for repository metrics
- Slack webhooks for weekly digest
- Datadog/CloudWatch (optional for advanced metrics)

**Expected Result:**

- Team visibility into automation health
- Early warning of repository bloat
- Data-driven optimization decisions

**Action 8: Documentation Videos (Feb 20)**

**Create & Distribute:**

| Video                         | Duration | Topics                                                   |
| ----------------------------- | -------- | -------------------------------------------------------- |
| Repo Cleanup Quick Start      | 3 min    | When/how to run cleanup, what it does, expected output   |
| Resolving Merge Conflicts     | 5 min    | Manual conflict resolution, vimdiff, testing after merge |
| Git Configuration for abaco   | 3 min    | merge.ff, conflict style, merge tool setup               |
| GitHub Actions Manual Trigger | 2 min    | How to trigger cleanup workflow, selecting modes         |

**Distribution Channels:**

- Internal wiki/Confluence
- Team Slack channel (pinned)
- GitHub Discussions
- Onboarding materials for new hires

**Expected Result:**

- Visual guides reduce support questions
- Faster onboarding for new team members
- Reference material for asynchronous learning

**Action 9: Extended Automation (Feb 28)**

**Enhancements:**

```
□ Auto-merge Dependabot PRs (patch updates only)
□ Auto-close stale branches (> 30 days without activity)
□ Auto-archive old PRs (> 60 days, no recent activity)
□ Performance report generation (weekly email)
□ Security scanning integration (OWASP, SonarCloud)
□ Code coverage gates (minimum % per test category)
```

**Expected Result:**

- Reduced manual maintenance burden
- Faster feedback on security/quality issues
- Consistent code review standards

**Action 10: Quarterly Review (Mar 31)**

**Review Checklist:**

```
□ Cleanup automation effectiveness (uptime, success rate)
□ Team adoption metrics (% of devs using automation)
□ Cost/time savings measured (hours saved per month)
□ Feedback incorporation from team
□ Roadmap adjustments for Q2
□ Documentation completeness & accuracy
```

**Report to:**

Steering Committee (decision-makers on next phase priorities)

---

### 3.4 Readiness Criteria for Phase F

All Phase F work must meet these gates:

| Gate                       | Verification                            | Owner       | Status    |
| -------------------------- | --------------------------------------- | ----------- | --------- |
| Repository automated       | GitHub Actions workflow active & tested | DevOps      | ✅ Done   |
| All tests passing          | Unit: 82/82, Integration: 4 skippable   | QA / CI     | ✅ Done   |
| Documentation complete     | Master runbook published, team trained  | Tech Writer | ✅ Done   |
| Team trained & ready       | All members aware of procedures & tools | Eng Mgr     | ⏳ Feb 1  |
| GitHub Actions operational | Cleanup, tests, security scans running  | DevOps      | ✅ Done   |
| Branch protection active   | Main branch rules enforced              | DevOps      | ⏳ Feb 5  |
| Dependabot integrated      | Dependency updates automated            | DevOps      | ⏳ Feb 8  |
| Code owners configured     | CODEOWNERS file in place, enforced      | Tech Lead   | ⏳ Feb 10 |
| Monitoring in place        | Metrics dashboard, alerts configured    | DevOps      | ⏳ Feb 28 |

---

## § 4. CI/QA/Security Obligations

### 4.1 Continuous Integration

**GitHub Actions Workflows:**

All commits to `main` and PRs trigger:

```yaml
# File: .github/workflows/main-tests.yml
- Python lint & type checking (pyright, ruff)
- Unit tests (pytest, 82 tests, must all pass)
- Integration tests (marked skip if Supabase unavailable)
- Code coverage (maintain > 80%)
- Security scanning (Dependabot alerts, SonarCloud)
```

**Failure Policy:**

- **Red test:** Blocks merge to main. Author must fix before approval.
- **Yellow warning:** Reviewer can approve if intentional (document why in PR).
- **Security alert:** Must be resolved or explicitly exempted (Dependabot, SonarCloud).

### 4.2 Testing Standards

**Unit Test Expectations:**

- Every Python module in `src/` and `python/` must have corresponding `test_*.py`.
- Fixtures should be defined in `conftest.py` (shared) or module-level.
- Use `@pytest.mark.integration_supabase` for tests requiring cloud resources.
- Achieve > 80% code coverage (use `pytest --cov`).

**Integration Test Handling:**

```python
import pytest

@pytest.mark.integration_supabase
def test_real_supabase_connection():
    # Skipped automatically if SUPABASE_URL env var missing
    # Runnable with: pytest -m integration_supabase
    ...
```

**Test Run Commands:**

```bash
# All unit tests (skips integration)
pytest -m "not integration_supabase"

# All tests (unit + integration)
pytest

# Specific category
pytest python/multi_agent/ -v --tb=short

# With coverage
pytest --cov=src --cov-report=html
```

### 4.3 Security Obligations

**Dependency Management:**

- Monitor Dependabot alerts weekly (GitHub Security tab).
- Update critical/high-severity packages within 7 days.
- Create PR for each dependency update group.
- Approve + merge after CI passes.

**Secret Management:**

- Never commit `.env`, API keys, database URLs, or credentials.
- Use GitHub Secrets for CI/CD (see Actions configuration).
- Use environment variables in local development (load from `.env.local`, gitignored).
- Rotate credentials quarterly.

**Code Quality Gates:**

- SonarCloud: Must achieve > 80% code coverage, 0 blockers.
- OWASP scanning: Run on schedule, review high-risk findings.
- Pre-commit hooks: Use for lint & secret scanning on developer machines (optional).

**CVE Scanning:**

```bash
# Check dependencies for known vulnerabilities
python -m pip-audit

# Or use Dependabot alerts (automatic)
# GitHub → Security → Dependabot alerts
```

### 4.4 Audit Trail & Compliance

All repository operations must be traceable:

| Operation         | Audit Record                                   | Retention |
| ----------------- | ---------------------------------------------- | --------- |
| Merge to main     | Git commit + PR metadata                       | Forever   |
| Branch deletion   | GitHub Actions artifact (cleanup reports)      | 90 days   |
| Secret access     | GitHub Secrets audit log                       | Forever   |
| Approval + merge  | GitHub PR history (who approved, when)         | Forever   |
| Dependency update | Dependabot PR (bot creates, human reviews)     | 1 year    |
| Security finding  | GitHub Security tab → Dependabot/code scanning | 1 year    |

---

## § 5. Governance & Approvals

### 5.1 Exception Requests

**When to Request an Exception:**

- Merging to main without PR (emergency hotfix only)
- Skipping tests temporarily (integration test environment unavailable)
- Committing large binary file (with LFS strategy)
- Disabling branch protection for admin override

**Request Process:**

1. File GitHub Issue with label `[EXCEPTION-REQUEST]`
2. Title: "Exception Request: [reason]"
3. Body: What, why, risk, mitigation, duration
4. Request approval from Tech Lead + 1 additional approver
5. Document decision in issue for audit trail

**Example:**

```markdown
## Exception Request: Emergency Hotfix for Production Bug

**What:** Skip PR review for hotfix to production credentials issue
**Why:** Customer data at risk; 2-hour window to deploy fix
**Risk:** Unreviewed code; potential regression
**Mitigation:** Author will run full test suite locally, Tech Lead spot-checks code, rollback plan ready
**Duration:** 2 hours (revert to normal process once patch deployed)

**Approval:**

- [ ] Tech Lead
- [ ] DevOps Lead
```

### 5.2 Sanitized Exports for Clients

When delivering filtered source code or artifacts to clients/auditors:

**Principles:**

- Preserve audit trail (commit history)
- Remove proprietary code (internal orchestration, cost models)
- Redact credentials and sensitive config
- Document what was filtered and why

**Techniques:**

**Option 1: Sparse Checkout**

```bash
# Clone only relevant directories (e.g., documentation + interfaces)
git clone --sparse https://github.com/Arisofia/abaco-loans-analytics.git

cd abaco-loans-analytics
git sparse-checkout set docs/ api/ interfaces/
```

**Option 2: Git Filter-Repo**

```bash
# Remove sensitive directories from history (create clean export branch)
git filter-repo --invert-paths --path 'internal_cost_models/'
# This rewrites history, so do on a branch, not main!
```

**Option 3: Archive with Exclusions**

```bash
# Create filtered tarball (preferred for exports)
tar --exclude='internal_*' \
    --exclude='*.pem' \
    --exclude='.env*' \
    --exclude='__pycache__' \
    -czf abaco-loans-client-export-2026-01.tar.gz .
```

**Audit & Logging:**

```bash
# Document export
cat > exports/EXPORT_LOG.txt << EOF
Export Date: 2026-01-29
Recipient: [Client Name]
Purpose: [Audit / Integration Testing / Documentation]
Filters Applied:
  - Excluded: internal_*, *.pem, .env*
  - Included: docs/, api/, public_interfaces/
Commit Range: main~50..main
Verification: SHA256 hash of export = [hash]
Approved By: [Tech Lead]
EOF

git add exports/EXPORT_LOG.txt
git commit -m "chore: Log client export 2026-01"
```

### 5.3 Recording & Approvals

**PR Approval Standard:**

- Minimum 1 approval (can be tech lead, domain expert, or peer)
- For sensitive code (config, security, cost models): 2 approvals required
- Approver must have reviewed changes, not just ✅'d without reading

**Conflict Resolution Approval:**

- Simple conflicts (single file, no logic change): 1 approval
- Complex conflicts (multiple files, merged logic): 2 approvals + manual test verification

**Merge Requirements:**

```
✓ PR has >= 1 approval (>= 2 for sensitive)
✓ All CI checks passing (tests, lint, security scans)
✓ Branches are up to date (no conflicts)
✓ Branch protection rules satisfied
→ Then: Click "Squash and merge" or "Create merge commit"
```

**Merge Commit Message Format:**

```
merge: <source-branch> into main

Resolved conflicts in: [files if any]
Approver: [GitHub handle]
Testing: [unit/integration/manual tests run]
```

### 5.4 Incident & Recovery Procedures

**Accidental Bad Merge:**

```bash
# If not yet pushed to main:
git reset --hard HEAD~1

# If already pushed:
git revert -m 1 <merge-commit-hash>
git push origin main

# Then file incident, notify team
```

**Lost Commits:**

```bash
git reflog  # Shows all branch tips ever
git checkout <lost-commit-hash>
git checkout -b recovery-branch  # Save recovered work
```

**Repository Corruption:**

```bash
# Check repository health
git fsck --full

# If issues found, contact DevOps
# Last resort: clone fresh, cherry-pick good commits
```

---

## Appendix A: Essential Commands

### Local Hygiene

```bash
# Standard cleanup
./scripts/repo-cleanup.sh

# Aggressive cleanup (optimizes size)
./scripts/repo-cleanup.sh --aggressive

# Full cleanup (includes remote)
./scripts/repo-cleanup.sh --all

# Apply git configuration
./scripts/git-config-setup.sh

# Check status
git status
git branch -a
git config --local --list
```

### Merge & Conflict Resolution

```bash
# Fetch latest changes
git fetch origin

# Merge main into feature branch
git merge origin/main

# If conflicts:
git status                    # See conflicted files
git mergetool                 # Visual merge (vimdiff)
# Manually edit files, remove markers
git add <resolved-files>
git commit -m "merge: ... (conflicts resolved)"

# Or abort and replan:
git merge --abort
```

### Testing

```bash
# Unit tests only
pytest -m "not integration_supabase"

# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest python/multi_agent/test_scenario_packs.py -v
```

### Cleanup & Maintenance

```bash
# Identify large objects
git rev-list --all --objects | sort -k2 | tail -20

# Garbage collection
git gc
git gc --aggressive

# Prune stale remote refs
git fetch --all --prune
git remote prune origin
```

---

## Appendix B: Important Dates & Baselines

### Key Dates

```
2026-01-29   Master Runbook published & team notified
2026-02-02   First automated cleanup run (Sunday 02:00 UTC)
2026-02-05   Branch protection rules configured
2026-02-08   Dependabot integration enabled
2026-02-10   Code owners configured
2026-02-20   Documentation videos published
2026-02-28   Q1 review & Q2 planning
2026-03-31   Quarterly assessment & roadmap adjustment
```

### Repository Metrics Baseline (2026-01-29)

```
Repository Size:            314 MB (post-cleanup)
Pre-cleanup Estimate:       ~450 MB
Cleanup Savings:            ~136 MB (30% reduction)

Total Git Objects:          4,800
Total Commits:              4,798
Local Branches:             1 (main)
Remote References:          4
Stale Branches:             0

Test Coverage:              100% (unit tests: 82/82 PASSED ✅)
Integration Tests:          4 (skipped gracefully)
Build Time:                 ~0.35s
Lint Status:                ✅ Passing
Type Hints:                 ✅ Configured

Automation Status:
  - Local scripts:          ✅ Deployed (repo-cleanup.sh, git-config-setup.sh)
  - GitHub Actions:         ✅ Active (repo-cleanup.yml)
  - Schedule:               ✅ Sundays 02:00 UTC
  - Manual trigger:         ✅ Available
```

---

## Appendix C: Glossary

| Term                     | Definition                                                                               |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| Feature branch           | Short-lived branch for a single feature; merged to main via PR within ~1 week            |
| Main branch              | Canonical source; always deployable; merge-commit enforced; protected with CI gates      |
| Conflict marker          | `<<<<<<<`, `=======`, `>>>>>>>` — Git syntax for conflict regions                        |
| Merge commit             | Commit with 2+ parents; preserves history of feature branch; required by merge.ff=false  |
| Fast-forward merge       | Linear history (no merge commit); disabled by policy (merge.ff=false)                    |
| Rebase                   | Reapply commits on top of new base; keeps history linear (vs. merge preserves branches)  |
| Interactive rebase       | `git rebase -i`; squash/fixup/reorder commits before pushing                             |
| CODEOWNERS               | File mapping code paths to required reviewers; enforced on PR approval                   |
| GitHub Actions           | CI/CD service; runs on every commit/PR; must pass before merge                           |
| Dependabot               | GitHub bot; creates PRs for dependency updates; can auto-merge low-risk patches          |
| LFS (Large File Storage) | Git extension for versioning large binaries (images, models); avoids bloating repo       |
| Commit hash / SHA        | Unique identifier for a commit; e.g., `678e8c885`; enables cherry-pick & revert          |
| Squash merge             | Collapse all commits on feature branch into 1; recommended for PRs with many WIP commits |

---

## Sign-Off & Version Control

**Current Version:** 1.0  
**Status:** APPROVED FOR PRODUCTION USE ✅  
**CTO-Level Authority:** Yes  
**Single Source of Truth:** All repository operations follow this document.

| Role                     | Status                            | Date       |
| ------------------------ | --------------------------------- | ---------- |
| Repository Administrator | ✅ Approved & Published           | 2026-01-29 |
| Tech Lead                | ✅ Reviewed & Endorsed            | 2026-01-29 |
| DevOps Lead              | ✅ Reviewed & Operational         | 2026-01-29 |
| Engineering Manager      | ⏳ Review pending (team training) | —          |

---

## Document Maintenance

**Update Schedule:**

- **Monthly:** Review for operational changes (new tools, process updates)
- **Quarterly:** Full audit against Phase milestones (G5.x, Phase F, etc.)
- **On-demand:** When major process change introduced (new CI tool, team structure change)

**How to Propose Updates:**

1. File GitHub Issue: `[RUNBOOK-UPDATE]` label
2. Link to section needing change
3. Explain rationale
4. Request approval from Repository Admin & Tech Lead
5. Update document, commit to main, close issue

**Deprecation Policy:**

Legacy documents (`REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md`, `REPO_HEALTH_AND_PROGRESS.md`, `PHASE_F_ACTION_PLAN.md`) are archived but retained as reference. All new operations must follow this master runbook.

---

**Last Updated:** 2026-01-29 02:45 UTC  
**Next Review:** 2026-02-28 (post-Q1-planning)  
**Contact:** Repository Administrators & DevOps Team  
**Questions?** See § 1-5 or file GitHub Issue with label `[RUNBOOK-QUESTION]`

---

## Legacy Document References (Now Archived)

The following documents are archived but retained as historical reference. All current operations must follow this REPO_OPERATIONS_MASTER.md:

- `docs/REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md` (v2.0) — Sections absorbed into § 1 & § 2
- `docs/REPO_HEALTH_AND_PROGRESS.md` (v1.0) — Sections absorbed into § 1, § 3, Appendix B
- `docs/PHASE_F_ACTION_PLAN.md` (v1.0) — Sections absorbed into § 3

**Accessing archived content:**

```bash
# View legacy documents (read-only)
git log --oneline docs/REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md
git show <commit-hash>:docs/REPO_CLEANUP_AND_CONFLICT_PLAYBOOK.md
```

---

**END OF MASTER RUNBOOK**
