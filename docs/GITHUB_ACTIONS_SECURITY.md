# GitHub Actions Security Best Practices

## Commit Hash Pinning

This repository has been updated to use commit hashes instead of semantic versioning for GitHub Actions. This is a security best practice that prevents supply chain attacks by ensuring that workflow runs use the exact code version that was audited and approved.

### Why Commit Hash Pinning?

1. **Immutability**: Tags can be moved to different commits, but commit hashes are immutable
2. **Security**: Prevents malicious actors from pushing compromised code to an existing tag
3. **Transparency**: Makes it clear exactly what code version is being used
4. **Auditability**: Easier to track and audit what actions are running in your workflows

### Commit Hash Reference

Below is the mapping of actions to their pinned commit hashes:

#### Core GitHub Actions

| Action | Version | Commit Hash |
|--------|---------|-------------|
| `actions/checkout` | v4.2.2 | `2a3af1b1dde7a068b44c712feead7d94d4fe19fa` |
| `actions/setup-python` | v5.3.0 | `fe75d2dea0e804b9c2cf7c1fe0718524504cc6e3` |
| `actions/setup-node` | v4.1.0 | `b7dde419cc031a3d665baa4a62731727917cd13e` |
| `actions/upload-artifact` | v4.4.3 | `250e9d8087e4d33cdf6c33e180d803782f68fdb1` |
| `actions/download-artifact` | v7.0.0 | `37930b1c2abaa49bbe596cd826c3c89aef350131` |
| `actions/github-script` | v7.0.1 | `60a0d83cf42496352c7b1c5b6cf25dc6aa6f8c93` |
| `actions/cache` | v4.1.2 | `b6c6e19650157c2e813776fd7f8b2bf258a5a410` |
| `actions/setup-java` | v4.5.0 | `8df1039502a15bceb9433410b1a100fbe190c53b` |
| `actions/stale` | v4.1.0 | `2ea3b114c2c58b28bdb72b5f9bb9c6adc8ecfb81` |

#### CodeQL Actions

| Action | Version | Commit Hash |
|--------|---------|-------------|
| `github/codeql-action/init` | v4.32.0 | `b20883bbd772085d89b7f2f66d5dc41fd8fb004c` |
| `github/codeql-action/autobuild` | v4.32.0 | `b20883bbd772085d89b7f2f66d5dc41fd8fb004c` |
| `github/codeql-action/analyze` | v4.32.0 | `b20883bbd772085d89b7f2f66d5dc41fd8fb004c` |
| `github/codeql-action/upload-sarif` | v4.32.0 | `b20883bbd772085d89b7f2f66d5dc41fd8fb004c` |

#### Docker Actions

| Action | Version | Commit Hash |
|--------|---------|-------------|
| `docker/build-push-action` | v5.3.0 | `94b440b8e4a7ae1f6e627619693455b84444c56b` |
| `docker/login-action` | v3.1.0 | `46df7e3028f5d5693b552b215737bc89121b29e4` |
| `docker/metadata-action` | v5.6.1 | `369eb591f429131d6889c46b94e711f089e6ca96` |
| `docker/setup-buildx-action` | v3.8.0 | `6524bf65af31da8d45b59e8c27de4bd072b392f5` |
| `docker/scout-action` | v1.16.1 | `cc6400ac43b9bcf0c54dcb5afe65c1f0b1f2b24e` |

#### Package Manager Actions

| Action | Version | Commit Hash |
|--------|---------|-------------|
| `pnpm/action-setup` | v4.0.0 | `fe02b34f77f8bc703788d5817da081398fad5dd2` |

### Updating Actions

When updating actions to newer versions:

1. Visit the action's GitHub repository releases page
2. Find the release you want to use
3. Note the commit hash associated with that release
4. Update the workflow file with the commit hash
5. Add a comment with the version number for documentation

Example:
```yaml
- uses: actions/checkout@2a3af1b1dde7a068b44c712feead7d94d4fe19fa  # v4.2.2
```

### Dependabot Configuration

The repository includes a Dependabot configuration (`.github/dependabot.yml`) to help keep actions up to date. Dependabot can automatically create pull requests when new versions of actions are released.

### Actions Not Updated

Some third-party actions were not updated to commit hashes due to:
- Version tags not clearly defined
- Actions still in rapid development
- Actions managed directly by cloud providers (Azure, AWS, etc.)

For these actions, it's recommended to:
1. Review their security posture regularly
2. Pin to specific semantic versions where possible
3. Consider using Dependabot to track updates
4. Evaluate alternatives if security is a concern

### Best Practices

1. **Regular Reviews**: Review and update action versions quarterly
2. **Security Scanning**: Use GitHub's Dependabot security alerts
3. **Testing**: Test workflow changes in a non-production branch first
4. **Documentation**: Keep this document updated when action versions change
5. **Audit Trail**: Document the reason for each action version choice

### Resources

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Using Commit Hashes in GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)
- [Dependabot for GitHub Actions](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot)

### Maintenance

This documentation was last updated: **2026-01-29**

For questions or concerns about GitHub Actions security, please contact the DevOps team or create an issue in this repository.
