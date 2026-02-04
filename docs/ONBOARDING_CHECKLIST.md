# Repository Onboarding Checklist

**For:** New team members, contractors, and periodic auditors  
**Mandatory:** Yes (all items must be completed before contributing code)  
**Reference:** [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md)  
**Last Updated:** 2026-01-29

---

## Day 1: Account & Access Setup

- [ ] **GitHub Account**
  - [ ] Request invitation to `Arisofia/abaco-loans-analytics` organization
  - [ ] Verify access: Visit [github.com/Arisofia/abaco-loans-analytics](https://github.com/Arisofia/abaco-loans-analytics)
  - [ ] Configure 2FA (two-factor authentication) on GitHub account
  - [ ] Set up SSH keys (`ssh-keygen -t rsa`, add to GitHub settings)

- [ ] **Local Development Environment**
  - [ ] Clone repository: `git clone git@github.com:Arisofia/abaco-loans-analytics.git`
  - [ ] Navigate to repository: `cd abaco-loans-analytics`
  - [ ] Verify Python version (≥ 3.10): `python --version`
  - [ ] Create virtual environment: `python -m venv venv`
  - [ ] Activate venv: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)
  - [ ] Install dependencies: `pip install -r requirements.txt`
  - [ ] Verify installation: `pytest --co` (should list all tests, no errors)

- [ ] **Git Configuration** (critical for repository operations)
  - [ ] Run setup script: `./scripts/git-config-setup.sh`
  - [ ] Verify local config: `git config --local --list`
  - [ ] Verify global config: `git config --global --list`
  - [ ] Test merge tool: `git mergetool` (should launch vimdiff)

---

## Day 1-2: Documentation & Standards

- [ ] **REQUIRED READING** (do not skip — master runbook is your single source of truth)
  - [ ] Read [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md) — **ENTIRE DOCUMENT**
    - [ ] § 1: Repository Hygiene (cleanup, archival, large-file governance)
    - [ ] § 2: Merge & Conflict Handling (resolution strategies, escalation)
    - [ ] § 3: Phase-Level Execution (G4.x status, Phase F plan, readiness criteria)
    - [ ] § 4: CI/QA/Security Obligations (automation, testing, vulnerability management)
    - [ ] § 5: Governance & Approvals (exception requests, sanitized exports, incident recovery)
    - [ ] Appendix A-C: Commands, dates, glossary

- [ ] **Project Documentation**
  - [ ] Read [README.md](README.md) (project overview)
  - [ ] Skim [DEVELOPMENT.md](docs/DEVELOPMENT.md) (if exists, development guide)
  - [ ] Review [CONTRIBUTING.md](CONTRIBUTING.md) (if exists, contribution guidelines)
  - [ ] Check [SECURITY.md](SECURITY.md) (if exists, security policy)

- [ ] **Architecture & Context**
  - [ ] Review [docs/architecture.md](docs/architecture.md) or similar (if exists)
  - [ ] Understand G4.2 implementation (see [G4_2_IMPLEMENTATION_SUMMARY.md](G4_2_IMPLEMENTATION_SUMMARY.md))
  - [ ] Understand Phase F roadmap (§ 3 of master runbook)

---

## Day 2-3: Hands-On Practice

- [ ] **Git Workflow Practice**
  - [ ] Create a feature branch: `git checkout -b feature/onboarding-test-<name>`
  - [ ] Make a trivial change (e.g., add your name to a test file, no code)
  - [ ] Commit with proper message: `git commit -m "chore: add <name> to onboarding test"`
  - [ ] Push to remote: `git push origin feature/onboarding-test-<name>`
  - [ ] Open a PR on GitHub (use [.github/pull_request_template.md](.github/pull_request_template.md))
  - [ ] Have a team member review & approve
  - [ ] Merge PR to `main` via GitHub UI

- [ ] **Repository Cleanup Practice**
  - [ ] Run local cleanup: `./scripts/maintenance/repo_maintenance.sh --mode=standard`
  - [ ] Review output (merged branches removed, GC optimized, stats reported)
  - [ ] Verify no errors: Exit code should be 0

- [ ] **Testing Practice**
  - [ ] Run unit tests: `pytest -m "not integration_supabase" -v`
  - [ ] Verify 82/82 tests pass (or current baseline)
  - [ ] Run lint: `ruff check . --select=E,W,F`
  - [ ] Run type checker: `pyright .`

