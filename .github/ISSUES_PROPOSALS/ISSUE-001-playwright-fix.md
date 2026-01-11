---
name: Playwright workflow fix
about: Fix failing Playwright workflow that produced runs with no jobs
---

**Summary**
The Playwright workflow used in a failing PR contains a malformed top-level key which caused GitHub to spawn runs with `jobs: []` and no logs. This issue will replace the malformed key and add a workflow validation job.

**Tasks**

- [ ] Replace the quoted top-level key with a valid key
- [ ] Add `workflow_call`/validation job to run on `pull_request`
- [ ] Re-run previously non-retryable runs and confirm jobs are created

**Acceptance**

- PR with fixes merged and previously non-retryable runs now show jobs and produce logs.

**Owner**: @engineering-lead
**Labels**: ci, high-priority
