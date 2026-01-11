# .sonarqube/conf/ Directory Data Policy

## Purpose

The `.sonarqube/conf/` directory contains configuration files and metadata supporting SonarQube code quality and security scanning in the `abaco-loans-analytics` repository. These files automate static analysis, define configuration baselines, and enable reproducibility of security and quality assessments.

## Contents

This directory may hold:

- SonarQube project configuration files (e.g., `sonar-project.properties`)
- Quality profile mappings
- Access tokens (as references to secrets, never the tokens themselves)
- Rule sets, inclusion/exclusion patterns
- Generated metadata for SonarCloud/SonarQube CI pipelines

No persistent application data or test data should reside here.

## Governance & Change Control

- Configuration files in this directory are source of truth for CI code analysis jobs.
- All changes must go through standard Pull Request (PR) workflow, with mandatory reviewer approval from code owners.
- No sensitive credentials, API keys, or secrets must ever be stored directly. Always use GitHub Secrets or environment variables.
- SonarQube-related settings that affect thresholds or rule sets must be justified in PR descriptions and linked to relevant issue or risk register items.

## Retention & Cleanup Policy

- **Version Controlled**: All files here are source-controlled and versioned with the repository history.
- **No binaries or large files**: Only plain-text configuration, YAML/JSON, or SonarQube property files permitted.
- **No audit/data exports**: Do NOT place analysis result exports or coverage reports here. Such artifacts should be stored only in build pipelines or ephemeral directories (e.g., the `reports/` or a `build/output` folder).

## Compliance & Security

- This directory must never contain raw application data, client data, test secrets, or production credentials.
- Routine audits are performed to confirm compliance with INFSEC requirements.
- Any accidental commit of credentials or sensitive data must be immediately reverted and treated as a security incident (see `SECURITY.md`).

## Restoration & Disaster Recovery

- In case of accidental deletion or misconfiguration, restore appropriate configuration from version history (`git log`, `git checkout`, or PR revert).
- When updating SonarQube config for rule or threshold changes, coordinate with relevant Quality, Product, or Security teams to ensure changes are communicated and documented.

## FAQ

- **Q: Can I store my custom analysis scripts or local exclusions here?**
  - A: No. Store only team-approved configuration. Temporary or local overrides should be ignored via `.gitignore`.
- **Q: Where should SonarQube scan logs or reports go?**
  - A: Use the repository’s `/reports` or your build output folder; don’t check them into source control.

## Contact & Ownership

- **Directory Owners**: [@Arisofia](https://github.com/Arisofia), [@data-engineering](https://github.com/data-engineering)
- For questions, incidents, or exceptions, open an issue with the `qa` or `security` labels.

---

Last reviewed: 2026-01-02

# .sonarqube/conf/ Directory Data Policy

## Purpose

The `.sonarqube/conf/` directory contains configuration files and metadata supporting SonarQube code quality and security scanning in the `abaco-loans-analytics` repository. These files automate static analysis, define configuration baselines, and enable reproducibility of security and quality assessments.

## Contents

This directory may hold:

- SonarQube project configuration files (e.g., `sonar-project.properties`)
- Quality profile mappings
- Access tokens (as references to secrets, never the tokens themselves)
- Rule sets, inclusion/exclusion patterns
- Generated metadata for SonarCloud/SonarQube CI pipelines

No persistent application data or test data should reside here.

## Governance & Change Control

- Configuration files in this directory are source of truth for CI code analysis jobs.
- All changes must go through standard Pull Request (PR) workflow, with mandatory reviewer approval from code owners.
- No sensitive credentials, API keys, or secrets must ever be stored directly. Always use GitHub Secrets or environment variables.
- SonarQube-related settings that affect thresholds or rule sets must be justified in PR descriptions and linked to relevant issue or risk register items.

## Retention & Cleanup Policy

- **Version Controlled**: All files here are source-controlled and versioned with the repository history.
- **No binaries or large files**: Only plain-text configuration, YAML/JSON, or SonarQube property files permitted.
- **No audit/data exports**: Do NOT place analysis result exports or coverage reports here. Such artifacts should be stored only in build pipelines or ephemeral directories (e.g., the `reports/` or a `build/output` folder).

## Compliance & Security

- This directory must never contain raw application data, client data, test secrets, or production credentials.
- Routine audits are performed to confirm compliance with INFSEC requirements.
- Any accidental commit of credentials or sensitive data must be immediately reverted and treated as a security incident (see `SECURITY.md`).

## Restoration & Disaster Recovery

- In case of accidental deletion or misconfiguration, restore appropriate configuration from version history (`git log`, `git checkout`, or PR revert).
- When updating SonarQube config for rule or threshold changes, coordinate with relevant Quality, Product, or Security teams to ensure changes are communicated and documented.

## FAQ

- **Q: Can I store my custom analysis scripts or local exclusions here?**
  - A: No. Store only team-approved configuration. Temporary or local overrides should be ignored via `.gitignore`.
- **Q: Where should SonarQube scan logs or reports go?**
  - A: Use the repository’s `/reports` or your build output folder; don’t check them into source control.

## Contact & Ownership

- **Directory Owners**: [@Arisofia](https://github.com/Arisofia), [@data-engineering](https://github.com/data-engineering)
- For questions, incidents, or exceptions, open an issue with the `qa` or `security` labels.

---
*Last reviewed: 2026-01-02*