---

## Day 3-4: Team Onboarding

- [ ] **Team Introductions**
  - [ ] Meet Tech Lead (ask about current Phase F tasks)
  - [ ] Meet DevOps Lead (ask about CI/CD, GitHub Actions, automation)
  - [ ] Meet QA Lead (ask about testing standards, coverage expectations)
  - [ ] Understand team communication channels (#devops-automation, #eng, etc.)

- [ ] **Understanding Project Structure**
  - [ ] Walk through directory layout: `ls -la` (see [Workspace Info](docs/README.md) or ask team)
  - [ ] Understand Python module structure: `python/`, `src/`, `tests/`
  - [ ] Identify key files: `pyproject.toml` (dependencies), `pytest.ini` (tests), `.github/workflows/` (CI/CD)
  - [ ] Review data flow (e.g., G4.2 pipeline: ingestion → transformation → KPI computation)

- [ ] **Getting First Task**
  - [ ] Identify a small bug fix or documentation improvement
  - [ ] File issue or claim existing issue from backlog
  - [ ] Discuss approach with Tech Lead (5-10 min sync)
  - [ ] Complete task following [PR checklist](.github/pull_request_template.md)

---

## Ongoing: Weekly & Monthly Checkpoints

### Weekly

- [ ] **Repository Health Monitoring**
  - [ ] Check GitHub Actions for failed tests: [Actions](https://github.com/Arisofia/abaco-loans-analytics/actions)
  - [ ] Review Dependabot alerts (if any): [Dependabot alerts](https://github.com/Arisofia/abaco-loans-analytics/security/dependabot)
  - [ ] Participate in team standup (discuss blockers, repository issues)

- [ ] **Personal Development**
  - [ ] Complete at least 1 task (PR, bug fix, documentation improvement)
  - [ ] Request code review on PR (wait for approval)
  - [ ] Review others' PRs (become familiar with team standards)

### Monthly

- [ ] **Competency Assessment**
  - [ ] Can you resolve a merge conflict without help? (practice per § 2.2)
  - [ ] Can you explain the Phase F roadmap? (study § 3)
  - [ ] Can you run local cleanup & identify large objects? (practice § 1)
  - [ ] Can you navigate & use the master runbook? (§ 1-5 fluency)

- [ ] **Documentation Review**
  - [ ] Re-read [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md) sections relevant to your tasks
  - [ ] Propose improvements via GitHub Issues labeled `[RUNBOOK-UPDATE]`
  - [ ] Update personal cheat sheets or wiki entries as needed

- [ ] **Repository Maintenance**
  - [ ] Participate in monthly cleanup (DevOps-led)
  - [ ] Review repository metrics (size, test coverage, CI times)
  - [ ] Report issues or bottlenecks to Tech Lead

---

## Role-Specific Onboarding

### For Software Engineers (Backend/Data)

- [ ] **Code Expectations**
  - [ ] Understand code style (Conventional Commits, docstring format, type hints)
  - [ ] Complete first feature branch (bug fix or small feature)
  - [ ] Achieve > 80% test coverage on your code
  - [ ] Pass lint & type checking (`ruff`, `pyright`)

- [ ] **Testing Requirements**
  - [ ] Write unit tests for every new function/method
  - [ ] Test edge cases and error conditions
  - [ ] Mark integration tests with `@pytest.mark.integration_supabase`
  - [ ] Run full test suite before pushing: `pytest -m "not integration_supabase"`

- [ ] **Data Pipeline (G4.x/Phase F)**
  - [ ] Understand REAL/MOCK provider pattern (see [G4_2_IMPLEMENTATION_SUMMARY.md](G4_2_IMPLEMENTATION_SUMMARY.md))
  - [ ] Know how to test without Supabase credentials (graceful fallback)
  - [ ] Understand KPI ingestion flow (ask Tech Lead for walkthrough)

### For DevOps/SRE

- [ ] **Infrastructure & Automation**
  - [ ] Review [.github/workflows/](https://github.com/Arisofia/abaco-loans-analytics/tree/main/.github/workflows) directory
  - [ ] Understand cleanup automation (weekly, manual trigger, artifact reports)
  - [ ] Understand branch protection rules (main branch, required checks)
  - [ ] Learn Dependabot configuration & auto-merge strategy

- [ ] **Incident Response**
  - [ ] Know how to revert a bad merge: `git revert -m 1 <hash>`
  - [ ] Know how to troubleshoot CI failures (read GitHub Actions logs)
  - [ ] Know escalation path (who to contact if automation fails)
  - [ ] File incident issue with `[INCIDENT]` label

### For QA/Test Engineers

- [ ] **Testing Infrastructure**
  - [ ] Understand pytest markers (`@pytest.mark.integration_supabase`, `@pytest.mark.asyncio`, etc.)
  - [ ] Know how to run subset of tests (filter by marker, path, name)
  - [ ] Review test results & coverage: `pytest --cov=src --cov-report=html`
  - [ ] Identify gaps in test coverage (report to team)

- [ ] **Quality Gates**
  - [ ] Understand SonarCloud checks (code coverage, code smell, security)
  - [ ] Know Dependabot workflow (auto-created PRs, security alerts)
  - [ ] Review GitHub Actions status checks (what blocks merge?)
  - [ ] Help triage test failures (unit vs. integration vs. flaky)

### For Tech Lead/Repository Admin

- [ ] **Full Master Runbook Mastery**
  - [ ] § 1-5: Complete fluency
  - [ ] Appendix A-C: Quick reference ready
  - [ ] Can explain every section to new team members

- [ ] **Governance & Approvals**
  - [ ] Authority to approve exception requests (§ 5.1)
  - [ ] Authority to record & log sanitized exports (§ 5.2)
  - [ ] Authority to escalate merge conflicts (§ 2.5)
  - [ ] Authority to propose runbook updates (Document Maintenance section)

- [ ] **Operational Responsibility**
  - [ ] Monitor GitHub Actions (weekly)
  - [ ] Review Dependabot alerts (weekly)
  - [ ] Conduct monthly maintenance checks
  - [ ] Lead quarterly reviews (§ 3.4)
  - [ ] Update master runbook as needed

---

## Sign-Off

**Onboarding Completion:**

After completing all sections above, request sign-off from Tech Lead or Repository Admin:

| Item                                     | Completed | Date             |
| ---------------------------------------- | --------- | ---------------- |
| Day 1: Account & Access Setup            | [ ]       | \***\*\_\_\*\*** |
| Day 1-2: Documentation & Standards       | [ ]       | \***\*\_\_\*\*** |
| Day 2-3: Hands-On Practice               | [ ]       | \***\*\_\_\*\*** |
| Day 3-4: Team Onboarding                 | [ ]       | \***\*\_\_\*\*** |
| Role-Specific Onboarding (if applicable) | [ ]       | \***\*\_\_\*\*** |

**Reviewer:** \***\*\*\*\*\*\*\***\_\***\*\*\*\*\*\*\*** (Tech Lead / Repository Admin)<br>
**Date:** \***\*\_\_\*\***

**Notes:**

[Any special circumstances, blockers, or customizations]

---

## Quick Reference During Onboarding

**Can't remember something?**

| Question                                 | Answer                                                                                 |
| ---------------------------------------- | -------------------------------------------------------------------------------------- |
| How do I run tests?                      | `pytest -m "not integration_supabase" -v`                                              |
| How do I resolve a merge conflict?       | See [§ 2.2](docs/REPO_OPERATIONS_MASTER.md#22-resolution-strategies) of master runbook |
| How do I clean up my local repo?         | `./scripts/maintenance/repo_maintenance.sh --mode=standard`                            |
| How do I apply git config?               | `./scripts/git-config-setup.sh`                                                        |
| What's the master runbook?               | [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md) — Read it!            |
| Where do I ask for help?                 | #devops-automation (Slack) or file [RUNBOOK-QUESTION] issue                            |
| How do I propose a change to procedures? | File [RUNBOOK-UPDATE] issue with rationale                                             |
| What's the Phase F roadmap?              | § 3 of master runbook + action plan with dates                                         |

---

**Welcome to the team! 🎉 If you have questions, ask in #devops-automation or file a GitHub issue. Don't hesitate—we're here to help.**

**Last Updated:** 2026-01-29  
**Next Review:** 2026-02-28  
**Questions?** See [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md) or contact Tech Lead
