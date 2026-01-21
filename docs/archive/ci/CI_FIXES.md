# CI Fixes & Remediation Plan

## High-priority fixes

1. Playwright workflow ( .github/workflows/playwright.yml )
   - Root cause: malformed workflow content in failing PRs (top-level quoting issue)
   - Fix action: unquote the top-level keys and add validation test
   - Status: ✅ FIXED in d4b24a76
   - Owner: @engineering-lead
   - ETA: Week 1

2. ShellCheck remediation plan
   - Triage category: SC2086 (unquoted var), SC2129 (repeated redirects), SC2028 (echo with escapes)
   - Plan: batch fixes by workflow owner in 3 PRs (high-risk, medium, low) to avoid noisy diffs
   - Owner: assigned workflow file owner

3. Exclude vendor workflows from validator
   - Already implemented in `scripts/fix-workflows.sh`; confirm on CI

4. Add a workflow CI check to validate workflows on PR (actionlint + shellcheck)
   - Add `ci:validate-workflows` job triggered on `pull_request` to block merges

## Medium-priority

- Bump in-repo actions (e.g., `actions/github-script`, `codecov`) where safe
- Add explicit `workflow_call` outputs where needed

## Observability & Alerts

- Add an alerting mechanism for scheduled runs that fail with `jobs: []` (no jobs). Possible first response: send notification to `#infra` channel.

## Acceptance criteria

- Validator job runs on PRs and fails on broken workflows
- Previously non-retryable runs are re-runnable after Playwright fix
- CI passes on the draft branch and main for critical jobs

---

> For each fix I will create an issue in `.github/ISSUES_PROPOSALS/` and include a minimal patch in the draft branch for review.
