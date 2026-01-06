# Q1 2026 Implementation Plan — Abaco Loans Analytics

## Executive summary

This plan surfaces the Figma analytics file in the repo, documents KPIs and calculation sources, fixes dashboard bindings, stabilizes CI, and prepares OKRs and a GitHub project board for Q1 2026 execution.

## Objectives (Q1 2026)

- Make analytics KPIs and related Figma visual artifacts discoverable and consumable by engineering and product teams.
- Stabilize CI (fix blocking workflows, reduce ShellCheck noise, add regression checks for Playwright and KPI pipelines).
- Deliver a verified dashboard with correct KPI bindings and E2E tests.
- Create a transparent set of OKRs and a working project board to track progress.

## Scope

- Add documentation and sample exports for Figma analytics file
- Add PLAN.md, OKRs, CI remediation checklist, and issue templates
- Fix Playwright workflow and remaining CI blocking issues
- Provide sample fixes for dashboard bindings and tests
- Create project board and populate initial issues

## Milestones & Timeline

- Week 1 (Sprint 1): Draft and commit PLAN.md, OKRs.md, figma/README.md, CI checklist; open draft PR.
- Week 2 (Sprint 1): Apply Playwright workflow fix to PR branch; re-run previously non-retryable runs and resolve immediate failures.
- Week 3 (Sprint 2): Remediate highest-severity ShellCheck warnings and bump in-repo actions; add CI regression checks.
- Week 4 (Sprint 2): Fix dashboard bindings, add unit/E2E checks, and run Playwright tests; collect and triage failures.
- Week 5-8 (Sprint 3): Complete OKR workstreams, finalize project board, and prepare release notes.

## Owners & Roles

- Engineering: implement CI fixes, dashboard binding fixes, unit & E2E tests (owner: @engineering-lead)
- Analytics: verify KPI formulas, maintain KPI definitions, provide baselines (owner: @analytics-lead)
- Design: provide Figma file and export guidelines (owner: @design-lead)
- DevOps: validate workflow changes and monitor scheduled runs (owner: @devops)
- Product: define acceptance criteria and review OKRs (owner: @product)

## Acceptance criteria

- Playwright workflows run successfully on PR branch and main after fix
- KPI unit tests and baseline regressions pass in CI
- Figma file exported and embedded README created
- OKRs approved and project board created

## Risks & Mitigations

- Risk: Some workflows require secrets only available in repo admin; Mitigation: create gated PRs and ask admins to run reattempts.
- Risk: Large ShellCheck remediation may be noisy; Mitigation: prioritize high-severity (blocking) issues first and schedule style passes.

---

> Next steps: push a draft branch with these files and open a PR for review; I can do that now if you want me to push the draft branch and open a draft PR for your preview.
