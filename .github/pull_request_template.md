## Description

**Summary** (2–3 sentences):
Provide a succinct description of what this PR accomplishes and why it is necessary.

**Problem Statement**:
What functional or technical problem does this PR address? What is the underlying root cause?

**Related Issues & Context**:
Reference all related issues, tickets, architecture documents, or decision records.

Fixes: #(issue_number)

---

## Type of Change

Select all that apply:

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactor/tech debt
- [ ] Performance optimization
- [ ] Security improvement
- [ ] Other (explain): _______________

---

## Checklist

**All boxes must be checked. If any item cannot be completed, it must be clearly flagged, justified, and may warrant rejection until resolved.**

### Code Quality & Standards

- [ ] Code strictly follows project style/conventions (see [CONTRIBUTING.md](../CONTRIBUTING.md) or run `npm run lint`)
- [ ] Performed thorough self-review; removed redundant/legacy code and dead imports
- [ ] Documented all non-trivial logic with clear docstrings (include: purpose, parameters, return values; complex algorithms require inline comments explaining *why*)
- [ ] No hardcoded secrets, credentials, PII, or sensitive data exposed in code or logs

### Testing & Validation

- [ ] Comprehensive, meaningful automated tests written for new/changed functionality and edge cases
  - Minimum ≥80% coverage for new code
  - Tests verify happy path, error cases, and boundary conditions
- [ ] All new and existing tests pass locally and in CI
- [ ] Edge cases and error conditions are explicitly tested
- [ ] (Database changes) Schema migrations reviewed and rollback plan documented

### Documentation & User Impact

- [ ] All user-facing and business logic changes reflected in documentation (API docs, README, user guide, architecture diagrams, decision records—as applicable)
- [ ] Complex or non-obvious implementation choices explained in comments or design docs
- [ ] (Breaking changes) Migration path, deprecation timeline, and upgrade guide clearly documented

### Dependencies & Security

- [ ] Downstream dependencies reviewed and updated as appropriate
  - Run: `npm audit` and review package-lock.json diffs
  - Security team/DevOps coordination completed if required
- [ ] No new warnings or errors in CI, linting, or runtime

### Performance & Operations

- [ ] Performance impact statement (if applicable):
  - [ ] Latency: ___ms →___ms (or N/A)
  - [ ] Memory footprint: ___MB →___MB (or N/A)
  - [ ] Benchmark results or load test attached (if applicable)
- [ ] (New features) Monitoring, alerts, and observability configured
- [ ] (Deployments) Rollback plan documented and tested
- [ ] (Deployments) Runbook or troubleshooting guide created (if applicable)

---

## Additional Context

### Architecture & Design Decisions

Document architectural rationale, technical decisions, and trade-offs. Include links to relevant design docs or decision records.

**Trade-offs & Shortcuts** (required if any):
Any shortcuts, technical debt, or deferred work must be explicitly documented. Tag with `#TODO` or document in [ARCHITECTURE.md](../docs/ARCHITECTURE.md) with a timeline for resolution.

### Performance, Security, Compliance, or Deployment Impact

Describe any significant impacts. Include screenshots, benchmark results, load test results, or links to test artifacts if relevant.

**Accessibility** (if UI changes):

- [ ] WCAG 2.1 AA compliance verified (if applicable)

---

## Reviewer Guidance (Codex Code Review Standard)

As a code reviewer, operate at the highest standard for reliability, maintainability, and business value. For this PR:

✅ **Approve only if ALL of the following are true:**

1. **Functionality**: Code works as intended; logic is sound; all edge cases and error conditions are handled
2. **Readability & Maintainability**: Variable/function names are clear; code is modular; no anti-patterns
3. **Performance**: Efficient; no unnecessary computations or bottlenecks; optimizations justified
4. **Security**: No vulnerabilities; sensitive data handled securely; inputs validated
5. **Best Practices**: Adheres to language-specific conventions; follows established patterns
6. **Testing**: Sufficient, meaningful tests; edge cases covered; CI passes
7. **Documentation**: Clear docstrings; complex logic explained; user-facing changes documented
8. **Business Value**: Change delivers clear value, furthers the roadmap, and is production-ready in a mission-critical system

❌ **Flag for discussion or rejection if:**

- Logic errors or untested paths are identified
- Test coverage is insufficient (boundary conditions, error cases not covered)
- Code style, naming, or documentation gaps exist (reference precise file paths and line numbers)
- Architectural/design choices impact scalability, resilience, maintainability, or operational cost without justification
- Trade-offs or deviations from standards are undiscussed or inadequately justified
- Secrets, hardcoded values, or sensitive data are exposed
- Downstream dependencies or breaking changes are not reviewed

💬 **Acknowledge and note** strengths, clean patterns, robust logic, and exemplary clarity. Suggest improvements for polish or maturity.

**By merging, you vouch for this code's quality and impact. Accept only PRs that you would trust to run autonomously in a high-stakes, production environment.**

---

## Approval & Merge Gates

- Code owners and domain-specific reviewers must approve before merge
- CI/CD pipeline must pass (lint, tests, security checks)
- All conversations must be resolved or explicitly acknowledged
