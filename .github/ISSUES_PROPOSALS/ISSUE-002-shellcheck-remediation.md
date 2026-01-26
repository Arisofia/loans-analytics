---
name: ShellCheck workflow style remediation
about: Remediate top ShellCheck warnings across workflows
---

**Summary**
Reduce ShellCheck noise by fixing the highest-risk warnings across repository workflows and adding a triage schedule.

**Tasks**

- [ ] Run shellcheck across all non-vendor workflows and create per-file PRs grouped by severity
- [ ] Prioritize fixes that may change behavior (unquoted vars, repeated redirects)
- [ ] Add CI gating for new shell-step fixes

**Owner**: @devops
**Labels**: ci, medium-priority
