# Contributing to Abaco Loans Analytics

This guide outlines our development practices to ensure code quality, traceability, and collaboration. For deeper workflow details, see the GitHub Workflow Runbook and Governance Framework.

## Branch Naming Conventions
Use consistent prefixes to organize work:
feat/<description>
fix/<description>
chore/<description>
docs/<description>
refactor/<description>
test/<description>
perf/<description>

## Commit Message Convention (Conventional Commits)
<type>(<scope>): <subject>

Types: feat, fix, chore, docs, refactor, test, perf. Use imperative subjects, no trailing period, ~50 chars.

## Pull Request Workflow
1. **Squash on merge**: Multiple logical commits are fine during development; the PR is squashed on merge to keep history clean.
2. **Quality gates**: Lint, tests, type-checks, CodeQL, SonarCloud, and CI pipelines must be green.
3. **Ownership**: Assign yourself and request required reviewers; respond to bot feedback.
4. **Traceability**: Keep scope tight; include clear commit messages and issue/spec links.

## Merging
- Default: squash-and-merge (one squashed commit to main).
- Stale PRs auto-close after inactivity unless labeled `do-not-close`, `important`, or `blocked`.

## Hygiene
- DO: descriptive commits, focused changes, reference issues, keep tests passing.
- DON’T: generic messages, mix unrelated changes, commit without tests, force-push shared branches.

## Dependency Management
- Dependabot runs for npm/pip/yarn daily; GitHub Actions weekly; auto-labeled (`dependencies`, `npm`/`python`/`ci-cd`).

## Automation & CI/CD
- Auto-close stale PRs with exemptions above.
- Quality gates: lint, unit tests, type checks, coverage, SonarQube quality gates.

## Questions?
Contact the dev team or open an issue.
