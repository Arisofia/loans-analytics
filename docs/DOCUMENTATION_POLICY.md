# Documentation & Settings Policy

## Purpose

This policy governs the use, content, retention, and organization of all project-level documentation and configuration in the repository—including, but not limited to, README.md, CONTRIBUTING.md, .vscode/, .github/, .env*, .settings/, and any project or settings files across the codebase.

The intent is to ensure clarity, minimize duplication, keep documentation concise and actionable, and prevent repository bloat.

## Directory & File Scope

This policy applies to:

- All README.md, README, README.txt and variants in any subdirectory
- Project definition files: pyproject.toml, package.json, requirements.txt, setup.cfg, environment.yml, etc.
- Settings and config directories (e.g., .vscode/, .idea/, .settings/, .github/)
- Any file or directory whose purpose is documentation, configuration, or environment setup

## Policy and Best Practices

1. **Single Source of Truth**
   - Each project/module/directory must have at most one authoritative README.
   - Centralize key setup, architecture, and usage instructions in the project root README.md.
   - If submodules require their own README, keep it focused on their unique purpose (not duplicating parent content).
2. **No Duplicates or Stale Files**
   - Remove any README, settings, or config file that is a near or verbatim copy of another (unless required for tooling compatibility), outdated, or meant only for demo/test/placeholder.
   - Do not keep settings/config examples that are not referenced in documentation for onboarding or automation.
3. **Minimalism & Relevance**
   - README and settings should only contain content relevant to the current state, deployment, or onboarding of the project/module.
   - Remove obsolete launch instructions, legacy badges, old roadmap notes, or anything that is not actionable or up-to-date.
4. **Automate Linting and Validation**
   - Incorporate linting (yamllint, jsonlint, markdownlint, etc.) into CI/CD to prevent broken or syntactically incorrect documentation/config from entering main.
5. **Documented Retention Policy**
   - Periodically audit .vscode/, .idea/, .settings/, etc. Remove files that are user-specific, IDE-generated, or are not explicitly required for build/test/development automation.
   - Add editor workspace files to .gitignore and document this in the main README.md.
6. **Link, Don’t Duplicate**
   - Where possible, link to centralized docs (company handbook, system architecture, onboarding guides) instead of copying in fragments or old versions.
   - Use code comments or per-directory README “see parent directory for ...” rather than re-documenting.

## Review & Enforcement

- All documentation and settings are subject to regular review.
- Owners and contributors must remove or consolidate files not meeting the above standards.
- Repeated violation (duplicate, stale, or junk files) should be flagged in review and CI; escalate to leads for chronic offenders.

## Contact

Direct all questions or policy exceptions to the CTO or designated repo owners.

_Adhering to this policy will keep your repository lean, navigable, and professional, helping both your current team and future maintainers work efficiently and confidently._
