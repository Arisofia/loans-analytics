# Security Policy

## Path Management Security

All path and environment variable resolution logic is covered by automated tests
in `tests/test_paths.py`. Any changes to path logic must pass this suite to
ensure data is never written to or read from insecure or unintended locations.

## Documentation & Settings Policy

All documentation, README, and settings/configuration files are governed by the
repository policy (see main README.md). Duplicates, stale, or user-specific
files are not permitted. All changes are subject to review and periodic audit.
See .gitignore for enforced exclusions.

## Secret Scanning & API Key Protection (Gitleaks)

**Status**: ✅ ENABLED  
**Configuration**: `.gitleaks.toml`  
**CI/CD Integration**: `.github/workflows/security-scan.yml` (secret-scanning job)  
**Update**: 2026-03-19 (R-12 Remediation)

### Detection Scope

Gitleaks scans all commits in push and pull request events to detect and prevent:

- AWS Access Keys (AKIA*)
- API Keys and Bearer Tokens
- Database passwords and connection strings
- Private SSH/RSA/PGP keys
- Supabase service role keys
- JWT authentication tokens
- GCP Service Account credentials

### Configuration & Allowlist

**File**: `.gitleaks.toml`  

The configuration uses default Gitleaks detection rules plus custom rules for project-specific keys:
- AWS credentials and service accounts
- Supabase API keys and tokens
- PostgreSQL connection strings with embedded passwords
- Private key file markers (-----BEGIN PRIVATE KEY-----)

**Explicitly Allowed Paths** (false positives):
- Documentation files (`docs/`, `README.md`)
- Test fixtures and sample data (`tests/fixtures/`, `*.example`)
- Generated files (`node_modules/`, `build/`, `dist/`)
- Lock files and compiled outputs
- CI/CD configuration (reviewed in GitHub)
- Infrastructure as Code (reviewed separately)

**Safe to Commit**:
- Example credentials in documentation (e.g., "admin:admin", "PLACEHOLDER_KEY")
- Test fixtures with placeholder values
- Configuration templates (`.env.example`, `.sample`)

### Failure Criteria

The scan **FAILS** if real secrets are detected:
- Actual AWS/API key patterns (not examples)
- Private key file content
- Database passwords (not connection strings with placeholders)
- Supabase service tokens with valid entropy
- Any unrecognized high-entropy patterns matching secret formats

### If Secrets Are Committed

If a secret is accidentally committed:

1. **Immediately revoke** the compromised key/token in the source system
2. **Create an issue** documenting the incident (mark as security incident)
3. **Rewrite git history** to remove the secret from all commits:
   ```bash
   # Using git-filter-repo (recommended)
   git filter-repo --invert-paths --path path/to/file
   # Force push (requires review approval)
   git push --force-with-lease origin main
   ```
4. **Update SECURITY.md** with incident details and mitigation steps
5. **Notify maintainers** and conduct post-incident review

### Gitleaks CI/CD Job Details

**When Run**:
- On every push to `main` or `develop`
- On every pull request to `main`
- Manual workflow dispatch

**Behavior**:
- Scans full git history (fetch-depth: 0)
- Uses `.gitleaks.toml` configuration
- Fails the workflow if secrets detected
- Uploads artifacts (JSON + SARIF reports)
- Logs are retained for 30 days

**Bypassing Gitleaks** (NOT RECOMMENDED):
- False positives can be allowlisted in `.gitleaks.toml`
- Requires code review before merging
- Should be rare and thoroughly documented
- Commit SHAs can be explicitly allowed (last resort)

## SonarQube Configuration Security

All SonarQube configuration and metadata is governed by the policy in
`.sonarqube/conf/README.md`. No secrets, credentials, or raw data may be stored
in `.sonarqube/conf/`. Any accidental commit of sensitive data must be reverted
and treated as a security incident. See the README for retention, audit, and
restoration procedures.

### Known Dependency Vulnerabilities

#### Pygments ReDoS (GHSA-5239-wwwm-4pmq / CVE-2026-4539)

- **Package**: `pygments`
- **Affected**: `<=2.19.2`
- **Patched version**: _None published upstream_
- **Severity**: Low (local attack vector)

Current status:
- The advisory has no patched release yet, so an upgrade-based remediation is not available.
- We track this advisory and will upgrade immediately once upstream publishes a fixed version.

Temporary mitigation:
- Dependabot pip updates are configured to ignore this advisory range until a real patch exists.
- Production exposure is limited because the attack requires local access and low privileges.
- Existing least-privilege and environment isolation controls remain required.

#### DoS/ReDoS in body-parser and path-to-regexp

The following advisories are present in the dependency tree (see
package-lock.json and pnpm-lock.yaml):

- **body-parser**: Denial of Service vulnerability (transitive dependency)
- **path-to-regexp**: ReDoS (Regular Expression Denial of Service) risk
  (transitive via router)
  These are not directly depended on by this project and are included via upstream
  dependencies. No direct upgrade path is available at this time. Monitor upstream
  for patches.
  If/when upstream releases a fix, update dependencies and lockfiles accordingly.

## Security and Audit Log

### Known Vulnerabilities

All known vulnerabilities in indirect dependencies (including `cookie` and `tmp`) have been resolved as of 2026-01-05.

### Mitigation Plan

- Monitor for updates and apply patches when available.
- Document and review usage of affected packages.
- Ensure audit logs and traceability for all pipeline steps.
