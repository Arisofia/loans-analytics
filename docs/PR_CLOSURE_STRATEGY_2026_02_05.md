# PR Closure Strategy - February 5, 2026

## Current Baseline (AUTHORITATIVE)

**Commit**: `e5ea015ce` (latest on main)  
**Status**: ✅ Production-ready with RLS governance  
**Includes**:

- ✅ RLS diagnostic tools (`diagnose-rls.sh`, `load-env.sh`)
- ✅ RLS smoke test suite (`scripts/test-rls.js`)
- ✅ Shellcheck linting fixes (SC2250)
- ✅ Environment variable validation
- ✅ Supabase governance and deployment verification

---

## Stale Branches to Close

### ❌ `copilot/sub-pr-234`

**Status**: CLOSE AS STALE  
**Reason**:

- Based on older commits (before RLS diagnostic tools were added)
- Would DELETE critical scripts: `diagnose-rls.sh`, `load-env.sh`
- Does not include: RLS smoke tests, Supabase governance improvements
- Regressive relative to current baseline

**Action**:

```bash
# Close via GitHub UI or CLI:
gh pr close <PR_NUMBER> --comment "Closing as stale - based on older commits that would remove critical RLS diagnostic tools. Current main includes production-ready RLS governance and should be used as baseline."
```

### ❌ `copilot/sub-pr-234-again`

**Status**: CLOSE AS STALE  
**Reason**: Same as above

- Removes diagnostic scripts
- Doesn't include current governance improvements
- Could introduce conflicts with deployed RLS policies

**Action**:

```bash
# Close via GitHub UI or CLI:
gh pr close <PR_NUMBER> --comment "Closing as stale - would remove critical RLS diagnostic tools. Use main as baseline instead."
```

---

## Dependabot PRs: Conditional Merge Strategy

### ✅ Auto-Merge Criteria

A Dependabot PR can be auto-merged ONLY if:

1. ✅ All CI checks pass (tests, security scans, linters)
2. ✅ No conflicts with main
3. ✅ No breaking changes for:
   - Streamlit dashboard (`streamlit_app.py`)
   - Supabase integrations (`python/supabase_pool.py`)
   - Pipeline runners (`src/pipeline/`)
   - Multi-agent system (`python/multi_agent/`)

### ⚠️ Manual Review Required

If ANY Dependabot PR:

- ❌ Fails CI checks
- ❌ Has merge conflicts
- ❌ Updates critical dependencies (Supabase client, Pydantic, OpenAI SDK)
- ❌ Updates Python version requirements

**Leave open for manual review** before merging.

---

## Current Dependabot PRs (10 total)

| Branch                                                                     | Action   | Status |
| -------------------------------------------------------------------------- | -------- | ------ |
| `dependabot/github_actions/actions/download-artifact-7`                    | CHECK CI | ⏳     |
| `dependabot/github_actions/actions/upload-artifact-6.0.0`                  | CHECK CI | ⏳     |
| `dependabot/github_actions/minor-and-patch-6c127ef132`                     | CHECK CI | ⏳     |
| `dependabot/github_actions/peter-evans/create-pull-request-8`              | CHECK CI | ⏳     |
| `dependabot/github_actions/snyk/actions-9adf32b1121593767fc3c057af55b55d*` | CHECK CI | ⏳     |
| `dependabot/pip/azure-monitor-opentelemetry-exporter-1.0.0b47`             | MANUAL   | ⚠️     |
| `dependabot/pip/cachetools-7.0.0`                                          | CHECK CI | ⏳     |
| `dependabot/pip/marshmallow-4.2.2`                                         | CHECK CI | ⏳     |
| `dependabot/pip/minor-and-patch-6b1256c9a7`                                | CHECK CI | ⏳     |
| `dependabot/pip/wrapt-2.1.1`                                               | CHECK CI | ⏳     |

---

## Baseline Definition (Going Forward)

**All work must be based on**:

- **Main branch commit**: `e5ea015ce` or later
- **Includes**: RLS diagnostic tools, smoke tests, Supabase governance
- **Does NOT include**: Removed/deleted RLS scripts

**Any branch that**:

- ✅ Has RLS diagnostic scripts = Current baseline ✓
- ❌ Is missing RLS diagnostic scripts = Stale and should not be merged

---

## Approval Workflow

```
┌─────────────────────────────────────────┐
│ New PR / Branch Created                 │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────▼──────────┐
         │ Based on current   │
         │ main (e5ea015ce+)? │
         └────┬──────────┬────┘
         YES  │          │  NO
             │          └──────► ❌ STALE
             │                  (Close)
    ┌────────▼──────────┐
    │ All CI checks     │
    │ passing?          │
    └────┬──────────┬───┘
   YES   │          │  NO
        │          └──────► ⏳ PENDING
        │                   (Manual review)
    ┌───▼────────────┐
    │ No breaking    │
    │ changes?       │
    └────┬───────┬──┘
   YES   │       │  NO
        │       └──────► ⚠️ REQUIRES
        │               ASSESSMENT
    ┌───▼────────────┐
    │ ✅ APPROVED    │
    │ (Auto-merge)   │
    └────────────────┘
```

---

## Summary for Team

✅ **Current main is production-ready** and includes all RLS governance improvements  
❌ **Do NOT merge stale Copilot PRs** - they would remove critical tools  
⏳ **Dependabot PRs** - merge only if CI passes and no breaking changes  
📍 **Baseline for all future work** = Current main + RLS diagnostic tools

---

**Last Updated**: 2026-02-05  
**Status**: Ready for implementation  
**Next Step**: Close stale PRs, evaluate Dependabot PRs
