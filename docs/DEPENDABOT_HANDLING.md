# Dependabot Issue Handling Guide

## Overview

This guide explains how to handle common Dependabot scenarios and errors in the Abaco Loans Analytics repository.

## Common Dependabot Scenarios

### Scenario 1: "pull_request_exists_for_latest_version"

**Error Example:**
```
dependency-name: "cookie"
dependency-version: "1.1.1"
```

**Root Cause**: Dependabot tried to create a PR for an update, but a PR already exists.

**Resolution Options:**

1. **Merge or Close Existing PR (Recommended)**
   - Navigate to repository's pull requests
   - Find the existing Dependabot PR for the package
   - Either merge it if the update is safe, or close it if you don't want the update

2. **Let Dependabot Handle It**
   - This error is informational and self-resolving
   - Once the existing PR is merged/closed, Dependabot will stop reporting this error
   - No code changes needed

3. **Adjust Dependabot Configuration**
   - Edit `.github/dependabot.yml` to limit open PRs:
   ```yaml
   version: 2
   updates:
     - package-ecosystem: "npm"
       directory: "/"
       schedule:
         interval: "weekly"
       open-pull-requests-limit: 5
   ```

### Scenario 2: "update_not_possible" with Dependency Conflicts

**Error Example:**
```
VulnerabilityAuditor: audit result not viable: downgrades_dependencies
Requirements to unlock update_not_possible
The latest possible version that can be installed is 0.0.33
```

**Root Cause**: Security update would downgrade other dependencies or has conflicting constraints.

**Resolution Options:**

1. **Review and Update Package Constraints (Recommended)**
   ```bash
   # Delete lock file and regenerate
   rm package-lock.json
   npm install
   ```

2. **Manually Update the Dependency**
   ```bash
   # Update to latest
   npm update @azure/static-web-apps-cli
   
   # Or force a specific version
   npm install @azure/static-web-apps-cli@latest --save-dev
   ```

3. **Allow Downgrades in Dependabot Config**
   ```yaml
   version: 2
   updates:
     - package-ecosystem: "npm"
       directory: "/"
       schedule:
         interval: "weekly"
       allow:
         - dependency-type: "all"
   ```

4. **Ignore Specific Updates**
   ```yaml
   version: 2
   updates:
     - package-ecosystem: "npm"
       directory: "/"
       ignore:
         - dependency-name: "cookie"
           versions: ["1.1.1"]
   ```

## Current Repository Status

### NPM Dependencies

**Primary Dependency:**
- `@azure/static-web-apps-cli: ^2.0.7` (dev dependency)

**Known Vulnerabilities:**
As of the last audit, there are 4 low severity vulnerabilities in transitive dependencies:
- `cookie` package (<0.7.0) - No fix available from upstream
- `tmp` package (<=0.2.3) - No fix available from upstream

These are dependencies of `@azure/static-web-apps-cli` and cannot be fixed without an update from Azure.

### Checking for Updates

```bash
# Check current versions
npm list @azure/static-web-apps-cli

# Check for available updates
npm outdated

# Check security audit
npm audit

# Dry-run update check
npm update --dry-run
```

### Updating Dependencies

```bash
# Update specific package
npm install @azure/static-web-apps-cli@latest --save-dev

# Update all packages within semver constraints
npm update

# Force audit fix (may break things)
npm audit fix

# Force audit fix including breaking changes
npm audit fix --force
```

## Validation After Updates

After updating any dependencies, always run the validation script:

```bash
python scripts/validate_complete_stack.py
```

This ensures:
- All data files are present
- All scripts are accessible and executable
- Dashboard components are available
- Docker configuration is valid
- Documentation is complete
- Agent analysis is functional

## Best Practices

1. **Review Before Merging**: Always review Dependabot PRs before merging
2. **Test Locally**: Pull the PR branch and run validation locally
3. **Check Breaking Changes**: Review changelog for breaking changes
4. **Run Tests**: Ensure all tests pass after dependency updates
5. **Monitor CI/CD**: Watch for any CI/CD failures after merging

## Dependabot Configuration

Current configuration (`.github/dependabot.yml`):
- **GitHub Actions**: Weekly updates, max 5 PRs
- **Python (pip)**: Weekly updates, max 10 PRs
- **JavaScript (npm)**: Weekly updates, max 10 PRs
- **Docker**: Weekly updates, max 5 PRs

All updates are grouped by minor and patch versions to reduce PR volume.

## Troubleshooting

### Issue: Too Many Open PRs

**Solution**: Temporarily disable Dependabot or increase `open-pull-requests-limit`

### Issue: Conflicting Dependencies

**Solution**: 
1. Review the conflict details in the Dependabot PR
2. Manually resolve by updating package.json
3. Regenerate lock files

### Issue: Breaking Changes

**Solution**:
1. Review the package changelog
2. Update code to accommodate breaking changes
3. Test thoroughly before merging

## Additional Resources

- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [npm Audit Documentation](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [Azure Static Web Apps CLI](https://github.com/Azure/static-web-apps-cli)

## Contact

For questions about dependency management in this repository, refer to:
- Repository maintainers
- GitHub Security tab for vulnerability alerts
- Dependabot dashboard in repository settings
