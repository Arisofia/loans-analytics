# Packages directory

This folder is reserved for shared libraries and utilities that may be published or reused across the project. It remains tracked so SonarCloud and other tooling can scan the repository structure consistently.

Guidelines:
- Place each shared package in its own subfolder (for example, `packages/loan-utils`).
- Include a README and appropriate licensing information within each package for traceability and auditability.
- Keep dependencies minimal and documented to support predictable CI behavior.
- Add tests alongside package code to maintain coverage quality.

If the directory is unused, leave this file in place so automated checks referencing `packages` continue to succeed.
