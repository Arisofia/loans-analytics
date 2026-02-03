# CodeQL CI Failure Resolution

**Date:** 2026-02-03  
**Issue:** Security Scan / CodeQL Analysis (python) failing on PR checks  
**Status:** ✅ Resolved

---

## Problem Statement

The CodeQL Analysis workflow was consistently failing with the following error:

```
ERROR: In extension for codeql/util:restrictAlertsTo, row 1 is invalid. 
Found '"undefined", "undefined", "undefined"', which does not match 
the signature 'restrictAlertsTo(string filePath, int lineStart, int lineEnd)'.
```

**Impact:**
- PR checks blocked
- Security scanning incomplete
- Cannot merge PRs until resolved

---

## Root Cause Analysis

### What Happened

CodeQL's differential analysis feature (PR diff range extension) requires determining the merge base between the PR branch and the target branch. This is used to:

1. Calculate which files changed in the PR
2. Focus analysis on modified code regions  
3. Generate actionable alerts for new code only

### Why It Failed

The GitHub Actions checkout step by default uses a **shallow clone** (`fetch-depth: 1`), which only fetches:
- The most recent commit on the PR branch
- No historical commits
- No merge base information

Without sufficient git history, CodeQL's `restrictAlertsTo` extension couldn't:
- Find the common ancestor commit (merge base)
- Calculate the diff range
- Determine file paths and line numbers for changed code

This resulted in "undefined" values being passed to the extension, causing validation errors.

---

## Solution

### Change Made

Modified `.github/workflows/security-scan.yml`:

```yaml
steps:
  - name: Checkout repository
    uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
    with:
      # Fetch full history to enable proper merge base detection for PR diffs
      fetch-depth: 0
```

### What This Does

- `fetch-depth: 0` instructs git to fetch the **full repository history**
- Enables CodeQL to properly calculate merge base with target branch
- Allows differential analysis to work correctly for PR contexts

### Trade-offs

**Pros:**
- ✅ Fixes CodeQL differential analysis
- ✅ Enables proper PR-scoped security scanning
- ✅ Minimal performance impact (git fetch is fast, analysis is the bottleneck)

**Cons:**
- ⚠️ Slightly longer checkout time for large repositories (~5-10 seconds typically)
- ⚠️ More bandwidth usage for checkout step

**Decision:** The minimal performance cost is acceptable for ensuring security scanning works correctly.

---

## Verification

### Before Fix

```
Job: CodeQL Analysis (python)
Status: ❌ Failure after 43s
Error: A 'codeql resolve extensions-by-pack' operation failed with error code 2
```

### After Fix

```
Job: CodeQL Analysis (python)  
Status: ✅ Success
Merge bases detected: 9fc703bc735b25d8110040af34e19a36d1bd490f
Analysis completed successfully
```

---

## Alternative Solutions Considered

### 1. Disable Differential Analysis
```yaml
- name: Perform CodeQL Analysis
  with:
    # Disable PR diff analysis
    upload: true
    # Don't use extension packs
```

**Rejected:** Loses valuable PR-scoped analysis features

### 2. Fetch Only Merge Base
```yaml
with:
  fetch-depth: 50  # Fetch last 50 commits
```

**Rejected:** May not be sufficient for all PRs; still fragile

### 3. Use Full History (Selected)
```yaml
with:
  fetch-depth: 0  # Fetch all history
```

**Selected:** Most reliable, minimal performance cost

---

## Related Documentation

- [CodeQL Action Documentation](https://github.com/github/codeql-action)
- [GitHub Actions Checkout](https://github.com/actions/checkout)
- [CodeQL Differential Analysis](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/configuring-code-scanning#analyzing-code-in-pull-requests)

---

## Prevention

To prevent similar issues in the future:

1. **When using CodeQL on PRs:** Always use `fetch-depth: 0` or ensure sufficient history
2. **Test workflow changes:** Use `workflow_dispatch` to manually trigger and test
3. **Monitor job logs:** Check for "merge base" detection messages in CodeQL output
4. **Validate locally:** Test git operations with shallow clones before deploying

---

## Commit Reference

- **Fix Commit:** e8b294e
- **Branch:** copilot/verify-repository-status  
- **Files Changed:** `.github/workflows/security-scan.yml`
- **Lines Modified:** +3 (added fetch-depth configuration with comment)

---

**Resolution Confirmed:** ✅ Issue resolved, security scanning operational
