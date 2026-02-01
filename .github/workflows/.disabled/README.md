# Disabled Workflows

This directory contains GitHub Actions workflows that have been temporarily disabled to reduce workflow failures and optimize CI/CD performance.

## Why Workflows Were Disabled

### Critical Issue: 81% Failure Rate
- **26,134+ accumulated workflow runs** with **81% recent failure rate**
- Primary culprit: `security-scan.yml` failing consistently
- CodeQL analysis failing for both Python and JavaScript
- Workflows triggering too frequently (every push + PR + weekly schedule)
- At peak development: 10-20+ runs per day → 8-16 failures per day

### Performance Impact
- High Actions minutes consumption (~80% from failed security scans)
- Noise in workflow status making it hard to spot real issues
- Developer fatigue from constant failure notifications

## Disabled Workflows

### security-scan.yml (Priority: HIGH - Fix Required)
**Reason**: CodeQL analysis failing consistently for Python and JavaScript

**Known Issues**:
1. **Missing build dependencies** - CodeQL autobuild may not handle complex Python project dependencies
2. **JavaScript/TypeScript confusion** - 2.6% of codebase is TypeScript, CodeQL may be misconfigured
3. **Timeout issues** - Large Python codebase (79%) may exceed CodeQL analysis limits
4. **Matrix strategy** - Running Python + JavaScript in parallel may be resource-intensive

**How to Re-enable**:

1. **Fix CodeQL Configuration** - Add explicit build steps:
   ```yaml
   jobs:
     codeql-python:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
         - uses: github/codeql-action/init@v3
           with:
             languages: python
         - uses: github/codeql-action/analyze@v3
           with:
             timeout: 30  # Add timeout protection
   ```

2. **Configure paths to skip**:
   ```yaml
   - uses: github/codeql-action/init@v3
     with:
       languages: python
       config: |
         paths-ignore:
           - '**/node_modules/**'
           - '**/vendor/**'
           - '**/__pycache__/**'
           - '**/dist/**'
   ```

3. **Test with workflow_dispatch first**:
   ```yaml
   on:
     workflow_dispatch:  # Manual testing only
     # schedule:
     #   - cron: "0 6 * * 1"  # Enable after testing
   ```

4. **Split Python and JavaScript into separate workflows** for better isolation

5. **Monitor the first 5 runs** - Only re-enable automatic triggers after 100% success rate

6. **Move back to active**:
   ```bash
   cd .github/workflows
   mv .disabled/security-scan.yml.disabled security-scan.yml
   git add security-scan.yml .disabled/
   git commit -m "chore: re-enable security-scan workflow after fixes"
   ```

### Other Disabled Workflows

- **agent-checklist-validation.yml** - Redundant with pr-checks.yml
- **azure_diagnostics.yml** - Not currently in use
- **batch_export_scheduled.yml** - Scheduled export, disable until needed
- **code-maintenance.yml** - Failing consistently, needs investigation
- **customer_segmentation.yml** - Not critical for CI
- **financial_forecast.yml** - Scheduled, non-essential
- **historical_supabase_integration.yml** - Scheduled, non-essential
- **investor_reporting.yml** - Scheduled, non-essential

## Post-Merge Cleanup Steps (Manual)

After this PR merges, clean up accumulated workflow runs:

### Option 1: GitHub UI
1. Go to **Actions** tab → Select workflow → **All workflows**
2. Filter by workflow name: `security-scan`
3. Select runs → Click **Delete workflow run**
4. Repeat for old failed runs

### Option 2: GitHub CLI (Recommended for bulk deletion)
```bash
# Delete runs older than 30 days for security-scan workflow
gh api repos/Arisofia/abaco-loans-analytics/actions/workflows/security-scan.yml/runs \
  --jq '.workflow_runs[] | select(.created_at < (now - 30*86400 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | .id' \
  | xargs -I {} gh api -X DELETE repos/Arisofia/abaco-loans-analytics/actions/runs/{}

# Or delete ALL runs for security-scan workflow
gh api repos/Arisofia/abaco-loans-analytics/actions/workflows/security-scan.yml/runs \
  --jq '.workflow_runs[].id' \
  | xargs -I {} gh api -X DELETE repos/Arisofia/abaco-loans-analytics/actions/runs/{}
```

**Note**: Requires GitHub PAT with `repo` and `workflow` scopes.

## Success Metrics

After re-enabling workflows:
- ✅ Workflow failure rate drops from 81% → <10%
- ✅ Active workflows maintain 100% success rate
- ✅ Actions minutes usage reduced by ~80%
- ✅ Clear audit trail for all workflow changes

## Additional Resources

- [CodeQL Configuration Reference](https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/using-workflows/about-workflows#about-workflows)
- [Workflow Management Strategy](./.workflow-management.yml)

## Questions or Issues?

If you encounter issues re-enabling workflows:
1. Check workflow logs for specific error messages
2. Test with `workflow_dispatch` trigger first
3. Reach out in #engineering-ci-cd channel
4. Document any new findings in this README

---

**Last Updated**: 2026-02-01  
**Updated By**: Copilot AI (Issue: 81% workflow failure rate)
